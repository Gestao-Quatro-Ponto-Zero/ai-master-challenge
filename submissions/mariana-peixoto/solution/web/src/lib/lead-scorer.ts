import fs from 'fs';
import path from 'path';

export interface ScoreFactor {
  label: string;
  points: number;
  description: string;
  positive: boolean;
}

export interface Deal {
  opportunity_id: string;
  sales_agent: string;
  product: string;
  account: string;
  deal_stage: 'Engaging' | 'Prospecting';
  engage_date: string;
  manager: string;
  regional_office: string;
  sector: string;
  revenue: number;
  employees: number;
  sales_price: number;
  score: number;
  score_breakdown: ScoreFactor[];
  recommendation: string;
  strategic_advice: string;
  days_in_pipeline: number;
}

export interface Summary {
  total_active: number;
  avg_score: number;
  by_stage: { Engaging: number; Prospecting: number };
  agents: string[];
  managers: string[];
  regions: string[];
}

function parseCSV(filePath: string): Record<string, string>[] {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n').filter((l) => l.trim());
  const headers = lines[0].split(',').map((h) => h.trim().replace(/\r/g, ''));
  return lines.slice(1).map((line) => {
    const values = line.split(',');
    return headers.reduce(
      (obj, header, i) => {
        obj[header] = (values[i] || '').trim().replace(/\r/g, '');
        return obj;
      },
      {} as Record<string, string>
    );
  });
}

// Dataset reference date (max date found in dataset)
const REFERENCE_DATE = new Date('2017-12-31');

export function loadAndScoreDeals(): { deals: Deal[]; summary: Summary } {
  const dataDir = path.join(process.cwd(), 'data');

  const pipeline = parseCSV(path.join(dataDir, 'sales_pipeline.csv'));
  const accounts = parseCSV(path.join(dataDir, 'accounts.csv'));
  const products = parseCSV(path.join(dataDir, 'products.csv'));
  const teams = parseCSV(path.join(dataDir, 'sales_teams.csv'));

  // Lookup maps
  const accountMap = Object.fromEntries(accounts.map((a) => [a.account, a]));
  const productMap = Object.fromEntries(products.map((p) => [p.product, p]));
  const teamMap = Object.fromEntries(teams.map((t) => [t.sales_agent, t]));

  // Win rates from historical Won/Lost data
  const agentStats: Record<string, { won: number; lost: number }> = {};
  for (const deal of pipeline) {
    const agent = deal.sales_agent;
    if (!agentStats[agent]) agentStats[agent] = { won: 0, lost: 0 };
    if (deal.deal_stage === 'Won') agentStats[agent].won++;
    if (deal.deal_stage === 'Lost') agentStats[agent].lost++;
  }

  const agentWinRates: Record<string, number> = {};
  for (const [agent, stats] of Object.entries(agentStats)) {
    const total = stats.won + stats.lost;
    agentWinRates[agent] = total > 0 ? stats.won / total : 0;
  }

  // Normalization anchors
  const maxRevenue = Math.max(...accounts.map((a) => parseFloat(a.revenue) || 0));
  const maxEmployees = Math.max(...accounts.map((a) => parseInt(a.employees) || 0));
  const maxPrice = Math.max(...products.map((p) => parseFloat(p.sales_price) || 0));

  // Win rate percentiles for rep tier classification
  const winRateValues = Object.values(agentWinRates).sort((a, b) => a - b);
  const p75 = winRateValues[Math.floor(winRateValues.length * 0.75)];

  // Process active deals only
  const activePipeline = pipeline.filter(
    (d) => d.deal_stage === 'Engaging' || d.deal_stage === 'Prospecting'
  );

  const deals: Deal[] = activePipeline.map((deal) => {
    const account = accountMap[deal.account] || {};
    const product = productMap[deal.product] || {};
    const team = teamMap[deal.sales_agent] || {};

    const revenue = parseFloat(account.revenue) || 0;
    const employees = parseInt(account.employees) || 0;
    const salesPrice = parseFloat(product.sales_price) || 0;
    const winRate = agentWinRates[deal.sales_agent] || 0;

    const engageDate = new Date(deal.engage_date);
    const daysInPipeline = Math.max(
      0,
      Math.floor((REFERENCE_DATE.getTime() - engageDate.getTime()) / (1000 * 60 * 60 * 24))
    );

    const factors: ScoreFactor[] = [];
    let totalScore = 0;

    // 1. Stage (max 25 pts)
    const stagePoints = deal.deal_stage === 'Engaging' ? 25 : 15;
    factors.push({
      label: 'Estágio do Deal',
      points: stagePoints,
      description:
        deal.deal_stage === 'Engaging'
          ? 'Em engajamento ativo — maior probabilidade de fechamento'
          : 'Em prospecção — início do funil',
      positive: true,
    });
    totalScore += stagePoints;

    // 2. Product value (max 20 pts)
    const priceScore = maxPrice > 0 ? Math.round((salesPrice / maxPrice) * 20) : 0;
    factors.push({
      label: 'Valor do Produto',
      points: priceScore,
      description: deal.product
        ? `${deal.product} — $${salesPrice.toLocaleString('pt-BR')} preço de tabela`
        : 'Nenhum produto vinculado',
      positive: priceScore >= 10,
    });
    totalScore += priceScore;

    // 3. Account profile (max 20 pts: 10 revenue + 10 employees)
    const revenueScore = maxRevenue > 0 ? Math.round((Math.min(revenue / maxRevenue, 1)) * 10) : 0;
    const employeeScore =
      maxEmployees > 0 ? Math.round((Math.min(employees / maxEmployees, 1)) * 10) : 0;
    const accountScore = revenueScore + employeeScore;
    factors.push({
      label: 'Perfil da Conta',
      points: accountScore,
      description: deal.account
        ? `Setor ${account.sector || 'desconhecido'} — $${revenue.toLocaleString('pt-BR', { maximumFractionDigits: 0 })}M de receita, ${employees.toLocaleString('pt-BR')} funcionários`
        : 'Nenhuma conta vinculada',
      positive: accountScore >= 10,
    });
    totalScore += accountScore;

    // 4. Pipeline velocity (max 20, min -5)
    let velocityPoints: number;
    let velocityDesc: string;
    if (daysInPipeline < 30) {
      velocityPoints = 20;
      velocityDesc = `${daysInPipeline} dias — oportunidade recente, alto momentum`;
    } else if (daysInPipeline < 60) {
      velocityPoints = 14;
      velocityDesc = `${daysInPipeline} dias — boa velocidade`;
    } else if (daysInPipeline < 90) {
      velocityPoints = 8;
      velocityDesc = `${daysInPipeline} dias — ritmo moderado`;
    } else if (daysInPipeline < 150) {
      velocityPoints = 2;
      velocityDesc = `${daysInPipeline} dias — desacelerando, precisa de atenção`;
    } else {
      velocityPoints = -5;
      velocityDesc = `${daysInPipeline} dias — deal parado, requalificar ou encerrar`;
    }
    factors.push({
      label: 'Velocidade no Pipeline',
      points: velocityPoints,
      description: velocityDesc,
      positive: velocityPoints > 0,
    });
    totalScore += velocityPoints;

    // 5. Rep performance (max 15 pts)
    let repPoints: number;
    let repDesc: string;
    const winPct = Math.round(winRate * 100);
    if (winRate >= p75) {
      repPoints = 15;
      repDesc = `${deal.sales_agent} — top performer (${winPct}% de taxa de fechamento)`;
    } else if (winRate >= 0.5) {
      repPoints = 10;
      repDesc = `${deal.sales_agent} — acima da média (${winPct}% de taxa de fechamento)`;
    } else if (winRate >= 0.35) {
      repPoints = 5;
      repDesc = `${deal.sales_agent} — performance média (${winPct}% de taxa de fechamento)`;
    } else {
      repPoints = 2;
      repDesc = `${deal.sales_agent} — em desenvolvimento (${winPct}% de taxa de fechamento)`;
    }
    factors.push({
      label: 'Performance do Vendedor',
      points: repPoints,
      description: repDesc,
      positive: repPoints >= 10,
    });
    totalScore += repPoints;

    const score = Math.max(0, Math.min(100, totalScore));

    let recommendation: string;
    if (score >= 70) {
      recommendation = 'Alta prioridade — agende uma ligação esta semana. Sinais fortes em todos os fatores.';
    } else if (score >= 50) {
      if (velocityPoints < 5) {
        recommendation = 'Reengajar agora — deal desacelerando. Envie um follow-up personalizado hoje.';
      } else {
        recommendation = 'Manter aquecido — bom potencial. Um contato direcionado pode acelerar o fechamento.';
      }
    } else if (velocityPoints < 0) {
      recommendation = 'Requalificar ou encerrar — deal estagnado. Decida rápido para liberar foco.';
    } else {
      recommendation = 'Baixa prioridade — monitore, mas direcione energia para oportunidades com score maior.';
    }

    let strategic_advice: string;
    if (score >= 85) {
      strategic_advice = 'Oportunidade excepcional. O perfil da conta e a velocidade indicam um "best-fit". Recomendo envolver um executivo sênior para formalizar a proposta final e garantir o fechamento até o fim do mês.';
    } else if (score >= 70) {
      strategic_advice = 'Deal maduro e com bom momentum. A estratégia deve focar em remover pequenos atritos contratuais. Agende uma demonstração técnica focada no ROI para validar o valor do produto.';
    } else if (velocityPoints < 0) {
      strategic_advice = 'Atenção: este deal está estagnado. A abordagem deve ser de "perda limpa" ou "re-engajamento agressivo". Envie um e-mail de "break-up" para testar o interesse real do cliente.';
    } else if (priceScore >= 15 && accountScore < 10) {
      strategic_advice = 'Ticket alto em conta de menor porte. O desafio aqui é a aprovação orçamentária. Foque em planos de pagamento flexíveis ou comece com um projeto piloto menor.';
    } else if (repPoints <= 5) {
      strategic_advice = 'Recomendo acompanhamento do Manager. O vendedor está em fase de desenvolvimento e este deal tem complexidades que podem se beneficiar de uma segunda voz na negociação.';
    } else {
      strategic_advice = 'Mantenha o radar ligado, mas não priorize ativamente. Use automação de marketing para nutrir este lead até que o score de velocidade ou estágio mude positivamente.';
    }

    return {
      opportunity_id: deal.opportunity_id,
      sales_agent: deal.sales_agent,
      product: deal.product,
      account: deal.account || '—',
      deal_stage: deal.deal_stage as 'Engaging' | 'Prospecting',
      engage_date: deal.engage_date,
      manager: team.manager || '—',
      regional_office: team.regional_office || '—',
      sector: account.sector || '—',
      revenue,
      employees,
      sales_price: salesPrice,
      score,
      score_breakdown: factors,
      recommendation,
      strategic_advice,
      days_in_pipeline: daysInPipeline,
    };
  });

  deals.sort((a, b) => b.score - a.score);

  const summary: Summary = {
    total_active: deals.length,
    avg_score: Math.round(deals.reduce((s, d) => s + d.score, 0) / deals.length),
    by_stage: {
      Engaging: deals.filter((d) => d.deal_stage === 'Engaging').length,
      Prospecting: deals.filter((d) => d.deal_stage === 'Prospecting').length,
    },
    agents: [...new Set(deals.map((d) => d.sales_agent))].sort(),
    managers: [...new Set(deals.map((d) => d.manager))].filter((m) => m !== '—').sort(),
    regions: [...new Set(deals.map((d) => d.regional_office))].filter((r) => r !== '—').sort(),
  };

  return { deals, summary };
}
