// Lightweight, dependency-free i18n for the Pipeline Focus Console.
// Default language is Brazilian Portuguese (pt-BR). English preserves the
// original experience. Raw data values (accounts, sellers, ids, products,
// values) are never translated — only the labels shown in the UI.

export type Lang = "pt" | "en";

export const LANG_STORAGE_KEY = "pipeline-focus-lang";
export const DEFAULT_LANG: Lang = "pt";

export function readSavedLang(): Lang {
  if (typeof window === "undefined") return DEFAULT_LANG;
  try {
    const saved = window.localStorage.getItem(LANG_STORAGE_KEY);
    if (saved === "pt" || saved === "en") return saved;
  } catch {
    // localStorage is non-critical.
  }
  return DEFAULT_LANG;
}

const locale = (lang: Lang) => (lang === "pt" ? "pt-BR" : "en-US");

/** Locale-aware integer / count formatting (e.g. 2.089 in pt-BR). */
export function fmtNumber(n: number, lang: Lang): string {
  return new Intl.NumberFormat(locale(lang)).format(n || 0);
}

/** Currency in USD, grouped per active locale (US$ 1.700.000 in pt-BR). */
export function fmtUSD(n: number, lang: Lang): string {
  return new Intl.NumberFormat(locale(lang), {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n || 0);
}

/** Compact currency (US$ 1,7 mi in pt-BR, $1.7M in en-US). */
export function fmtCompactUSD(n: number, lang: Lang): string {
  return new Intl.NumberFormat(locale(lang), {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(n || 0);
}

// ---- Stage & priority label maps (display only; raw value kept for logic) ----

export function stageLabel(stage: string, lang: Lang): string {
  if (lang === "en") return stage;
  const map: Record<string, string> = {
    Prospecting: "Prospecção",
    Engaging: "Em negociação",
    Won: "Ganho",
    Lost: "Perdido",
  };
  return map[stage] ?? stage;
}

export function priorityLabel(priority: string, lang: Lang): string {
  if (lang === "en") {
    return (
      { High: "High priority", Priority: "Priority", Watch: "Watch", Low: "Low" }[priority] ??
      priority
    );
  }
  return (
    { High: "Alta prioridade", Priority: "Prioritário", Watch: "Acompanhar", Low: "Baixa" }[
      priority
    ] ?? priority
  );
}

// ---- Static UI dictionary (flat keys, {param} placeholders) ----

type Dict = Record<string, string>;

const EN: Dict = {
  "app.subtitle": "Prioritize the deals sellers should act on now",
  "header.scoringLogic": "Scoring logic",

  "status.liveCsvs": "CRM connected · {n} deals",
  "status.noData": "CRM data unavailable",
  "status.checking": "Connecting CRM…",

  "metric.openDeals": "Open deals",
  "metric.openDeals.sub": "in the active pipeline",
  "metric.highPriority": "High-priority",
  "metric.highPriority.sub": "score 80+ — act now",
  "metric.prioritizedValue": "Prioritized value",
  "metric.prioritizedValue.sub": "High + Priority deals",
  "metric.coolingRisk": "Cooling risk",
  "metric.coolingRisk.sub": "{value} at risk",

  "morning.kicker": "Monday morning brief",
  "morning.title": "Start with the deals that move revenue now",
  "morning.subtitle":
    "A seller can open this console and leave with the first move, the risk queue and the manager escalations.",
  "morning.firstMove": "First move",
  "morning.noDeal": "No open deal",
  "morning.score": "score {score} with {seller}",
  "morning.high.label": "High priority",
  "morning.high.sub": "{value} in high-score deals",
  "morning.cooling.label": "Cooling",
  "morning.cooling.sub": "{value} needs attention",
  "morning.manager.label": "Manager review",
  "morning.manager.sub": "low-confidence or escalation cases",

  "manager.kicker": "RevOps manager view",
  "manager.title": "Where leadership should focus the pipeline",
  "manager.unknown": "Unassigned manager",
  "manager.open": "Open",
  "manager.high": "High",
  "manager.cooling": "Cooling",
  "manager.avg": "Avg score",
  "manager.score": "score {score}",
  "manager.riskValue": "{value} cooling value",

  "quality.kicker": "Score quality",
  "quality.title": "Confidence and data limitations",
  "quality.estimated": "Estimated value",
  "quality.limited": "With limitations",
  "quality.note":
    "The score stays usable, but every missing join, estimated value or fallback is disclosed instead of hidden.",

  "filter.search": "Search account or opportunity…",
  "filter.seller": "Seller",
  "filter.manager": "Manager",
  "filter.region": "Region",
  "filter.stage": "Stage",
  "filter.priority": "Priority",
  "filter.product": "Product",
  "filter.allSuffix": "{label}: All",
  "filter.clear": "Clear",
  "filter.showing": "Showing {n} prioritized deals",

  "table.noMatch.title": "No deals match these filters",
  "table.noMatch.sub": "Adjust or clear the filters to see open opportunities.",
  "table.queueTitle": "Prioritized deal queue",
  "table.showingOf": "Showing {x} of {y} filtered deals.",
  "table.csvPrepared": "CSV prepared with {n} rows.",
  "table.export": "Export CSV",
  "table.col.rank": "#",
  "table.col.oppAccount": "Opportunity / Account",
  "table.col.sellerRegion": "Seller / Region",
  "table.col.stage": "Stage",
  "table.col.value": "Value",
  "table.col.score": "Score",
  "table.col.nextAction": "Next best action",
  "table.open": "open",
  "table.est": "est.",
  "table.showNext": "Show next {n} deals",

  "panel.totalScore": "Total score",
  "panel.daysOpen": "{n} days open",
  "panel.whyThisScore": "Why this score",
  "panel.nextBestAction": "Next best action",
  "panel.positiveFactors": "Positive factors",
  "panel.riskFactors": "Risk factors",
  "panel.scoreBreakdown": "Score breakdown",
  "panel.dataUsed": "Data used",
  "panel.limitations": "Limitations",
  "panel.noLimitations":
    "Rule-based score v0 — no predictive model. All inputs come from the CRM data tables.",
  "panel.selectDeal": "Select a deal",
  "panel.selectDeal.sub": "Click any row to see its score, reasons and recommended action.",

  "scoring.title": "Scoring logic — v0",
  "scoring.description":
    "A transparent, rule-based score from 0–100. No black box: every point traces back to CRM data.",
  "scoring.formula.heading": "The formula",
  "scoring.formula.text":
    "score = Σ (factor score × weight), normalized to 0–100. Each factor is scored 0–1 against the rest of the pipeline, then weighted below.",
  "scoring.weights.heading": "Weights",
  "scoring.bands.heading": "Priority bands",
  "scoring.bands.high": "80–100 · High priority",
  "scoring.bands.high.note": "act now",
  "scoring.bands.priority": "60–79 · Priority",
  "scoring.bands.priority.note": "work this week",
  "scoring.bands.watch": "40–59 · Watch",
  "scoring.bands.watch.note": "monitor",
  "scoring.bands.low": "0–39 · Low",
  "scoring.bands.low.note": "deprioritize",
  "scoring.explain.heading": "Why it's explainable",
  "scoring.explain.1":
    "Only open deals (Prospecting, Engaging) are scored — closed deals feed the win-rate signal.",
  "scoring.explain.2": "It never ranks on deal value alone — value is one of six weighted factors.",
  "scoring.explain.3":
    "Each deal shows its positive factors, risk factors, data used and limitations.",
  "scoring.explain.4": "Missing data falls back to neutral and is disclosed as a limitation.",
  "scoring.reference":
    "Reference “today” = latest date in the data ({date}). Team win rate: {rate}%.",

  "scoring.w.stage": "Stage",
  "scoring.w.stage.desc":
    "Engaging deals outrank prospecting — a confirmed buyer is closer to revenue.",
  "scoring.w.value": "Value",
  "scoring.w.value.desc":
    "Expected value (close value, or product list price when no value is set) ranked against the open pipeline.",
  "scoring.w.fit": "Account fit",
  "scoring.w.fit.desc":
    "Account revenue and headcount vs. peers — larger accounts carry more budget.",
  "scoring.w.timing": "Timing / risk",
  "scoring.w.timing.desc":
    "Days open since the engage date. Fresh deals keep momentum; aging deals lose points and flag cooling risk.",
  "scoring.w.product": "Product signal",
  "scoring.w.product.desc": "Product price tier — premium products signal higher strategic value.",
  "scoring.w.rep": "Rep / manager / region",
  "scoring.w.rep.desc":
    "Historical win rate from closed deals (won ÷ closed), falling back to manager, region, then team average.",

  "empty.loading.title": "Connecting to CRM data",
  "empty.loading.body": "Preparing the prioritized pipeline with the official opportunity data.",
  "empty.unavailable.title": "CRM data unavailable",
  "empty.unavailable.body":
    "The console could not load the operational pipeline data. Retry the connection or check the data bundle before using the queue.",
  "empty.retry": "Retry connection",

  "chips.label": "Focus",
  "chips.actNow": "Act now",
  "chips.highScore": "High score",
  "chips.coolingRisk": "Cooling risk",
  "chips.managerReview": "Manager review",
  "chips.engaging": "Engaging",
  "chips.prospecting": "Prospecting",

  "confidence.label": "Confidence",
  "confidence.High": "High",
  "confidence.Medium": "Medium",
  "confidence.Low": "Low",
  "confidence.High.desc": "Complete joins, few limitations.",
  "confidence.Medium.desc": "Estimated value or a light fallback.",
  "confidence.Low.desc": "Missing joins, dates or key fields.",

  "table.copyList": "Copy action list",
  "table.copied": "Top {n} copied to clipboard.",
  "table.copyFailed": "Clipboard permission blocked. Select and copy the visible list manually.",
  "table.copyFallbackLabel": "Action list ready to copy manually",
  "table.downloadReady": "Download CSV ready",
  "table.estValue": "Estimated from product price",
  "table.aria.copyList": "Copy action list",
  "table.aria.export": "Export CSV",

  "panel.dataQuality": "Data quality",
  "panel.estimatedValue": "Estimated value (product list price — not a contracted value).",
  "panel.priority": "Priority",

  "scoring.note.heading": "How deals enter the score",
  "scoring.note.1": "Only open deals (Prospecting, Engaging) are scored.",
  "scoring.note.2": "Won / Lost deals feed the win-rate history, not the queue.",
  "scoring.note.3": "Open deals with no close_value use the product list price.",
  "scoring.note.4": "The score never ranks by value alone.",
};

const PT: Dict = {
  "app.subtitle": "Priorize os negócios que o vendedor deve atacar agora",
  "header.scoringLogic": "Lógica da pontuação",

  "status.liveCsvs": "CRM conectado · {n} negócios",
  "status.noData": "Dados do CRM indisponíveis",
  "status.checking": "Conectando ao CRM…",

  "metric.openDeals": "Negócios abertos",
  "metric.openDeals.sub": "no pipeline ativo",
  "metric.highPriority": "Alta prioridade",
  "metric.highPriority.sub": "score 80+ — aja agora",
  "metric.prioritizedValue": "Valor priorizado",
  "metric.prioritizedValue.sub": "Negócios Alta + Prioritário",
  "metric.coolingRisk": "Risco de esfriamento",
  "metric.coolingRisk.sub": "{value} em risco",

  "morning.kicker": "Brief de segunda-feira",
  "morning.title": "Comece pelos negócios que mexem na receita agora",
  "morning.subtitle":
    "O vendedor abre o console e sai com o primeiro movimento, a fila de risco e os casos para escalar ao manager.",
  "morning.firstMove": "Primeiro movimento",
  "morning.noDeal": "Nenhum negócio aberto",
  "morning.score": "score {score} com {seller}",
  "morning.high.label": "Alta prioridade",
  "morning.high.sub": "{value} em deals de score alto",
  "morning.cooling.label": "Esfriando",
  "morning.cooling.sub": "{value} precisa de atenção",
  "morning.manager.label": "Revisão do manager",
  "morning.manager.sub": "baixa confiança ou casos de escalada",

  "manager.kicker": "Visão RevOps para managers",
  "manager.title": "Onde a liderança deve focar o pipeline",
  "manager.unknown": "Manager não atribuído",
  "manager.open": "Abertos",
  "manager.high": "Alta",
  "manager.cooling": "Esfriando",
  "manager.avg": "Score médio",
  "manager.score": "score {score}",
  "manager.riskValue": "{value} esfriando",

  "quality.kicker": "Qualidade do score",
  "quality.title": "Confiança e limitações dos dados",
  "quality.estimated": "Valor estimado",
  "quality.limited": "Com limitações",
  "quality.note":
    "A pontuação continua utilizável, mas cada join ausente, valor estimado ou fallback fica explícito em vez de escondido.",

  "filter.search": "Buscar conta ou oportunidade…",
  "filter.seller": "Vendedor",
  "filter.manager": "Gerente",
  "filter.region": "Região",
  "filter.stage": "Estágio",
  "filter.priority": "Prioridade",
  "filter.product": "Produto",
  "filter.allSuffix": "{label}: Todos",
  "filter.clear": "Limpar",
  "filter.showing": "Exibindo {n} negócios priorizados",

  "table.noMatch.title": "Nenhum negócio corresponde a esses filtros",
  "table.noMatch.sub": "Ajuste ou limpe os filtros para ver oportunidades abertas.",
  "table.queueTitle": "Fila de oportunidades priorizadas",
  "table.showingOf": "Exibindo {x} de {y} negócios filtrados.",
  "table.csvPrepared": "CSV preparado com {n} linhas.",
  "table.export": "Exportar CSV",
  "table.col.rank": "#",
  "table.col.oppAccount": "Oportunidade / Conta",
  "table.col.sellerRegion": "Vendedor / Região",
  "table.col.stage": "Estágio",
  "table.col.value": "Valor",
  "table.col.score": "Pontuação",
  "table.col.nextAction": "Próxima melhor ação",
  "table.open": "aberto",
  "table.est": "est.",
  "table.showNext": "Mostrar próximos {n} negócios",

  "panel.totalScore": "Pontuação total",
  "panel.daysOpen": "{n} dias aberto",
  "panel.whyThisScore": "Por que esta pontuação",
  "panel.nextBestAction": "Próxima melhor ação",
  "panel.positiveFactors": "Fatores positivos",
  "panel.riskFactors": "Fatores de risco",
  "panel.scoreBreakdown": "Composição da pontuação",
  "panel.dataUsed": "Dados utilizados",
  "panel.limitations": "Limitações",
  "panel.noLimitations":
    "Pontuação baseada em regras v0 — sem modelo preditivo. Todas as entradas vêm das tabelas do CRM.",
  "panel.selectDeal": "Selecione um negócio",
  "panel.selectDeal.sub":
    "Clique em qualquer linha para ver a pontuação, os motivos e a ação recomendada.",

  "scoring.title": "Lógica da pontuação — v0",
  "scoring.description":
    "Uma pontuação transparente, baseada em regras, de 0 a 100. Sem caixa-preta: cada ponto remonta aos dados do CRM.",
  "scoring.formula.heading": "A fórmula",
  "scoring.formula.text":
    "pontuação = Σ (nota do fator × peso), normalizada de 0 a 100. Cada fator recebe nota de 0 a 1 em relação ao restante do pipeline e depois é ponderado abaixo.",
  "scoring.weights.heading": "Pesos",
  "scoring.bands.heading": "Faixas de prioridade",
  "scoring.bands.high": "80–100 · Alta prioridade",
  "scoring.bands.high.note": "aja agora",
  "scoring.bands.priority": "60–79 · Prioritário",
  "scoring.bands.priority.note": "trabalhar esta semana",
  "scoring.bands.watch": "40–59 · Acompanhar",
  "scoring.bands.watch.note": "monitorar",
  "scoring.bands.low": "0–39 · Baixa",
  "scoring.bands.low.note": "despriorizar",
  "scoring.explain.heading": "Por que é explicável",
  "scoring.explain.1":
    "Só negócios abertos (Prospecção, Em negociação) são pontuados — negócios fechados alimentam o sinal de win rate.",
  "scoring.explain.2":
    "Nunca prioriza pelo valor do negócio sozinho — o valor é um de seis fatores ponderados.",
  "scoring.explain.3":
    "Cada negócio mostra seus fatores positivos, fatores de risco, dados usados e limitações.",
  "scoring.explain.4": "Dados ausentes voltam ao neutro e são divulgados como uma limitação.",
  "scoring.reference":
    "“Hoje” de referência = data mais recente nos dados ({date}). Win rate do time: {rate}%.",

  "scoring.w.stage": "Estágio",
  "scoring.w.stage.desc":
    "Negócios em negociação superam os de prospecção — um comprador confirmado está mais perto da receita.",
  "scoring.w.value": "Valor",
  "scoring.w.value.desc":
    "Valor esperado (valor de fechamento, ou preço de tabela do produto quando não há valor) comparado ao pipeline aberto.",
  "scoring.w.fit": "Aderência da conta",
  "scoring.w.fit.desc":
    "Receita e número de funcionários da conta vs. pares — contas maiores têm mais orçamento.",
  "scoring.w.timing": "Tempo / risco",
  "scoring.w.timing.desc":
    "Dias em aberto desde a data de engajamento. Negócios recentes mantêm o ritmo; os antigos perdem pontos e sinalizam risco de esfriamento.",
  "scoring.w.product": "Sinal de produto",
  "scoring.w.product.desc":
    "Faixa de preço do produto — produtos premium sinalizam maior valor estratégico.",
  "scoring.w.rep": "Vendedor / gerente / região",
  "scoring.w.rep.desc":
    "Win rate histórico de negócios fechados (ganhos ÷ fechados), recorrendo a gerente, região e, por fim, à média do time.",

  "empty.loading.title": "Conectando aos dados do CRM",
  "empty.loading.body": "Preparando o pipeline priorizado com a base oficial de oportunidades.",
  "empty.unavailable.title": "Dados do CRM indisponíveis",
  "empty.unavailable.body":
    "O console não conseguiu carregar os dados operacionais do pipeline. Tente reconectar ou verifique o pacote de dados antes de usar a fila.",
  "empty.retry": "Tentar reconectar",

  "chips.label": "Foco",
  "chips.actNow": "Ação agora",
  "chips.highScore": "Score alto",
  "chips.coolingRisk": "Risco de esfriar",
  "chips.managerReview": "Revisão do manager",
  "chips.engaging": "Em negociação",
  "chips.prospecting": "Prospecção",

  "confidence.label": "Confiança",
  "confidence.High": "Alta",
  "confidence.Medium": "Média",
  "confidence.Low": "Baixa",
  "confidence.High.desc": "Joins completos, poucas limitações.",
  "confidence.Medium.desc": "Valor estimado ou fallback leve.",
  "confidence.Low.desc": "Faltam joins, datas ou campos importantes.",

  "table.copyList": "Copiar lista de ações",
  "table.copied": "Top {n} copiados para a área de transferência.",
  "table.copyFailed":
    "Permissão da área de transferência bloqueada. Selecione e copie a lista visível manualmente.",
  "table.copyFallbackLabel": "Lista de ações pronta para copiar manualmente",
  "table.downloadReady": "Baixar CSV pronto",
  "table.estValue": "Estimado pelo preço do produto",
  "table.aria.copyList": "Copiar lista de ações",
  "table.aria.export": "Exportar CSV",

  "panel.dataQuality": "Qualidade dos dados",
  "panel.estimatedValue": "Valor estimado (preço de tabela do produto — não é valor contratado).",
  "panel.priority": "Prioridade",

  "scoring.note.heading": "Como os negócios entram na pontuação",
  "scoring.note.1": "Apenas negócios abertos (Prospecção, Em negociação) são pontuados.",
  "scoring.note.2": "Negócios Ganho / Perdido alimentam o histórico de win rate, não a fila.",
  "scoring.note.3": "Negócios abertos sem close_value usam o preço de tabela do produto.",
  "scoring.note.4": "A pontuação nunca ordena apenas pelo valor.",
};

const DICTS: Record<Lang, Dict> = { pt: PT, en: EN };

export function translate(
  lang: Lang,
  key: string,
  params?: Record<string, string | number>,
): string {
  let str = DICTS[lang][key] ?? DICTS.en[key] ?? key;
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      str = str.replace(new RegExp(`\\{${k}\\}`, "g"), String(v));
    }
  }
  return str;
}

// ---- Localized strings produced by the scoring engine ----

export interface ScoringStrings {
  repBasis: { rep: string; manager: string; region: string; team: string };
  dataUsed: {
    stage: (s: string) => string;
    value: (usd: string, estimated: boolean) => string;
    revenue: (m: number) => string;
    employees: (n: string) => string;
    sector: (s: string) => string;
    open: (days: number) => string;
    line: (series: string) => string;
  };
  lim: {
    noCloseValue: string;
    noAccount: string;
    accountNotFound: string;
    noEngageDate: string;
    noProductPrice: string;
    notEnoughClosed: string;
    agentNotFound: string;
  };
  factor: {
    activeEngagement: { label: string; detail: string };
    earlyStage: { label: string; detail: string };
    highValue: (usd: string) => { label: string; detail: string };
    smallerDeal: (usd: string) => { label: string; detail: string };
    strongFit: (sector: string) => { label: string; detail: string };
    smallerAccount: { label: string; detail: string };
    coolingRisk: (days: number | null) => { label: string; detail: string };
    freshMomentum: (days: number | null) => { label: string; detail: string };
    premiumProduct: (name: string) => { label: string; detail: string };
    reliableCloser: (pct: number, basis: string) => { label: string; detail: string };
    belowAverage: (pct: number, basis: string) => { label: string; detail: string };
  };
  valuePhrase: (usd: string, product: string, account: string, id: string) => string;
  why: (
    priority: string,
    args: { phrase: string; isEngaging: boolean; pct: number; stale: boolean },
  ) => string;
  risk: (args: {
    stale: boolean;
    days: number | null;
    isEngaging: boolean;
    repLow: boolean;
    pct: number;
    estimated: boolean;
  }) => string;
  nextAction: (
    kind:
      | "revive"
      | "callToday"
      | "engageBuyer"
      | "followUp"
      | "qualify"
      | "managerReview"
      | "monitor"
      | "deprioritize",
  ) => string;
}

export function buildScoringStrings(lang: Lang): ScoringStrings {
  const sl = (s: string) => stageLabel(s, lang);
  if (lang === "pt") {
    return {
      repBasis: {
        rep: "histórico do vendedor",
        manager: "histórico do gerente",
        region: "histórico da região",
        team: "média do time",
      },
      dataUsed: {
        stage: (s) => `Estágio: ${sl(s)}`,
        value: (usd, est) =>
          `Valor esperado: ${usd}${est ? " (estimado pelo preço de tabela)" : ""}`,
        revenue: (m) => `Receita da conta: US$ ${m}M`,
        employees: (n) => `Funcionários: ${n}`,
        sector: (s) => `Setor: ${s}`,
        open: (d) => `Aberto há ${d} dias (desde o engajamento)`,
        line: (series) => `Linha de produto: ${series}`,
      },
      lim: {
        noCloseValue: "Sem close_value ainda — valor estimado pelo preço de tabela do produto.",
        noAccount: "Nenhuma conta vinculada ao negócio — aderência definida como neutra.",
        accountNotFound: "Conta não encontrada na base de contas — aderência definida como neutra.",
        noEngageDate: "Sem data de engajamento — tempo definido como neutro.",
        noProductPrice: "Preço do produto ausente — sinal de produto neutro.",
        notEnoughClosed:
          "Negócios fechados insuficientes para este vendedor — usamos o win rate do time.",
        agentNotFound: "Vendedor não encontrado na base comercial — gerente/região desconhecidos.",
      },
      factor: {
        activeEngagement: {
          label: "Engajamento ativo",
          detail: "O comprador está engajado, não apenas prospectado.",
        },
        earlyStage: {
          label: "Estágio inicial",
          detail: "Ainda em prospecção — sem engajamento confirmado.",
        },
        highValue: (usd) => ({
          label: "Negócio de alto valor",
          detail: `${usd} — topo do pipeline aberto.`,
        }),
        smallerDeal: (usd) => ({
          label: "Negócio menor",
          detail: `${usd} — parte de baixo do pipeline aberto.`,
        }),
        strongFit: (sector) => ({
          label: "Forte aderência da conta",
          detail: `${sector} com receita e equipe expressivas.`,
        }),
        smallerAccount: {
          label: "Conta menor",
          detail: "Receita/equipe limitadas vs. pares.",
        },
        coolingRisk: (days) => ({
          label: "Risco de esfriamento",
          detail: `Aberto há ${days} dias sem fechar — risco de esfriar.`,
        }),
        freshMomentum: (days) => ({
          label: "Ritmo recente",
          detail: days != null ? `Engajado há ${days} dias.` : "Atividade recente.",
        }),
        premiumProduct: (name) => ({
          label: "Produto premium",
          detail: `${name} — faixa de preço mais alta.`,
        }),
        reliableCloser: (pct, basis) => ({
          label: "Fechador confiável",
          detail: `${pct}% de win rate (${basis}).`,
        }),
        belowAverage: (pct, basis) => ({
          label: "Win rate abaixo da média",
          detail: `${pct}% de win rate (${basis}).`,
        }),
      },
      valuePhrase: (usd, product, account, id) =>
        account
          ? `negócio de ${usd} em ${product} na ${account}`
          : `oportunidade de ${usd} em ${product} (${id})`,
      why: (priority, { phrase, isEngaging, pct, stale }) => {
        if (priority === "High")
          return `Prioridade máxima: ${phrase}. ${
            isEngaging ? "O comprador está engajado" : "Fundamentos sólidos"
          } e ${pct}% de win rate do vendedor fazem deste um foco claro.`;
        if (priority === "Priority")
          return `Boa oportunidade: ${phrase}. Boa combinação de valor, aderência e timing — vale trabalhar esta semana.`;
        if (priority === "Watch")
          return `Sinais mistos: ${phrase}. Há algum potencial, mas ${
            stale ? "está aberto há um tempo." : "a aderência ou o estágio é fraco."
          }`;
        return `Baixa prioridade: ${phrase}. Combinação fraca de estágio, valor, aderência ou timing no momento.`;
      },
      risk: ({ stale, days, isEngaging, repLow, pct, estimated }) => {
        if (stale) return `Aberto há ${days} dias — o ritmo está caindo e o negócio pode esfriar.`;
        if (!isEngaging) return "Ainda em prospecção — sem engajamento confirmado do comprador.";
        if (repLow) return `Vendedor abaixo do win rate do time (${pct}%); pode precisar de apoio.`;
        if (estimated)
          return "Sem valor de fechamento acordado — termos econômicos não confirmados.";
        return "Risco imediato baixo — mantenha o ritmo.";
      },
      nextAction: (kind) =>
        ({
          revive: "Reativar ou desqualificar",
          callToday: "Ligar hoje",
          engageBuyer: "Engajar o decisor agora",
          followUp: "Fazer follow-up nesta semana",
          qualify: "Qualificar o comprador",
          managerReview: "Revisão com o gerente",
          monitor: "Monitorar",
          deprioritize: "Despriorizar",
        })[kind],
    };
  }

  // English (original wording preserved)
  return {
    repBasis: {
      rep: "rep history",
      manager: "manager history",
      region: "region history",
      team: "team average",
    },
    dataUsed: {
      stage: (s) => `Deal stage: ${s}`,
      value: (usd, est) => `Expected value: ${usd}${est ? " (list price estimate)" : ""}`,
      revenue: (m) => `Account revenue: $${m}M`,
      employees: (n) => `Employees: ${n}`,
      sector: (s) => `Sector: ${s}`,
      open: (d) => `Open for ${d} days (since engage date)`,
      line: (series) => `Product line: ${series}`,
    },
    lim: {
      noCloseValue: "No close_value yet — value estimated from product list price.",
      noAccount: "No account linked to the deal — fit set to neutral.",
      accountNotFound: "Account not found in the account data — fit set to neutral.",
      noEngageDate: "No engage date — timing set to neutral.",
      noProductPrice: "Product price missing — product signal neutral.",
      notEnoughClosed: "Not enough closed deals for this rep — used team-wide win rate.",
      agentNotFound: "Sales agent not found in the sales team data — manager/region unknown.",
    },
    factor: {
      activeEngagement: {
        label: "Active engagement",
        detail: "Buyer is engaged, not just prospected.",
      },
      earlyStage: { label: "Early stage", detail: "Still prospecting — not yet engaged." },
      highValue: (usd) => ({
        label: "High-value deal",
        detail: `${usd} — top tier of open pipeline.`,
      }),
      smallerDeal: (usd) => ({
        label: "Smaller deal",
        detail: `${usd} — lower end of open pipeline.`,
      }),
      strongFit: (sector) => ({
        label: "Strong account fit",
        detail: `${sector} with significant revenue and headcount.`,
      }),
      smallerAccount: {
        label: "Smaller account",
        detail: "Limited revenue/headcount vs. peers.",
      },
      coolingRisk: (days) => ({
        label: "Cooling risk",
        detail: `Open ${days} days with no close — at risk of going stale.`,
      }),
      freshMomentum: (days) => ({
        label: "Fresh momentum",
        detail: days != null ? `Engaged ${days} days ago.` : "Recent activity.",
      }),
      premiumProduct: (name) => ({
        label: "Premium product",
        detail: `${name} — higher price tier.`,
      }),
      reliableCloser: (pct, basis) => ({
        label: "Reliable closer",
        detail: `${pct}% win rate (${basis}).`,
      }),
      belowAverage: (pct, basis) => ({
        label: "Below-average win rate",
        detail: `${pct}% win rate (${basis}).`,
      }),
    },
    valuePhrase: (usd, product, account, id) =>
      account ? `${usd} ${product} deal at ${account}` : `${usd} ${product} opportunity ${id}`,
    why: (priority, { phrase, isEngaging, pct, stale }) => {
      if (priority === "High")
        return `Top-priority: ${phrase}. ${
          isEngaging ? "Buyer is engaged" : "Strong fundamentals"
        } and ${pct}% rep win rate make this a clear focus.`;
      if (priority === "Priority")
        return `Solid opportunity: ${phrase}. Good mix of value, fit and timing — worth working this week.`;
      if (priority === "Watch")
        return `Mixed signals on the ${phrase}. Some upside but ${
          stale ? "it's been open a while" : "fit or stage is weak"
        }.`;
      return `Low priority: ${phrase}. Weak combination of stage, value, fit or timing right now.`;
    },
    risk: ({ stale, days, isEngaging, repLow, pct, estimated }) => {
      if (stale) return `Open for ${days} days — momentum is fading and the deal may go cold.`;
      if (!isEngaging) return "Still in prospecting — no confirmed buyer engagement yet.";
      if (repLow) return `Rep is below team win rate (${pct}%); deal may need support.`;
      if (estimated) return "No agreed close value yet — economic terms unconfirmed.";
      return "Low immediate risk — keep the momentum going.";
    },
    nextAction: (kind) =>
      ({
        revive: "Revive or disqualify",
        callToday: "Call today",
        engageBuyer: "Engage economic buyer now",
        followUp: "Follow up this week",
        qualify: "Qualify the buyer",
        managerReview: "Manager review",
        monitor: "Monitor",
        deprioritize: "Deprioritize",
      })[kind],
  };
}
