"""API do Lead Scorer (FastAPI). Todo endpoint aceita `data` (YYYY-MM-DD) para ver o
pipeline como ele estava naquela data — sem ela, usa a data final do dataset. O
cálculo de cada data fica em cache no Motor; a regra de cada consulta mora em
consultas.py (compartilhada com a IA e os e-mails)."""
import logging
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from . import config, consultas, emails, ia
from .dados import carregar
from .motor import Motor, Visao
from .scoring import ORDEM_ACOES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("lead_scorer")

MOTOR = Motor(carregar(config.DATA_DIR))

app = FastAPI(title="Lead Scorer", version="0.3.0")
app.add_middleware(CORSMiddleware, allow_origins=config.ORIGENS_CORS, allow_methods=["GET", "POST"], allow_headers=["*"])


def _visao(data: Optional[str]) -> Visao:
    try:
        return MOTOR.visao(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def _rodar(funcao, *args, **kwargs):
    """Chama uma consulta convertendo filtro inválido em 400."""
    try:
        return funcao(*args, **kwargs)
    except consultas.FiltroInvalido as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Consultas ─────────────────────────────────────────────────────────────────

@app.get("/saude")
def saude():
    return {"ok": True, "data_final": MOTOR.data_final.date().isoformat(), "auc_calibracao": MOTOR.calibracao.auc,
            "ia": ia.status()}


@app.get("/datas")
def datas():
    """Datas que a interface pode simular (segundas-feiras + data final)."""
    opcoes = []
    for d in reversed(MOTOR.datas_disponiveis()):
        fim_tri = d.to_period("Q").end_time.normalize()
        opcoes.append({"data": d.date().isoformat(), "dias_para_fim_trimestre": (fim_tri - d).days,
                       "final": d == MOTOR.data_final})
    return {"padrao": (config.DATA_REFERENCIA or MOTOR.data_final.date().isoformat()), "datas": opcoes}


@app.get("/filtros")
def filtros(data: Optional[str] = None):
    v = _visao(data)
    met = v.metricas.sort_values("agente")
    return {
        "data_referencia": v.data.date().isoformat(),
        "agentes": [{"nome": r.agente, "manager": r.manager, "regiao": r.regiao, "deals_abertos": int(r.deals_abertos)}
                    for r in met.itertuples()],
        "managers": sorted(met.manager.unique()),
        "regioes": sorted(met.regiao.unique()),
        "acoes": ORDEM_ACOES,
    }


@app.get("/pipeline")
def pipeline(data: Optional[str] = None, agente: Optional[str] = None, manager: Optional[str] = None,
             regiao: Optional[str] = None, stage: Optional[str] = None, acao: Optional[str] = None,
             limite: int = Query(200, ge=1, le=5000)):
    """Deals abertos do recorte, ordenados por ação e valor esperado, + resumo por ação."""
    return _rodar(consultas.pipeline, _visao(data), limite=limite, agente=agente, manager=manager,
                  regiao=regiao, stage=stage, acao=acao)


@app.get("/deals/{opportunity_id}")
def deal(opportunity_id: str, data: Optional[str] = None):
    v = _visao(data)
    d = consultas.deal(v, opportunity_id)
    if d is None:
        raise HTTPException(status_code=404, detail=f"Deal {opportunity_id} não está aberto em {v.data.date()}.")
    return d


@app.get("/alertas")
def listar_alertas(data: Optional[str] = None, agente: Optional[str] = None, manager: Optional[str] = None,
                   regiao: Optional[str] = None, stage: Optional[str] = None, severidade: Optional[str] = None):
    """Lembretes do recorte + fila de alertas de deal, do mais grave pro mais leve."""
    return _rodar(consultas.alertas, _visao(data), severidade=severidade, agente=agente, manager=manager,
                  regiao=regiao, stage=stage)


@app.get("/emergencia")
def emergencia(data: Optional[str] = None, agente: Optional[str] = None, manager: Optional[str] = None,
               regiao: Optional[str] = None):
    """Meta x projeção do recorte e a lista de resgate."""
    return _rodar(consultas.emergencia, _visao(data), agente=agente, manager=manager, regiao=regiao)


@app.get("/time")
def time_endpoint(data: Optional[str] = None, agente: Optional[str] = None, manager: Optional[str] = None,
                  regiao: Optional[str] = None):
    """Métricas por vendedor (ritmo, cobertura, velocidade, capacidade, dado) e por manager."""
    return _rodar(consultas.time, _visao(data), agente=agente, manager=manager, regiao=regiao)


@app.get("/cross-sell")
def cross_sell(data: Optional[str] = None, agente: Optional[str] = None, manager: Optional[str] = None,
               regiao: Optional[str] = None, limite: int = Query(100, ge=1, le=1000)):
    return _rodar(consultas.cross_sell, _visao(data), limite=limite, agente=agente, manager=manager, regiao=regiao)


@app.get("/benchmarks")
def benchmarks(data: Optional[str] = None):
    """Os números do histórico que sustentam o score + a calibração (backtest)."""
    return consultas.benchmarks(_visao(data))


# ── IA ────────────────────────────────────────────────────────────────────────

class PedidoEscopo(BaseModel):
    data: Optional[str] = None
    agente: Optional[str] = None
    manager: Optional[str] = None


class PedidoData(BaseModel):
    data: Optional[str] = None


class MensagemChat(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class PedidoPergunta(BaseModel):
    data: Optional[str] = None
    pergunta: str = Field(min_length=2, max_length=1000)
    historico: list[MensagemChat] = Field(default_factory=list, max_length=20)


class PedidoRascunho(BaseModel):
    data: Optional[str] = None
    tipo: Literal["followup", "requalificacao", "encerramento"] = "followup"


@app.get("/ia/status")
def ia_status():
    return ia.status()


@app.post("/ia/briefing")
def ia_briefing(p: PedidoEscopo):
    """Briefing de segunda: do vendedor (agente), do manager (manager) ou da RevOps (nenhum)."""
    return _rodar(ia.briefing, _visao(p.data), agente=p.agente, manager=p.manager)


@app.post("/ia/deal/{opportunity_id}")
def ia_deal(opportunity_id: str, p: PedidoData):
    r = ia.explicar_deal(_visao(p.data), opportunity_id)
    if r is None:
        raise HTTPException(status_code=404, detail=f"Deal {opportunity_id} não está aberto nessa data.")
    return r


@app.post("/ia/perguntar")
def ia_perguntar(p: PedidoPergunta):
    """Chat sobre o pipeline — o LLM consulta as mesmas consultas da API como ferramentas."""
    return ia.perguntar(_visao(p.data), p.pergunta, [m.model_dump() for m in p.historico])


@app.post("/ia/plano-resgate")
def ia_plano_resgate(p: PedidoEscopo):
    return _rodar(ia.plano_resgate, _visao(p.data), agente=p.agente, manager=p.manager)


@app.post("/ia/rascunho/{opportunity_id}")
def ia_rascunho(opportunity_id: str, p: PedidoRascunho):
    r = ia.rascunho(_visao(p.data), opportunity_id, p.tipo)
    if r is None:
        raise HTTPException(status_code=404, detail=f"Deal {opportunity_id} não está aberto nessa data.")
    return r


@app.post("/ia/winloss")
def ia_winloss(p: PedidoEscopo):
    return _rodar(ia.analise_winloss, _visao(p.data), agente=p.agente, manager=p.manager)


# ── E-mails ───────────────────────────────────────────────────────────────────
# A API só LISTA e PRÉ-VISUALIZA. Enviar é decisão de quem opera: linha de comando
# (python -m app.emails --modo enviar) ou job agendado — nunca um clique na tela.

@app.get("/emails")
def emails_listar(data: Optional[str] = None):
    v = _visao(data)
    return {"modo": config.EMAIL_MODO, "redirecionar": bool(config.EMAIL_REDIRECIONAR),
            "destinatarios_reais": config.DESTINATARIOS.exists(), "ia": ia.status(), "emails": emails.listar(v)}


@app.get("/emails/preview", response_class=HTMLResponse)
def emails_preview(papel: Literal["vendedor", "manager", "revops"], nome: str, data: Optional[str] = None):
    v = _visao(data)
    item = next((e for e in emails.listar(v) if e["papel"] == papel and e["nome"] == nome), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Destinatário não encontrado para essa data.")
    email = _rodar(emails.montar, v, papel, nome, item["para"])
    if email is None:
        return HTMLResponse("<p>Sem conteúdo para este destinatário nesta data.</p>")
    return HTMLResponse(email.html)
