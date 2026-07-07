"""
API FastAPI para Análise de Churn - Ravenstack
Endpoints para predição de churn, geração de relatórios e gerenciamento de riscos
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
import joblib
import logging
import os
import importlib.util
from datetime import datetime
import json

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar aplicação
app = FastAPI(
    title="API Análise de Churn",
    description="API para predição e análise de churn de clientes",
    version="1.0.0"
)

# CORS middleware para aceitar requisições de diferentes domínios
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Função para carregar módulos
def carregar_modulo(caminho_arquivo, nome_modulo):
    """Carrega um módulo Python a partir de um arquivo."""
    spec = importlib.util.spec_from_file_location(nome_modulo, caminho_arquivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo

# Carregar módulos de negócio
processamento = carregar_modulo('01_data_preprocessing.py', 'preprocessing')
engenharia_features = carregar_modulo('02_feature_engineering.py', 'feature_engineering')
pontuacao_risco = carregar_modulo('05_risk_scoring.py', 'risk_scoring')
modelo_churn = carregar_modulo('churn_model.py', 'churn_model')

# Classes do Pydantic para validação de dados
class ContaDados(BaseModel):
    """Modelo de dados de uma conta para predição"""
    account_id: int
    industry: str
    country: str
    plan_tier: str
    mrr_amount: float
    adoption_rate: float
    support_quality_score: float
    support_ticket_count: int
    avg_resolution_time: float
    avg_satisfaction_score: float
    days_since_signup: int
    is_trial: bool = False

class CenarioSimulacao(BaseModel):
    """Modelo para simulação de cenários (what-if)"""
    adoption_rate: Optional[float] = None
    support_quality_score: Optional[float] = None
    support_ticket_count: Optional[int] = None
    avg_resolution_time: Optional[float] = None
    avg_satisfaction_score: Optional[float] = None
    mrr_amount: Optional[float] = None
    days_since_signup: Optional[int] = None

class RespostaPrevision(BaseModel):
    """Resposta de predição de churn"""
    account_id: int
    probabilidade_churn: float
    tier_risco: str
    drivers_primarios: List[str]
    acoes_recomendadas: List[str]
    confianca_predicao: float

class RespostaSimulacao(BaseModel):
    """Resposta de simulação de cenários"""
    probabilidade_original: float
    probabilidade_simulada: float
    mudanca_percentual: float
    novo_tier_risco: str
    impacto_por_driver: Dict[str, float]

# Variáveis globais para armazenar modelos carregados
modelos_cache = {}
colunas_features = None

def carregar_modelos():
    """Carrega modelos treinados e features do cache"""
    global modelos_cache, colunas_features
    
    try:
        if 'xgb' not in modelos_cache:
            modelos_cache['xgb'] = joblib.load('models/xgb_model.pkl')
            modelos_cache['lgb'] = joblib.load('models/lgb_model.pkl')
            colunas_features = joblib.load('models/feature_columns.pkl')
            logger.info("[OK] Modelos carregados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao carregar modelos: {e}")
        raise

@app.on_event("startup")
async def inicializar_app():
    """Inicializa a aplicação ao iniciar"""
    logger.info("Iniciando API de Análise de Churn...")
    carregar_modelos()
    logger.info("API pronta para receber requisições")

@app.get("/")
async def raiz():
    """Endpoint raiz com informações da API"""
    return {
        "nome": "API Análise de Churn",
        "versao": "1.0.0",
        "status": "pronta",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/saude")
async def verificar_saude():
    """Verifica a saúde da API"""
    try:
        carregar_modelos()
        return {
            "status": "saudável",
            "modelos_carregados": True,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Serviço indisponível: {str(e)}")

@app.post("/api/v1/prever-churn")
async def prever_churn(conta: ContaDados) -> RespostaPrevision:
    """
    Prediz a probabilidade de churn para uma conta
    
    Args:
        conta: Dados da conta com features necessárias
        
    Returns:
        RespostaPrevision: Probabilidade, tier de risco e recomendações
    """
    try:
        # Preparar dados para predição
        dados_conta = {
            'adoption_rate': conta.adoption_rate,
            'support_quality_score': conta.support_quality_score,
            'support_ticket_count': conta.support_ticket_count,
            'avg_resolution_time': conta.avg_resolution_time,
            'avg_satisfaction_score': conta.avg_satisfaction_score,
            'mrr_amount': conta.mrr_amount,
            'days_since_signup': conta.days_since_signup,
            'is_trial': int(conta.is_trial)
        }
        
        # Criar dataframe com uma linha
        df = pd.DataFrame([dados_conta])
        
        # Completar com valores padrão para features não fornecidas
        for col in colunas_features:
            if col not in df.columns:
                df[col] = 0
        
        # Selecionar apenas as colunas necessárias
        df = df[colunas_features]
        
        # Fazer predições
        pred_xgb = modelos_cache['xgb'].predict_proba(df)[0][1]
        pred_lgb = modelos_cache['lgb'].predict_proba(df)[0][1]
        
        # Ensemble (60% XGBoost, 40% LightGBM)
        probabilidade_churn = pred_xgb * 0.6 + pred_lgb * 0.4
        
        # Determinar tier de risco
        if probabilidade_churn >= 0.7:
            tier_risco = "Crítico"
        elif probabilidade_churn >= 0.5:
            tier_risco = "Alto"
        elif probabilidade_churn >= 0.3:
            tier_risco = "Médio"
        else:
            tier_risco = "Baixo"
        
        # Drivers primários
        drivers = []
        if conta.adoption_rate < 30:
            drivers.append("Adoção baixa de features")
        if conta.support_quality_score < 3.0:
            drivers.append("Qualidade de suporte inadequada")
        if conta.avg_resolution_time > 40:
            drivers.append("Tempo de resolução longo")
        if conta.is_trial:
            drivers.append("Conta em período de trial")
        
        # Ações recomendadas
        acoes = []
        if tier_risco == "Crítico":
            acoes.append("URGENTE: Atribuir gerente de sucesso dedicado")
            acoes.append("URGENTE: Oferecer desconto de retenção (15-25%)")
        elif tier_risco == "Alto":
            acoes.append("Agendar call com cliente sobre roadmap")
            acoes.append("Enviar campanhas de feature adoption")
        elif tier_risco == "Médio":
            acoes.append("Educação proativa sobre features")
        
        # Confiança da predição
        confianca = 0.9 if tier_risco in ["Crítico", "Baixo"] else 0.7
        
        return RespostaPrevision(
            account_id=conta.account_id,
            probabilidade_churn=round(probabilidade_churn, 4),
            tier_risco=tier_risco,
            drivers_primarios=drivers,
            acoes_recomendadas=acoes,
            confianca_predicao=round(confianca, 2)
        )
        
    except Exception as e:
        logger.error(f"Erro na predição de churn: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na predição: {str(e)}")

@app.post("/api/v1/simular-cenario")
async def simular_cenario(conta_base: ContaDados, cenario: CenarioSimulacao) -> RespostaSimulacao:
    """
    Simula um cenário (what-if) modificando features da conta
    
    Args:
        conta_base: Dados da conta original
        cenario: Features a serem modificadas
        
    Returns:
        RespostaSimulacao: Comparação entre original e simulado
    """
    try:
        # Predição original
        pred_orig = await prever_churn(conta_base)
        prob_original = pred_orig.probabilidade_churn
        
        # Aplicar modificações para simular cenário
        conta_simulada = conta_base.copy(deep=True)
        if cenario.adoption_rate is not None:
            conta_simulada.adoption_rate = cenario.adoption_rate
        if cenario.support_quality_score is not None:
            conta_simulada.support_quality_score = cenario.support_quality_score
        if cenario.support_ticket_count is not None:
            conta_simulada.support_ticket_count = cenario.support_ticket_count
        if cenario.avg_resolution_time is not None:
            conta_simulada.avg_resolution_time = cenario.avg_resolution_time
        if cenario.avg_satisfaction_score is not None:
            conta_simulada.avg_satisfaction_score = cenario.avg_satisfaction_score
        if cenario.mrr_amount is not None:
            conta_simulada.mrr_amount = cenario.mrr_amount
        if cenario.days_since_signup is not None:
            conta_simulada.days_since_signup = cenario.days_since_signup
        
        # Predição simulada
        pred_sim = await prever_churn(conta_simulada)
        prob_simulada = pred_sim.probabilidade_churn
        
        # Calcular impacto
        mudanca_percentual = ((prob_simulada - prob_original) / max(prob_original, 0.01)) * 100
        
        # Impacto por driver
        impacto_drivers = {}
        if cenario.adoption_rate is not None:
            impacto_drivers["Adoção"] = round((cenario.adoption_rate - conta_base.adoption_rate) / 100 * 100, 2)
        if cenario.support_quality_score is not None:
            impacto_drivers["Qualidade Suporte"] = round((cenario.support_quality_score - conta_base.support_quality_score) * 10, 2)
        
        return RespostaSimulacao(
            probabilidade_original=round(prob_original, 4),
            probabilidade_simulada=round(prob_simulada, 4),
            mudanca_percentual=round(mudanca_percentual, 2),
            novo_tier_risco=pred_sim.tier_risco,
            impacto_por_driver=impacto_drivers
        )
        
    except Exception as e:
        logger.error(f"Erro na simulação: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na simulação: {str(e)}")

@app.get("/api/v1/registros-risco")
async def obter_registros_risco(
    tier_risco: Optional[str] = None,
    limite: int = 100
):
    """
    Obtém registros de risco do arquivo gerado
    
    Args:
        tier_risco: Filtrar por tier ('Crítico', 'Alto', 'Médio', 'Baixo')
        limite: Número máximo de resultados
        
    Returns:
        Lista de contas com risco
    """
    try:
        df = pd.read_csv('outputs/risk_register.csv')
        
        if tier_risco:
            df = df[df['risk_tier'] == tier_risco]
        
        df = df.head(limite)
        
        return {
            "total": len(df),
            "contas": df.to_dict(orient='records')
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter registros de risco: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter registros: {str(e)}")

@app.get("/api/v1/estatisticas")
async def obter_estatisticas():
    """Obtém estatísticas gerais do modelo e dados"""
    try:
        df = pd.read_csv('outputs/risk_register.csv')
        
        stats = {
            "total_contas": len(df),
            "risco_critico": len(df[df['risk_tier'] == 'Critical']),
            "risco_alto": len(df[df['risk_tier'] == 'High']),
            "risco_medio": len(df[df['risk_tier'] == 'Medium']),
            "risco_baixo": len(df[df['risk_tier'] == 'Low']),
            "probabilidade_churn_media": float(df['churn_probability'].mean()),
            "arr_total": float(df['arr_amount'].sum()),
            "arr_em_risco_critico": float(df[df['risk_tier'] == 'Critical']['arr_amount'].sum()),
            "arr_em_risco_alto": float(df[df['risk_tier'] == 'High']['arr_amount'].sum()),
            "timestamp": datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao obter estatísticas: {str(e)}")

@app.post("/api/v1/gerar-relatorio")
async def gerar_relatorio(industry: Optional[str] = None):
    """
    Gera relatório PDF para um setor específico ou geral
    
    Args:
        industry: Indústria específica ou None para todas
        
    Returns:
        Arquivo PDF do relatório
    """
    try:
        from generate_pdf_report import PDFReportGenerator
        
        # Carregar risk register
        df = pd.read_csv('outputs/risk_register.csv')
        
        if industry:
            df = df[df['industry'] == industry]
        
        if len(df) == 0:
            raise HTTPException(status_code=404, detail="Nenhuma conta encontrada para este filtro")
        
        # Gerar relatório
        gerador = PDFReportGenerator(df)
        caminho_pdf = gerador.generate_report()
        
        return FileResponse(
            caminho_pdf,
            media_type="application/pdf",
            filename=f"relatorio_churn_{industry or 'geral'}.pdf"
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar relatório: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório: {str(e)}")

@app.get("/docs", include_in_schema=False)
async def documentacao_swagger():
    """Documentação interativa da API (Swagger UI)"""
    return FileResponse("docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_principal:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
