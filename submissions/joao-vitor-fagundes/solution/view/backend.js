const POWER_BACKEND = (() => {
  const SUPABASE_URL = "https://wbysjververrnohnoezb.supabase.co";
  const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndieXNqdmVydmVycm5vaG5vZXpiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc5NDY1ODcsImV4cCI6MjEwMzUyMjU4N30.a1CRx11P-c5sC2a9FfpNiDlCswSaOkUksUqlyYON280";
  const STAGES = ["Prospecting", "Engaging", "Won", "Lost"];
  const INITIAL_STAGE_SIZE = 50;
  const PAGE_SIZE = 1000;
  const PAGE_CONCURRENCY = 3;
  const REQUEST_TIMEOUT_MS = 8000;
  const MAX_PAGE_ATTEMPTS = 2;
  const LOCAL_READ_MODEL = ["127.0.0.1", "localhost"].includes(window.location.hostname)
    ? "/api/opportunity-power"
    : null;
  const PRIORITY_ORDER = [
    "power_priority_score.desc.nullslast",
    "opportunity_id.asc",
  ].join(",");
  const LIST_FIELDS = [
    "opportunity_id",
    "deal_stage",
    "engage_date",
    "close_date",
    "close_value",
    "snapshot_date",
    "potential_value",
    "age_days",
    "sales_agent",
    "manager",
    "regional_office",
    "product_key",
    "product",
    "series",
    "account",
    "sector",
    "revenue_musd",
    "employees",
    "office_location",
    "score_version",
    "input_hash",
    "propensity_score",
    "opportunity_value_score",
    "opportunity_value_tier",
    "warmth_score",
    "warmth_temperature",
    "execution_fit_score",
    "power_priority_score",
  ].join(",");

  function requestHeaders(extra = {}) {
    return {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
      ...extra,
    };
  }

  function wait(milliseconds) {
    return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
  }

  async function rest(path, options = {}) {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const remoteUrl = `${SUPABASE_URL}/rest/v1/${path}`;
      const query = path.includes("?") ? path.slice(path.indexOf("?")) : "";
      let response = LOCAL_READ_MODEL
        ? await fetch(`${LOCAL_READ_MODEL}${query}`, {
          ...options,
          headers: options.headers,
          cache: "default",
          signal: controller.signal,
        })
        : null;

      if (!response || response.status === 404 || response.status >= 500) {
        response = await fetch(remoteUrl, {
          ...options,
          headers: requestHeaders(options.headers),
          cache: "no-store",
          signal: controller.signal,
        });
      }

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Supabase ${response.status}: ${detail || response.statusText}`);
      }
      return response;
    } catch (error) {
      if (error.name === "AbortError") {
        throw new Error(`Supabase timeout after ${REQUEST_TIMEOUT_MS / 1000}s`);
      }
      throw error;
    } finally {
      window.clearTimeout(timeout);
    }
  }

  function mapOpportunity(row) {
    const issues = [];
    if (!row.account) issues.push("Conta ausente");
    if (!row.engage_date) issues.push("Data de contato ausente");
    if (row.propensity_score === null) issues.push("Histórico insuficiente para Propensity");
    if (row.execution_fit_score === null) issues.push("Histórico insuficiente para Execution Fit");

    return {
      id: row.opportunity_id,
      stage: row.deal_stage,
      seller: row.sales_agent,
      manager: row.manager,
      region: row.regional_office,
      product: row.product,
      product_key: row.product_key,
      series: row.series,
      potential_value: row.potential_value,
      close_value: row.close_value,
      account: row.account,
      sector: row.sector,
      account_revenue: row.revenue_musd,
      account_employees: row.employees,
      office_location: row.office_location,
      engage_date: row.engage_date,
      close_date: row.close_date,
      snapshot_date: row.snapshot_date,
      age_days: row.age_days,
      attention: row.warmth_temperature || row.deal_stage,
      issues,
      score_version: row.score_version,
      input_hash: row.input_hash,
      scores: {
        P: row.propensity_score,
        O: row.opportunity_value_score,
        W: row.warmth_score,
        E: row.execution_fit_score,
        PP: row.power_priority_score,
      },
      value_tier: row.opportunity_value_tier,
      temperature: row.warmth_temperature,
      propensity_evidence: row.propensity_evidence || null,
      warmth_evidence: row.warmth_evidence || null,
      execution_fit_evidence: row.execution_fit_evidence || null,
    };
  }

  async function fetchStagePage(stage, from, to, includeCount = false) {
    const response = await rest(`opportunity_power?select=${LIST_FIELDS}&deal_stage=eq.${encodeURIComponent(stage)}&order=${PRIORITY_ORDER}`, {
      headers: {
        Range: `${from}-${to}`,
        ...(includeCount ? { Prefer: "count=exact" } : {}),
      },
    });
    return {
      stage,
      rows: await response.json(),
      contentRange: response.headers.get("content-range"),
    };
  }

  async function fetchStagePageWithRetry(stage, from, to, includeCount = false) {
    let lastError;
    for (let attempt = 1; attempt <= MAX_PAGE_ATTEMPTS; attempt += 1) {
      try {
        return await fetchStagePage(stage, from, to, includeCount);
      } catch (error) {
        lastError = error;
        if (attempt < MAX_PAGE_ATTEMPTS) await wait(250 * attempt);
      }
    }
    throw lastError;
  }

  function emitProgress(onProgress, opportunities, total, state, failures = [], stageTotals = {}) {
    if (typeof onProgress !== "function") return;
    onProgress(
      buildPayload(opportunities, {
        total_available: total,
        load_state: state,
        failed_ranges: failures,
        stage_totals: stageTotals,
      }),
    );
  }

  function emitStatus(onStatus, opportunities, total, failures = []) {
    if (typeof onStatus !== "function") return;
    onStatus({
      loaded: opportunities.length,
      total,
      failed_ranges: failures.length,
    });
  }

  async function fetchAllOpportunities(onProgress, onStatus) {
    const seeds = await Promise.all(
      STAGES.map((stage) => fetchStagePageWithRetry(stage, 0, INITIAL_STAGE_SIZE - 1, true)),
    );
    const stageTotals = Object.fromEntries(
      seeds.map((seed) => [
        seed.stage,
        Number(seed.contentRange?.split("/").at(-1)) || seed.rows.length,
      ]),
    );
    const total = Object.values(stageTotals).reduce((sum, count) => sum + count, 0);
    const opportunities = seeds.flatMap((seed) => seed.rows.map(mapOpportunity));
    const ranges = STAGES.flatMap((stage) => {
      const stageRanges = [];
      for (let from = INITIAL_STAGE_SIZE; from < stageTotals[stage]; from += PAGE_SIZE) {
        stageRanges.push({
          stage,
          from,
          to: Math.min(from + PAGE_SIZE - 1, stageTotals[stage] - 1),
        });
      }
      return stageRanges;
    });

    emitProgress(onProgress, opportunities, total, ranges.length ? "loading" : "ready", [], stageTotals);

    const failures = [];
    let cursor = 0;
    const worker = async () => {
      while (cursor < ranges.length) {
        const rangeIndex = cursor;
        cursor += 1;
        const { stage, from, to } = ranges[rangeIndex];
        try {
          const page = await fetchStagePageWithRetry(stage, from, to);
          opportunities.push(...page.rows.map(mapOpportunity));
        } catch (error) {
          failures.push({ stage, from, to, message: error.message });
        }
        emitStatus(onStatus, opportunities, total, failures);
      }
    };

    const workers = Array.from(
      { length: Math.min(PAGE_CONCURRENCY, ranges.length) },
      () => worker(),
    );
    await Promise.all(workers);
    opportunities.sort((left, right) => left.id.localeCompare(right.id));

    return buildPayload(opportunities, {
      total_available: total,
      load_state: failures.length ? "partial" : "ready",
      failed_ranges: failures,
      stage_totals: stageTotals,
    });
  }

  function buildPayload(opportunities, load = {}) {
    const active = opportunities.filter((item) => ["Prospecting", "Engaging"].includes(item.stage));
    const stageCounts = Object.fromEntries(
      ["Prospecting", "Engaging", "Won", "Lost"].map((stage) => [
        stage,
        opportunities.filter((item) => item.stage === stage).length,
      ]),
    );
    const snapshotDate = opportunities.reduce(
      (latest, item) => (!latest || item.snapshot_date > latest ? item.snapshot_date : latest),
      null,
    );

    return {
      meta: {
        source: "Supabase · opportunity_power",
        snapshot_date: snapshotDate,
        total_opportunities: opportunities.length,
        total_available: load.total_available || opportunities.length,
        load_state: load.load_state || "ready",
        failed_ranges: load.failed_ranges || [],
        active_opportunities: active.length,
        pipeline_value: opportunities.reduce((sum, item) => sum + (item.potential_value || 0), 0),
        missing_account: opportunities.filter((item) => !item.account).length,
        stale_opportunities: active.filter((item) => item.temperature === "Estagnada").length,
        stage_counts: Object.keys(load.stage_totals || {}).length
          ? load.stage_totals
          : stageCounts,
      },
      filters: {
        sellers: [...new Set(opportunities.map((item) => item.seller).filter(Boolean))].sort(),
        regions: [...new Set(opportunities.map((item) => item.region).filter(Boolean))].sort(),
        products: [...new Set(opportunities.map((item) => item.product).filter(Boolean))].sort(),
      },
      opportunities,
    };
  }

  async function loadPipeline(options = {}) {
    return fetchAllOpportunities(options.onProgress, options.onStatus);
  }

  async function loadOpportunity(opportunityId) {
    const query = new URLSearchParams({
      select: "*",
      opportunity_id: `eq.${opportunityId}`,
      limit: "1",
    });
    const response = await rest(`opportunity_power?${query.toString()}`);
    const rows = await response.json();
    if (!rows[0]) throw new Error("Opportunity not found");
    return mapOpportunity(rows[0]);
  }

  async function generateRecommendation(opportunityId, attempt = 0) {
    const response = await fetch(`${SUPABASE_URL}/functions/v1/generate-recommendation`, {
      method: "POST",
      headers: requestHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ opportunity_id: opportunityId }),
    });
    const body = await response.json().catch(() => ({}));
    if (response.status === 202 && body.status === "generating") {
      if (attempt >= 20) throw new Error("Recommendation generation timed out");
      const retryAfter = Math.max(250, Math.min(2000, Number(body.retry_after_ms) || 750));
      await wait(retryAfter);
      return generateRecommendation(opportunityId, attempt + 1);
    }
    if (!response.ok) throw new Error(body.error || `Recommendation HTTP ${response.status}`);
    return body;
  }

  return { loadPipeline, loadOpportunity, generateRecommendation };
})();

window.POWER_BACKEND = POWER_BACKEND;
