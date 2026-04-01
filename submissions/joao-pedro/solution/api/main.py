"""
Deal Prioritization API — FastAPI entry point
Run: uvicorn api.main:app --reload  (from deal-prioritization/)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import get_benchmarks, get_pipeline_df
from api.routers import deals, sellers, managers, products, accounts, analysis

app = FastAPI(
    title="Deal Prioritization API",
    version="1.0.0",
    description="API REST para o motor de priorização de deals. Expõe scoring, viabilidade e recomendações de ação.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def warm_cache() -> None:
    """Pré-aquece o cache de benchmarks e pipeline na inicialização."""
    get_benchmarks()
    get_pipeline_df()


app.include_router(deals.router,    prefix="/deals",    tags=["Deals"])
app.include_router(sellers.router,  prefix="/sellers",  tags=["Sellers"])
app.include_router(managers.router, prefix="/managers", tags=["Managers"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
app.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])


@app.get("/benchmarks", tags=["Meta"])
def get_benchmarks_endpoint() -> dict:
    """Retorna os benchmarks calculados (win rates globais, medianas de tempo, etc.)."""
    b = get_benchmarks()
    return {
        "global_wr": b["global_wr"],
        "won_median_days": b["won_median"],
        "lost_median_days": b["lost_median"],
        "engaging_median_days": b["engaging_median"],
        "total_deals": b["total_deals"],
        "snapshot_date": b["snapshot_date"],
        "seller_win_rates": b["seller_wr"],
        "product_win_rates": b["product_wr"],
        "region_win_rates": b["region_wr"],
        "top_20_accounts": b["top_20_accounts"],
    }


@app.get("/health", tags=["Meta"])
def health() -> dict:
    return {"status": "ok"}
