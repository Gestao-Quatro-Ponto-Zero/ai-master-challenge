import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { mkdir } from 'node:fs/promises';
import { PGlite } from '@electric-sql/pglite';
import { parse } from 'csv-parse/sync';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const dataDirectory = process.env.PGLITE_DATA_DIR ?? join(root, 'local-data', 'postgres');
await mkdir(dataDirectory, { recursive: true });

export const database = new PGlite(dataDirectory);

export async function waitForDatabase() {
  await database.query('SELECT 1');
}

function nullable(value) {
  return value === undefined || value === null || String(value).trim() === '' ? null : String(value).trim();
}

function numberOrNull(value) {
  const clean = nullable(value);
  return clean === null ? null : Number(clean);
}

async function readCsv(name) {
  const raw = await readFile(join(root, 'data', name), 'utf8');
  return parse(raw, { columns: true, skip_empty_lines: true, trim: true });
}

async function insertRows(client, table, columns, rows, conflictColumn) {
  const batchSize = 400;
  for (let start = 0; start < rows.length; start += batchSize) {
    const batch = rows.slice(start, start + batchSize);
    const values = [];
    const placeholders = batch.map((row, rowIndex) => {
      const offset = rowIndex * columns.length;
      columns.forEach((column) => values.push(row[column]));
      return `(${columns.map((_, columnIndex) => `$${offset + columnIndex + 1}`).join(',')})`;
    });
    await client.query(
      `INSERT INTO ${table} (${columns.join(',')}) VALUES ${placeholders.join(',')} ON CONFLICT (${conflictColumn}) DO NOTHING`,
      values,
    );
  }
}

export async function ensureDatabase() {
  const schema = await readFile(join(here, 'schema.sql'), 'utf8');
  await database.exec(schema);
  const { rows: [{ count }] } = await database.query('SELECT COUNT(*)::int AS count FROM opportunities');
    if (count === 0) {
      const [accountRows, productRows, teamRows, pipelineRows] = await Promise.all([
        readCsv('accounts.csv'), readCsv('products.csv'), readCsv('sales_teams.csv'), readCsv('sales_pipeline.csv'),
      ]);

      const accounts = accountRows.map((row) => ({
        account: row.account,
        sector_raw: nullable(row.sector),
        sector: row.sector === 'technolgy' ? 'technology' : nullable(row.sector),
        year_established: numberOrNull(row.year_established),
        revenue: numberOrNull(row.revenue),
        employees: numberOrNull(row.employees),
        office_location: nullable(row.office_location),
        subsidiary_of: nullable(row.subsidiary_of),
      }));
      const products = productRows.map((row) => ({ product: row.product, series: row.series, sales_price: Number(row.sales_price) }));
      const agents = teamRows.map((row) => ({ sales_agent: row.sales_agent, manager: row.manager, regional_office: row.regional_office }));
      const opportunities = pipelineRows.map((row) => ({
        opportunity_id: row.opportunity_id,
        sales_agent: row.sales_agent,
        product: row.product === 'GTXPro' ? 'GTX Pro' : row.product,
        account: nullable(row.account),
        deal_stage: row.deal_stage,
        engage_date: nullable(row.engage_date),
        close_date: nullable(row.close_date),
        close_value: numberOrNull(row.close_value),
      }));

      await database.transaction(async (transaction) => {
        await insertRows(transaction, 'accounts', ['account', 'sector_raw', 'sector', 'year_established', 'revenue', 'employees', 'office_location', 'subsidiary_of'], accounts, 'account');
        await insertRows(transaction, 'products', ['product', 'series', 'sales_price'], products, 'product');
        await insertRows(transaction, 'sales_agents', ['sales_agent', 'manager', 'regional_office'], agents, 'sales_agent');
        await insertRows(transaction, 'opportunities', ['opportunity_id', 'sales_agent', 'product', 'account', 'deal_stage', 'engage_date', 'close_date', 'close_value'], opportunities, 'opportunity_id');
      });
    }
}

export async function loadSourceRows() {
  const { rows } = await database.query(`
    SELECT o.*, p.series, p.sales_price::float,
      a.sector, a.year_established, a.revenue::float, a.employees,
      a.office_location, a.subsidiary_of,
      s.manager, s.regional_office
    FROM opportunities o
    JOIN products p ON p.product = o.product
    JOIN sales_agents s ON s.sales_agent = o.sales_agent
    LEFT JOIN accounts a ON a.account = o.account
  `);
  return rows;
}

export async function loadLatestActions() {
  const { rows } = await database.query(`
    SELECT DISTINCT ON (opportunity_id) *
    FROM deal_actions
    ORDER BY opportunity_id, created_at DESC, id DESC
  `);
  return new Map(rows.map((row) => [row.opportunity_id, row]));
}

export async function saveAction({ opportunityId, actorProfile, status, note, nextStep, dueDate }) {
  const completedAt = status === 'completed' ? new Date() : null;
  const { rows } = await database.query(`
    INSERT INTO deal_actions(opportunity_id, actor_profile, status, note, next_step, due_date, completed_at)
    VALUES ($1, $2, $3, $4, $5, $6, $7)
    RETURNING *
  `, [opportunityId, actorProfile, status, nullable(note), nullable(nextStep), nullable(dueDate), completedAt]);
  return rows[0];
}
