"""
Ponto de entrada da API.

Rodar (dentro da pasta backend/):
    python -m uvicorn app.main:app --reload

- Tela:                        http://localhost:8000   (se frontend/dist existir)
- Documentação interativa:     http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import config
from app.rotas import pipeline, resumo
from app.servicos.pontuacao import pontuar_deals_abertos


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    # Carrega e pontua os dados na subida do servidor,
    # para a primeira requisição não ficar lenta.
    pontuar_deals_abertos()
    yield


app = FastAPI(
    title="Priorização de Deals",
    description="Ajuda vendedores a decidir em quais negócios focar.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ORIGENS_PERMITIDAS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(pipeline.roteador)
app.include_router(resumo.roteador)


# Serve a tela compilada, se ela existir. Registrado depois das rotas da API
# para que /api/* continue respondendo normalmente.
if (config.PASTA_FRONTEND_COMPILADO / "index.html").exists():
    app.mount(
        "/assets",
        StaticFiles(directory=config.PASTA_FRONTEND_COMPILADO / "assets"),
        name="assets",
    )

    @app.get("/", include_in_schema=False)
    def tela():
        return FileResponse(config.PASTA_FRONTEND_COMPILADO / "index.html")
