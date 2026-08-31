import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import express from 'express';
import { ensureDatabase, loadLatestActions, loadSourceRows, saveAction, waitForDatabase } from './db.mjs';
import { applyScope, buildScoringModel } from './scoring.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const port = Number(process.env.PORT ?? 3001);
const app = express();
app.use(express.json({ limit: '200kb' }));

let sourceRows = [];
let model;

function parseScope(request) {
  const role = ['seller', 'manager', 'revops'].includes(request.query.role) ? request.query.role : 'seller';
  const profile = String(request.query.profile ?? 'Darcel Schlecht');
  return { role, profile };
}

function latestActionState(action) {
  if (!action) return null;
  return { id: action.id, status: action.status, note: action.note, next_step: action.next_step, due_date: action.due_date, created_at: action.created_at };
}

function isAvailableToday(action) {
  if (!action) return true;
  if (action.status === 'completed') return false;
  if (action.status === 'snoozed' && action.due_date) return new Date(action.due_date) <= new Date();
  return true;
}

async function scopedOpen(request) {
  const { role, profile } = parseScope(request);
  const actions = await loadLatestActions();
  return applyScope(model.open, role, profile).map((row) => ({ ...row, latest_action: latestActionState(actions.get(row.opportunity_id)) }));
}

function summarizeCommercial(rows, dimension) {
  const grouped = new Map();
  rows.forEach((row) => {
    const label = row[dimension] ?? 'Não informado';
    const current = grouped.get(label) ?? { label, open: 0, won: 0, lost: 0, closed: 0, openPotential: 0, lostPotential: 0, wonRevenue: 0 };
    const price = Number(row.sales_price ?? 0);
    if (row.deal_stage === 'Prospecting' || row.deal_stage === 'Engaging') {
      current.open += 1;
      current.openPotential += price;
    }
    if (row.deal_stage === 'Won') {
      current.won += 1;
      current.closed += 1;
      current.wonRevenue += Number(row.close_value ?? 0);
    }
    if (row.deal_stage === 'Lost') {
      current.lost += 1;
      current.closed += 1;
      current.lostPotential += price;
    }
    grouped.set(label, current);
  });
  return [...grouped.values()].map((row) => ({
    ...row,
    winRate: row.closed ? Number(((row.won / row.closed) * 100).toFixed(1)) : 0,
  })).sort((a, b) => b.lost - a.lost || b.openPotential - a.openPotential);
}

function sumBy(rows, dimension, selector) {
  return rows.reduce((result, row) => {
    const label = row[dimension] ?? 'Não informado';
    result.set(label, (result.get(label) ?? 0) + Number(selector(row) ?? 0));
    return result;
  }, new Map());
}

app.get('/api/health', (_request, response) => response.json({ status: model ? 'ok' : 'starting', offline: true, referenceDate: '2017-12-31' }));

app.get('/api/bootstrap', (_request, response) => {
  const sellers = [...new Set(sourceRows.map((row) => row.sales_agent))].sort();
  const managers = [...new Set(sourceRows.map((row) => row.manager))].sort();
  const regions = [...new Set(sourceRows.map((row) => row.regional_office))].sort();
  const products = [...new Set(sourceRows.map((row) => row.product))].sort();
  response.json({ profiles: { sellers, managers, revops: ['Revenue Operations'] }, filters: { regions, products, actions: ['Avançar agora', 'Definir próximo passo', 'Reengajar hoje', 'Requalificar ou encerrar', 'Completar dados'], scoreBands: ['Alto', 'Médio', 'Baixo'] }, referenceDate: '2017-12-31', scoreVersion: 'v0.3', baseline: model.baseline });
});

app.get('/api/dashboard', async (request, response, next) => {
  try {
    const rows = await scopedOpen(request);
    const available = rows.filter((row) => isAvailableToday(row.latest_action));
    const top = available.slice(0, 5);
    const counts = rows.reduce((result, row) => ({ ...result, [row.action_key]: (result[row.action_key] ?? 0) + 1 }), {});
    const scoreCounts = rows.reduce((result, row) => ({ ...result, [row.focus_band]: (result[row.focus_band] ?? 0) + 1 }), {});
    response.json({
      total: rows.length, top, counts, scoreCounts,
      revenueInFocus: top.reduce((sum, row) => sum + Number(row.sales_price ?? 0), 0),
      totalExpectedRevenue: rows.reduce((sum, row) => sum + Number(row.sales_price ?? 0), 0),
    });
  } catch (error) { next(error); }
});

app.get('/api/pipeline', async (request, response, next) => {
  try {
    let rows = await scopedOpen(request);
    const search = String(request.query.search ?? '').trim().toLowerCase();
    if (search) rows = rows.filter((row) => [row.opportunity_id, row.account, row.product, row.sales_agent].some((value) => String(value ?? '').toLowerCase().includes(search)));
    if (request.query.action) rows = rows.filter((row) => row.action_key === request.query.action);
    if (request.query.scoreBand) rows = rows.filter((row) => row.focus_band === request.query.scoreBand);
    if (request.query.stage) rows = rows.filter((row) => row.deal_stage === request.query.stage);
    if (request.query.product) rows = rows.filter((row) => row.product === request.query.product);
    if (request.query.region) rows = rows.filter((row) => row.regional_office === request.query.region);
    const page = Math.max(1, Number(request.query.page ?? 1));
    const pageSize = Math.min(100, Math.max(10, Number(request.query.pageSize ?? 25)));
    response.json({ total: rows.length, page, pageSize, rows: rows.slice((page - 1) * pageSize, page * pageSize) });
  } catch (error) { next(error); }
});

app.get('/api/deals/:id', async (request, response, next) => {
  try {
    const deal = model.byId.get(request.params.id);
    if (!deal) return response.status(404).json({ error: 'Oportunidade não encontrada.' });
    const actions = await loadLatestActions();
    return response.json({ ...deal, latest_action: latestActionState(actions.get(deal.opportunity_id)) });
  } catch (error) { return next(error); }
});

app.post('/api/actions', async (request, response, next) => {
  try {
    const { opportunityId, actorProfile, status, note = null, nextStep = null, dueDate = null } = request.body ?? {};
    if (!model.byId.has(opportunityId)) return response.status(400).json({ error: 'Oportunidade inválida.' });
    if (!actorProfile || !['pending', 'completed', 'snoozed'].includes(status)) return response.status(400).json({ error: 'Ação inválida.' });
    const action = await saveAction({ opportunityId, actorProfile, status, note, nextStep, dueDate });
    return response.status(201).json(action);
  } catch (error) { return next(error); }
});

app.get('/api/team', async (request, response, next) => {
  try {
    const rows = await scopedOpen(request);
    const { role, profile } = parseScope(request);
    const scopedSourceRows = applyScope(sourceRows, role, profile);
    const expectedByProduct = sumBy(rows, 'product', (row) => row.expected_revenue);
    const expectedByRegion = sumBy(rows, 'regional_office', (row) => row.expected_revenue);
    const lostPotentialBySeller = sumBy(scopedSourceRows.filter((row) => row.deal_stage === 'Lost'), 'sales_agent', (row) => row.sales_price);
    const grouped = new Map();
    rows.forEach((row) => {
      const current = grouped.get(row.sales_agent) ?? { sales_agent: row.sales_agent, manager: row.manager, regional_office: row.regional_office, open: 0, scoreTotal: 0, expectedRevenue: 0, potentialValue: 0, advance: 0, reengage: 0, pending: 0, highFocus: 0 };
      current.open += 1; current.scoreTotal += row.priority_score; current.expectedRevenue += row.expected_revenue; current.potentialValue += Number(row.sales_price ?? 0);
      if (row.action_key === 'Avançar agora' || row.action_key === 'Definir próximo passo') current.advance += 1;
      if (row.action_key === 'Reengajar hoje') current.reengage += 1;
      if (row.action_key === 'Completar dados' || row.action_key === 'Requalificar ou encerrar') current.pending += 1;
      if (row.focus_band === 'Alto') current.highFocus += 1;
      grouped.set(row.sales_agent, current);
    });
    const sellers = [...grouped.values()].map((row) => ({ ...row, lostPotential: lostPotentialBySeller.get(row.sales_agent) ?? 0, averageScore: Number((row.scoreTotal / row.open).toFixed(1)) })).sort((a, b) => b.expectedRevenue - a.expectedRevenue);
    const lostRows = scopedSourceRows.filter((row) => row.deal_stage === 'Lost');
    const products = summarizeCommercial(scopedSourceRows, 'product').map((row) => ({ ...row, expectedRevenue: expectedByProduct.get(row.label) ?? 0 }));
    const regions = summarizeCommercial(scopedSourceRows, 'regional_office').map((row) => ({ ...row, expectedRevenue: expectedByRegion.get(row.label) ?? 0 }));
    response.json({
      sellers,
      products,
      regions,
      losses: {
        count: lostRows.length,
        potentialValue: lostRows.reduce((sum, row) => sum + Number(row.sales_price ?? 0), 0),
      },
    });
  } catch (error) { next(error); }
});

app.get('/api/recovery', (request, response) => {
  const { role, profile } = parseScope(request);
  response.json(applyScope(model.recovery, role, profile));
});

app.use((error, _request, response, _next) => {
  console.error(error);
  response.status(500).json({ error: 'Não foi possível concluir a operação.' });
});

const dist = join(root, 'dist');
if (existsSync(dist)) {
  app.use(express.static(dist));
  app.use((_request, response) => response.sendFile(join(dist, 'index.html')));
}

await waitForDatabase();
await ensureDatabase();
sourceRows = await loadSourceRows();
model = buildScoringModel(sourceRows);

app.listen(port, '0.0.0.0', () => console.log(`Lead Scorer disponível na porta ${port}`));
