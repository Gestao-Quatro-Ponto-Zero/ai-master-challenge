import os
import sys
from contextlib import asynccontextmanager
from functools import lru_cache

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client

# Add parent dir to path for scoring/ai imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from scoring.engine import score_pipeline, get_pipeline_metrics, get_deal_explanations
from scoring.features import compute_global_stats

# --- Globals ---
DATA_CACHE: dict = {}
SCORED_CACHE: pd.DataFrame = pd.DataFrame()
STATS_CACHE: dict = {}


def get_supabase_admin():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    return create_client(url, key)


def load_all_data():
    global DATA_CACHE, SCORED_CACHE, STATS_CACHE
    sb = get_supabase_admin()

    accounts = pd.DataFrame(sb.table("accounts").select("*").execute().data)
    products = pd.DataFrame(sb.table("products").select("*").execute().data)
    teams = pd.DataFrame(sb.table("sales_teams").select("*").execute().data)

    all_data = []
    offset = 0
    while True:
        result = sb.table("sales_pipeline").select("*").range(offset, offset + 999).execute()
        if not result.data:
            break
        all_data.extend(result.data)
        if len(result.data) < 1000:
            break
        offset += 1000

    pipeline = pd.DataFrame(all_data)
    if not pipeline.empty:
        pipeline["engage_date"] = pd.to_datetime(pipeline["engage_date"])
        pipeline["close_date"] = pd.to_datetime(pipeline["close_date"])

    DATA_CACHE = {"accounts": accounts, "products": products, "teams": teams, "pipeline": pipeline}
    SCORED_CACHE = score_pipeline(pipeline, accounts, products, teams)
    STATS_CACHE = compute_global_stats(pipeline, accounts, products, teams)

    return DATA_CACHE


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_all_data()
    yield


app = FastAPI(title="Lead Scorer API", lifespan=lifespan)

CORS_DOMAIN = os.getenv("CORS_DOMAIN", "bredasudre.com")
_cors_escaped = CORS_DOMAIN.replace(".", r"\.")
_cors_regex = rf"https?://(.*\.)?({_cors_escaped}|easypanel\.host)(:\d+)?"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=_cors_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Auth dependency with cache ---
_auth_cache: dict[str, tuple[dict, float]] = {}
AUTH_CACHE_TTL = 300  # 5 minutes

async def get_current_user(authorization: str = Header(None)):
    """Verify Supabase JWT and return user profile (cached)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Token não fornecido")

    token = authorization.replace("Bearer ", "")

    # Check cache
    import time
    now = time.time()
    if token in _auth_cache:
        profile, cached_at = _auth_cache[token]
        if now - cached_at < AUTH_CACHE_TTL:
            return profile

    sb = get_supabase_admin()

    try:
        user = sb.auth.get_user(token)
        if not user or not user.user:
            raise HTTPException(status_code=401, detail="Token inválido")

        result = sb.table("users").select("*").eq("id", str(user.user.id)).execute()
        if not result.data:
            # Auto-create profile on first login (admin for evaluation purposes)
            # Production: change to "vendedor" and require admin promotion
            new_profile = {
                "id": str(user.user.id),
                "email": user.user.email,
                "role": "admin",
            }
            sb.table("users").insert(new_profile).execute()
            result = sb.table("users").select("*").eq("id", str(user.user.id)).execute()

        profile = result.data[0]
        _auth_cache[token] = (profile, now)
        return profile
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")


# --- Helper ---
def filter_by_role(scored: pd.DataFrame, profile: dict, teams: pd.DataFrame) -> pd.DataFrame:
    if profile["role"] == "admin":
        return scored
    elif profile["role"] == "vendedor":
        return scored[scored["sales_agent_id"] == profile["sales_team_id"]]
    elif profile["role"] == "manager":
        team_ids = teams[teams["manager"] == profile["manager_name"]]["id"].tolist()
        return scored[scored["sales_agent_id"].isin(team_ids)]
    return scored.head(0)


def filter_pipeline_by_role(pipeline: pd.DataFrame, profile: dict, teams: pd.DataFrame) -> pd.DataFrame:
    if profile["role"] == "admin":
        return pipeline
    elif profile["role"] == "vendedor":
        return pipeline[pipeline["sales_agent_id"] == profile["sales_team_id"]]
    elif profile["role"] == "manager":
        team_ids = teams[teams["manager"] == profile["manager_name"]]["id"].tolist()
        return pipeline[pipeline["sales_agent_id"].isin(team_ids)]
    return pipeline.head(0)


# --- Helper: serialize dataframe ---
def _serialize_df(df: pd.DataFrame, cols: list[str]) -> list[dict]:
    available = [c for c in cols if c in df.columns]
    records = df[available].to_dict("records")
    for r in records:
        for k, v in r.items():
            if pd.isna(v):
                r[k] = None
            elif hasattr(v, "isoformat"):
                r[k] = v.isoformat()
    return records


# --- Routes ---

@app.get("/api/health")
async def health():
    return {"status": "ok", "deals": len(SCORED_CACHE)}


@app.get("/api/init")
async def init_data(profile: dict = Depends(get_current_user)):
    """Single endpoint that returns ALL data needed by the frontend."""
    teams = DATA_CACHE["teams"]
    pipeline = filter_pipeline_by_role(DATA_CACHE["pipeline"], profile, teams)
    scored = filter_by_role(SCORED_CACHE, profile, teams)
    metrics = get_pipeline_metrics(pipeline, scored)

    deal_cols = ["id", "opportunity_id", "deal_stage", "score", "product_name",
                 "account_name", "agent_name", "manager_name", "regional_office",
                 "potential_value", "engage_date",
                 "_f_pipeline_aging", "_f_win_rate_combined", "_f_win_rate_account",
                 "_f_potential_value", "_f_account_fit", "_f_agent_performance",
                 "_f_agent_load", "_f_repeat_customer"]

    history_cols = ["id", "opportunity_id", "deal_stage", "product_name", "account_name",
                    "agent_name", "close_value", "close_date", "engage_date"]

    history = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])].copy()
    product_map = DATA_CACHE["products"].set_index("id")["name"].to_dict()
    account_map = DATA_CACHE["accounts"].set_index("id")["name"].to_dict()
    agent_map = teams.set_index("id")["sales_agent"].to_dict()
    history["product_name"] = history["product_id"].map(product_map)
    history["account_name"] = history["account_id"].map(account_map)
    history["agent_name"] = history["sales_agent_id"].map(agent_map)
    history = history.sort_values("close_date", ascending=False)

    # Filters
    filters = {
        "stages": sorted(scored["deal_stage"].unique().tolist()) if not scored.empty else [],
        "products": sorted(scored["product_name"].dropna().unique().tolist()) if not scored.empty else [],
        "agents": sorted(scored["agent_name"].dropna().unique().tolist()) if not scored.empty else [],
        "offices": sorted(scored["regional_office"].dropna().unique().tolist()) if not scored.empty else [],
    }

    # Team ranking
    ranking = []
    closed = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])]
    for _, agent in teams.iterrows():
        agent_closed = closed[closed["sales_agent_id"] == agent["id"]]
        agent_active = scored[scored["sales_agent_id"] == agent["id"]]
        won = len(agent_closed[agent_closed["deal_stage"] == "Won"])
        total = len(agent_closed)
        wr = (won / total * 100) if total > 0 else 0
        ranking.append({
            "agent": agent["sales_agent"], "office": agent["regional_office"],
            "win_rate": round(wr, 1), "active_deals": len(agent_active),
            "avg_score": round(float(agent_active["score"].mean()), 1) if len(agent_active) > 0 else 0,
            "potential": float(agent_active["potential_value"].sum()) if len(agent_active) > 0 else 0,
        })
    ranking.sort(key=lambda x: x["avg_score"], reverse=True)

    # Pipeline health score (0-100)
    hot = scored[scored["score"] >= 55]
    warm = scored[(scored["score"] >= 40) & (scored["score"] < 55)]
    cold = scored[scored["score"] < 40]

    health_factors = []
    # 1. Pipeline volume (enough deals?)
    volume_score = min(1, len(scored) / 50) if len(scored) > 0 else 0
    health_factors.append(("volume", volume_score, 0.15))
    # 2. Quality mix (% hot + warm)
    quality = (len(hot) + len(warm)) / len(scored) if len(scored) > 0 else 0
    health_factors.append(("quality", quality, 0.25))
    # 3. Win rate vs benchmark (63% global)
    wr_score = min(1, metrics["win_rate"] / 70) if metrics["win_rate"] > 0 else 0
    health_factors.append(("win_rate", wr_score, 0.25))
    # 4. Average score
    avg_score_norm = scored["score"].mean() / 100 if len(scored) > 0 else 0
    health_factors.append(("avg_score", avg_score_norm, 0.20))
    # 5. Low risk ratio (few cold deals)
    low_risk = 1 - (len(cold) / len(scored)) if len(scored) > 0 else 0
    health_factors.append(("low_risk", low_risk, 0.15))

    health_score = round(sum(v * w for _, v, w in health_factors) * 100, 1)
    health_details = {name: round(val * 100, 1) for name, val, _ in health_factors}

    return {
        "metrics": metrics,
        "deals": _serialize_df(scored, deal_cols),
        "history": _serialize_df(history.head(500), history_cols),
        "filters": filters,
        "ranking": ranking,
        "profile": profile,
        "health": {"score": health_score, "details": health_details},
    }


@app.get("/api/deals")
async def get_deals(
    page: int = 1,
    per_page: int = 20,
    stage: str = None,
    product: str = None,
    agent: str = None,
    min_score: float = 0,
    max_score: float = 100,
    sort_by: str = "score",
    sort_order: str = "desc",
    profile: dict = Depends(get_current_user),
):
    teams = DATA_CACHE["teams"]
    filtered = filter_by_role(SCORED_CACHE, profile, teams)

    if stage:
        stages = stage.split(",")
        filtered = filtered[filtered["deal_stage"].isin(stages)]
    if product:
        products = product.split(",")
        filtered = filtered[filtered["product_name"].isin(products)]
    if agent:
        agents = agent.split(",")
        filtered = filtered[filtered["agent_name"].isin(agents)]

    filtered = filtered[(filtered["score"] >= min_score) & (filtered["score"] <= max_score)]

    ascending = sort_order == "asc"
    if sort_by in filtered.columns:
        filtered = filtered.sort_values(sort_by, ascending=ascending)

    total = len(filtered)
    start = (page - 1) * per_page
    page_data = filtered.iloc[start:start + per_page]

    cols = ["id", "opportunity_id", "deal_stage", "score", "product_name",
            "account_name", "agent_name", "manager_name", "regional_office",
            "potential_value", "engage_date",
            "_f_pipeline_aging", "_f_win_rate_combined", "_f_win_rate_account",
            "_f_potential_value", "_f_account_fit", "_f_agent_performance",
            "_f_agent_load", "_f_repeat_customer"]
    available = [c for c in cols if c in page_data.columns]

    records = page_data[available].to_dict("records")
    for r in records:
        for k, v in r.items():
            if pd.isna(v):
                r[k] = None
            elif hasattr(v, "isoformat"):
                r[k] = v.isoformat()

    return {
        "deals": records,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total - 1) // per_page + 1),
    }


@app.get("/api/deals/{deal_id}/explain")
async def explain_deal_endpoint(deal_id: int, profile: dict = Depends(get_current_user)):
    teams = DATA_CACHE["teams"]
    filtered = filter_by_role(SCORED_CACHE, profile, teams)
    deal_row = filtered[filtered["id"] == deal_id]

    if deal_row.empty:
        raise HTTPException(status_code=404, detail="Deal não encontrado")

    deal = deal_row.iloc[0]
    explanations = get_deal_explanations(
        deal, STATS_CACHE,
        DATA_CACHE["products"], DATA_CACHE["accounts"], DATA_CACHE["teams"]
    )
    return {"explanations": explanations}


@app.get("/api/metrics")
async def get_metrics(profile: dict = Depends(get_current_user)):
    teams = DATA_CACHE["teams"]
    pipeline = filter_pipeline_by_role(DATA_CACHE["pipeline"], profile, teams)
    scored = filter_by_role(SCORED_CACHE, profile, teams)
    metrics = get_pipeline_metrics(pipeline, scored)
    return metrics


@app.get("/api/history")
async def get_history(
    page: int = 1,
    per_page: int = 50,
    stage: str = None,
    profile: dict = Depends(get_current_user),
):
    teams = DATA_CACHE["teams"]
    pipeline = filter_pipeline_by_role(DATA_CACHE["pipeline"], profile, teams)
    history = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])].copy()

    if stage:
        history = history[history["deal_stage"].isin(stage.split(","))]

    history = history.sort_values("close_date", ascending=False)

    product_map = DATA_CACHE["products"].set_index("id")["name"].to_dict()
    account_map = DATA_CACHE["accounts"].set_index("id")["name"].to_dict()
    agent_map = teams.set_index("id")["sales_agent"].to_dict()

    history["product_name"] = history["product_id"].map(product_map)
    history["account_name"] = history["account_id"].map(account_map)
    history["agent_name"] = history["sales_agent_id"].map(agent_map)

    total = len(history)
    start = (page - 1) * per_page
    page_data = history.iloc[start:start + per_page]

    cols = ["id", "opportunity_id", "deal_stage", "product_name", "account_name",
            "agent_name", "close_value", "close_date", "engage_date"]
    records = page_data[cols].to_dict("records")
    for r in records:
        for k, v in r.items():
            if pd.isna(v):
                r[k] = None
            elif hasattr(v, "isoformat"):
                r[k] = v.isoformat()

    return {"deals": records, "total": total, "page": page, "per_page": per_page}


@app.get("/api/team-ranking")
async def get_team_ranking(profile: dict = Depends(get_current_user)):
    if profile["role"] == "vendedor":
        raise HTTPException(status_code=403, detail="Acesso restrito a managers e admins")

    teams = DATA_CACHE["teams"]
    pipeline = filter_pipeline_by_role(DATA_CACHE["pipeline"], profile, teams)
    scored = filter_by_role(SCORED_CACHE, profile, teams)
    closed = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])]

    ranking = []
    for _, agent in teams.iterrows():
        agent_closed = closed[closed["sales_agent_id"] == agent["id"]]
        agent_active = scored[scored["sales_agent_id"] == agent["id"]]
        won = len(agent_closed[agent_closed["deal_stage"] == "Won"])
        total = len(agent_closed)
        wr = (won / total * 100) if total > 0 else 0

        ranking.append({
            "agent": agent["sales_agent"],
            "office": agent["regional_office"],
            "win_rate": round(wr, 1),
            "active_deals": len(agent_active),
            "avg_score": round(float(agent_active["score"].mean()), 1) if len(agent_active) > 0 else 0,
            "potential": float(agent_active["potential_value"].sum()) if len(agent_active) > 0 else 0,
        })

    ranking.sort(key=lambda x: x["avg_score"], reverse=True)
    return {"ranking": ranking}


@app.get("/api/filters")
async def get_filter_options(profile: dict = Depends(get_current_user)):
    teams = DATA_CACHE["teams"]
    scored = filter_by_role(SCORED_CACHE, profile, teams)

    return {
        "stages": sorted(scored["deal_stage"].unique().tolist()),
        "products": sorted(scored["product_name"].dropna().unique().tolist()),
        "agents": sorted(scored["agent_name"].dropna().unique().tolist()),
        "offices": sorted(scored["regional_office"].dropna().unique().tolist()),
    }


class ChatRequest(BaseModel):
    messages: list[dict]


class CreateDealRequest(BaseModel):
    sales_agent_id: int
    product_id: int
    account_id: int
    deal_stage: str = "Prospecting"
    engage_date: str | None = None


class ClassifyDealRequest(BaseModel):
    deal_stage: str  # "Won" or "Lost"
    close_value: float = 0


@app.post("/api/deals")
async def create_deal(req: CreateDealRequest, profile: dict = Depends(get_current_user)):
    """Create a new deal in the pipeline."""
    import uuid

    if req.deal_stage not in ("Prospecting", "Engaging"):
        raise HTTPException(status_code=400, detail="Novo deal deve ser Prospecting ou Engaging")

    sb = get_supabase_admin()
    opportunity_id = uuid.uuid4().hex[:8].upper()

    data = {
        "opportunity_id": opportunity_id,
        "sales_agent_id": req.sales_agent_id,
        "product_id": req.product_id,
        "account_id": req.account_id,
        "deal_stage": req.deal_stage,
        "engage_date": req.engage_date if req.deal_stage == "Engaging" else None,
        "close_date": None,
        "close_value": 0,
    }

    result = sb.table("sales_pipeline").insert(data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar deal")

    # Reload data to include new deal
    load_all_data()

    return {"id": result.data[0]["id"], "opportunity_id": opportunity_id}


@app.patch("/api/deals/{deal_id}/classify")
async def classify_deal(deal_id: int, req: ClassifyDealRequest, profile: dict = Depends(get_current_user)):
    """Classify a deal as Won or Lost."""
    if req.deal_stage not in ("Won", "Lost"):
        raise HTTPException(status_code=400, detail="Classificação deve ser Won ou Lost")

    sb = get_supabase_admin()

    from datetime import date
    close_date = str(REFERENCE_DATE.date()) if REFERENCE_DATE else str(date.today())

    # Fetch current deal to check engage_date
    current = sb.table("sales_pipeline").select("engage_date").eq("id", deal_id).execute()
    if not current.data:
        raise HTTPException(status_code=404, detail="Deal nao encontrado")

    update_data = {
        "deal_stage": req.deal_stage,
        "close_date": close_date,
        "close_value": req.close_value if req.deal_stage == "Won" else 0,
    }

    # Won/Lost require engage_date — set it if missing (Prospecting deals)
    if not current.data[0].get("engage_date"):
        update_data["engage_date"] = close_date

    result = sb.table("sales_pipeline").update(update_data).eq("id", deal_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Deal não encontrado")

    # Reload data
    load_all_data()

    return {"status": "ok", "deal_id": deal_id, "new_stage": req.deal_stage}


@app.get("/api/options")
async def get_options(profile: dict = Depends(get_current_user)):
    """Get dropdown options for deal creation form."""
    teams = DATA_CACHE["teams"]
    products = DATA_CACHE["products"]
    accounts = DATA_CACHE["accounts"]

    return {
        "agents": [{"id": int(r["id"]), "name": r["sales_agent"]} for _, r in teams.iterrows()],
        "products": [{"id": int(r["id"]), "name": r["name"], "price": float(r["sales_price"])} for _, r in products.iterrows()],
        "accounts": [{"id": int(r["id"]), "name": r["name"]} for _, r in accounts.iterrows()],
    }


# Import REFERENCE_DATE for classify endpoint
from scoring.features import REFERENCE_DATE


def _build_chat_context(profile: dict) -> str:
    """Build full data context for AI chat."""
    teams = DATA_CACHE["teams"]
    pipeline = filter_pipeline_by_role(DATA_CACHE["pipeline"], profile, teams)
    scored = filter_by_role(SCORED_CACHE, profile, teams)
    metrics = get_pipeline_metrics(pipeline, scored)

    # Zonas de prioridade
    hot = scored[scored["score"] >= 55]
    warm = scored[(scored["score"] >= 40) & (scored["score"] < 55)]
    cold = scored[scored["score"] < 40]

    # Top 10 deals detalhados
    top10_lines = []
    for _, d in scored.head(10).iterrows():
        top10_lines.append(
            f"  - {d.get('account_name','?')} | {d.get('product_name','?')} | "
            f"Score: {d['score']} | Stage: {d['deal_stage']} | "
            f"Vendedor: {d.get('agent_name','?')} | "
            f"Valor potencial: R${d.get('potential_value',0):,.0f}"
        )

    # Deals em risco (score < 40, top 10)
    risk_lines = []
    for _, d in cold.head(10).iterrows():
        risk_lines.append(
            f"  - {d.get('account_name','?')} | {d.get('product_name','?')} | "
            f"Score: {d['score']} | Vendedor: {d.get('agent_name','?')}"
        )

    # Distribuição por produto
    product_dist = scored.groupby("product_name").agg(
        deals=("score", "count"),
        avg_score=("score", "mean"),
        total_value=("potential_value", "sum"),
    ).sort_values("total_value", ascending=False)
    prod_lines = []
    for name, row in product_dist.iterrows():
        prod_lines.append(f"  - {name}: {int(row['deals'])} deals, score médio {row['avg_score']:.1f}, potencial R${row['total_value']:,.0f}")

    # Distribuição por conta (top 10)
    acct_dist = scored.groupby("account_name").agg(
        deals=("score", "count"),
        avg_score=("score", "mean"),
        total_value=("potential_value", "sum"),
    ).sort_values("total_value", ascending=False).head(10)
    acct_lines = []
    for name, row in acct_dist.iterrows():
        acct_lines.append(f"  - {name}: {int(row['deals'])} deals, score médio {row['avg_score']:.1f}, potencial R${row['total_value']:,.0f}")

    # Distribuição por vendedor
    agent_dist = scored.groupby("agent_name").agg(
        deals=("score", "count"),
        avg_score=("score", "mean"),
        total_value=("potential_value", "sum"),
    ).sort_values("avg_score", ascending=False)
    agent_lines = []
    for name, row in agent_dist.iterrows():
        agent_lines.append(f"  - {name}: {int(row['deals'])} deals, score médio {row['avg_score']:.1f}, potencial R${row['total_value']:,.0f}")

    # Histórico resumo
    hist = pipeline[pipeline["deal_stage"].isin(["Won", "Lost"])]
    won = hist[hist["deal_stage"] == "Won"]
    lost = hist[hist["deal_stage"] == "Lost"]

    context = f"""=== MÉTRICAS GERAIS ===
- Deals ativos (Engaging + Prospecting): {len(scored)}
- Win rate histórico: {metrics['win_rate']}%
- Ticket médio (Won): R${metrics['avg_ticket']:,.0f}
- Potencial total em pipeline: R${metrics['total_potential']:,.0f}
- Receita total Won: R${metrics['total_won_value']:,.0f}

=== ZONAS DE PRIORIDADE ===
- Alta prioridade (score >= 55): {len(hot)} deals, potencial R${hot['potential_value'].sum():,.0f}
- Atenção (score 40-54): {len(warm)} deals, potencial R${warm['potential_value'].sum():,.0f}
- Baixa prioridade (score < 40): {len(cold)} deals, potencial R${cold['potential_value'].sum():,.0f}

=== TOP 10 DEALS (por score) ===
{chr(10).join(top10_lines)}

=== DEALS EM RISCO (score mais baixo) ===
{chr(10).join(risk_lines[:10])}

=== PIPELINE POR PRODUTO ===
{chr(10).join(prod_lines)}

=== TOP 10 CONTAS POR POTENCIAL ===
{chr(10).join(acct_lines)}

=== PIPELINE POR VENDEDOR ===
{chr(10).join(agent_lines)}

=== HISTÓRICO ===
- Total Won: {len(won)} deals (R${won['close_value'].sum():,.0f})
- Total Lost: {len(lost)} deals
- Deals por stage: Engaging={len(pipeline[pipeline['deal_stage']=='Engaging'])}, Prospecting={len(pipeline[pipeline['deal_stage']=='Prospecting'])}, Won={len(won)}, Lost={len(lost)}

=== CRITÉRIOS DE SCORE (v4) ===
O score (0-100) é composto por 8 fatores ponderados:
- pipeline_aging (22%): quanto mais recente a oportunidade em Negociação, maior. Usa sigmoid decay com mediana/IQR dos deals ativos. Prospecção = 0.30 (abaixo do neutro, pois é etapa mais fria).
- potential_value (18%): valor do produto em escala logarítmica × contexto da conta (70% preço + 30% preço × porte da conta). Contas maiores amplificam o valor potencial.
- win_rate_combined (15%): média da taxa de conversão do setor + produto, com desvio amplificado em relação à média global (63.2%).
- account_fit (12%): porte da empresa (receita + funcionários) em escala log. Oportunidades sem conta definida recebem valor abaixo da mediana.
- repeat_customer (10%): histórico de compras da conta em escala log. Contas que já compraram mais vezes pontuam mais.
- agent_load (10%): carga do vendedor vs média do time. Ambos os extremos (sobrecarregado ou ocioso) reduzem o score. Ótimo = perto da média.
- win_rate_account (8%): taxa de conversão da conta específica, ponderada por confiança (contas com poucos deals ficam neutras).
- agent_performance (5%): win rate do vendedor vs média global, simétrico e com peso reduzido para evitar feedback loop.

Zonas de prioridade:
- Alta Prioridade: score >= 55
- Atenção: score 40-54
- Baixa Prioridade: score < 40

Todos os valores monetários são em R$ (reais brasileiros).
"""
    return context


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest, profile: dict = Depends(get_current_user)):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="OpenAI API key não configurada")

    context = _build_chat_context(profile)

    from openai import OpenAI
    from ai.prompts import SYSTEM_PROMPT_CHAT

    client = OpenAI(api_key=api_key)
    system = SYSTEM_PROMPT_CHAT + f"\n\n{context}"

    api_messages = [{"role": "system", "content": system}]
    for msg in req.messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=api_messages,
        temperature=0.7,
        max_tokens=1200,
    )

    return {"response": response.choices[0].message.content}


@app.post("/api/deals/{deal_id}/ai-analysis")
async def ai_analysis(deal_id: int, profile: dict = Depends(get_current_user)):
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=503, detail="OpenAI API key não configurada")

    teams = DATA_CACHE["teams"]
    filtered = filter_by_role(SCORED_CACHE, profile, teams)
    deal_row = filtered[filtered["id"] == deal_id]

    if deal_row.empty:
        raise HTTPException(status_code=404, detail="Deal não encontrado")

    deal = deal_row.iloc[0]
    explanations = get_deal_explanations(
        deal, STATS_CACHE,
        DATA_CACHE["products"], DATA_CACHE["accounts"], DATA_CACHE["teams"]
    )

    from openai import OpenAI
    from ai.prompts import SYSTEM_PROMPT_EXPLAINER, EXPLAIN_TEMPLATE

    client = OpenAI(api_key=api_key)
    deal_info = f"{deal['account_name']} - {deal['product_name']} ({deal['deal_stage']})"
    factors = "\n".join([f"- {e['text']}" for e in explanations])
    prompt = EXPLAIN_TEMPLATE.format(deal_info=deal_info, score=deal["score"], factors=factors)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_EXPLAINER},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
        max_tokens=500,
    )

    return {"analysis": response.choices[0].message.content}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
