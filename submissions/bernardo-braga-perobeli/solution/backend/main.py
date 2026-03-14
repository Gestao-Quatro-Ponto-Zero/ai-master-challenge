"""
G4 IA - Inteligência de Suporte — Backend FastAPI

API REST para triagem inteligente de tickets com classificação via Transformers,
sistema de 3 níveis, autenticação JWT e interfaces por perfil.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI, HTTPException, Query, Depends, Header, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import io

from schemas import (
    LoginRequest, LoginResponse,
    ClassificarRequest, ClassificarResponse,
    TriagemRequest, TriagemResponse,
    SugerirRespostaRequest, SugerirRespostaResponse, TicketSimilar,
    AtualizarStatusTicketRequest, DetalheTicket,
    StatusAgenteRequest, InfoAgente,
    InfoAlerta, MetricasResponse, TopMotivosResponse,
    StatusTicket, NivelSeveridade, StatusAgente,
    CriarUsuarioRequest, AtualizarUsuarioRequest, UsuarioResponse,
    OnboardingResponse, WebhookTicketRequest,
)
from classifier import get_classifier
from triage import processar_triagem
from auth import authenticate_user, create_token, verify_token, ContaDesativadaError
from database import db
from config import (
    ALERT_THRESHOLDS, PROJECT_NAME, PROJECT_VERSION, LABEL_MAP_EN_TO_PT,
    USERS, _hash_pw,
)

app = FastAPI(
    title=PROJECT_NAME,
    description="API de triagem inteligente com classificação via Transformers e sistema de 3 níveis de severidade",
    version=PROJECT_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Inicialização ---

@app.on_event("startup")
async def startup():
    import logging
    import threading
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    from rag import rag_store
    from llm import llm_disponivel

    if llm_disponivel():
        logger.info("Gemini API detectada — RAG será inicializado em background...")

        def _init_rag():
            rag_store.inicializar()
            logger.info("RAG finalizado: %d documentos, pronto=%s", rag_store.size, rag_store.ready)

        threading.Thread(target=_init_rag, daemon=True).start()
    else:
        logger.warning("GOOGLE_API_KEY não encontrada — modo fallback (DeBERTa + templates)")
        get_classifier()

    logger.info(f"{PROJECT_NAME} v{PROJECT_VERSION} — Backend pronto (LLM ativo, RAG carregando em background).")


# --- Autenticação ---

@app.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    try:
        user = authenticate_user(req.email, req.senha)
    except ContaDesativadaError:
        raise HTTPException(status_code=403, detail="Conta desativada. Contate o gestor.")
    if not user:
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    token = create_token(user)
    return LoginResponse(token=token, nome=user["nome"], email=user["email"], perfil=user["perfil"])


# --- Classificação e Triagem ---

@app.post("/classificar", response_model=ClassificarResponse)
async def classificar_ticket(req: ClassificarRequest, user: dict = Depends(verify_token)):
    classificador = get_classifier()
    resultado = classificador.classify(req.texto)
    categoria_pt = LABEL_MAP_EN_TO_PT.get(resultado["category"], resultado["category"])
    scores_pt = {LABEL_MAP_EN_TO_PT.get(k, k): v for k, v in resultado["all_scores"].items()}
    return ClassificarResponse(categoria=categoria_pt, confianca=resultado["confidence"], todas_pontuacoes=scores_pt)


@app.post("/triagem", response_model=TriagemResponse)
async def triar_ticket(req: TriagemRequest, user: dict = Depends(verify_token)):
    return processar_triagem(req.texto, req.nome_cliente, req.canal)


@app.post("/sugerir-resposta", response_model=SugerirRespostaResponse)
async def sugerir_resposta(req: SugerirRespostaRequest, user: dict = Depends(verify_token)):
    classificador = get_classifier()
    similares = classificador.find_similar_tickets(req.texto, req.quantidade)
    return SugerirRespostaResponse(
        consulta=req.texto,
        tickets_similares=[TicketSimilar(
            texto=s["text"], resolucao=s["resolution"], pontuacao_similaridade=s["similarity_score"]
        ) for s in similares],
    )


# --- Gestão de Tickets ---

@app.get("/tickets", response_model=list[DetalheTicket])
async def listar_tickets(
    status: StatusTicket | None = None,
    severidade: NivelSeveridade | None = None,
    nome_agente: str | None = None,
    limite: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(verify_token),
):
    return db.listar_tickets(status=status, severidade=severidade, nome_agente=nome_agente, limite=limite, offset=offset)


@app.get("/tickets/{ticket_id}", response_model=DetalheTicket)
async def obter_ticket(ticket_id: str, user: dict = Depends(verify_token)):
    ticket = db.obter_ticket(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    return ticket


@app.patch("/tickets/{ticket_id}/status", response_model=DetalheTicket)
async def atualizar_status_ticket(ticket_id: str, req: AtualizarStatusTicketRequest, user: dict = Depends(verify_token)):
    ticket = db.atualizar_status_ticket(ticket_id, req.status, req.nome_agente)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket não encontrado")
    return ticket


# --- Agentes ---

@app.post("/agentes/status", response_model=InfoAgente)
async def definir_status_agente(req: StatusAgenteRequest, user: dict = Depends(verify_token)):
    return db.definir_status_agente(req.nome, req.status)


@app.get("/agentes/online", response_model=list[InfoAgente])
async def obter_agentes_online(user: dict = Depends(verify_token)):
    return db.obter_agentes_online()


# --- Métricas e Alertas ---

@app.get("/metricas", response_model=MetricasResponse)
async def obter_metricas(
    periodo: str = Query("dia", pattern="^(dia|semana|mes)$"),
    user: dict = Depends(verify_token),
):
    m = db.obter_metricas(periodo)
    return MetricasResponse(
        periodo=m["periodo"],
        total_tickets=m["total_tickets"],
        por_severidade=m["por_severidade"],
        por_status=m["por_status"],
        tempo_medio_resolucao_horas=m["tempo_medio_resolucao_horas"],
        auto_resolvidos=m["auto_resolvidos"],
        pct_auto_resolvidos=m["pct_auto_resolvidos"],
    )


@app.get("/metricas/top-motivos", response_model=TopMotivosResponse)
async def obter_top_motivos(
    periodo: str = Query("dia", pattern="^(dia|semana|mes)$"),
    severidade: str = Query("todos", pattern="^(todos|baixo|medio|critico)$"),
    user: dict = Depends(verify_token),
):
    motivos = db.obter_top_motivos(periodo, severidade)
    return TopMotivosResponse(periodo=periodo, filtro_severidade=severidade, motivos=motivos)


@app.get("/alertas", response_model=list[InfoAlerta])
async def obter_alertas(apenas_ativos: bool = False, user: dict = Depends(verify_token)):
    return db.obter_alertas(apenas_ativos)


# --- Diagnóstico Operacional ---

@app.get("/diagnostico")
async def diagnostico_operacional(user: dict = Depends(verify_token)):
    from analise import carregar_diagnostico
    return carregar_diagnostico()


# --- CRUD de Usuários ---

PERFIS_ADMIN = ("gestor", "diretor")
PERFIS_VALIDOS = ("agente", "gestor", "diretor")


@app.get("/usuarios", response_model=list[UsuarioResponse])
async def listar_usuarios(user: dict = Depends(verify_token)):
    if user.get("perfil") not in PERFIS_ADMIN:
        raise HTTPException(status_code=403, detail="Acesso restrito a gestores e diretores")
    return [
        UsuarioResponse(email=email, nome=u["nome"], perfil=u["perfil"], ativo=u.get("ativo", True))
        for email, u in USERS.items()
    ]


@app.post("/usuarios", response_model=UsuarioResponse, status_code=201)
async def criar_usuario(req: CriarUsuarioRequest, user: dict = Depends(verify_token)):
    if user.get("perfil") not in PERFIS_ADMIN:
        raise HTTPException(status_code=403, detail="Acesso restrito a gestores e diretores")
    if req.email in USERS:
        raise HTTPException(status_code=409, detail="Email já cadastrado")
    if req.perfil not in PERFIS_VALIDOS:
        raise HTTPException(status_code=400, detail="Perfil deve ser 'agente', 'gestor' ou 'diretor'")

    USERS[req.email] = {
        "nome": req.nome,
        "senha_hash": _hash_pw(req.senha),
        "perfil": req.perfil,
        "ativo": True,
    }
    return UsuarioResponse(email=req.email, nome=req.nome, perfil=req.perfil, ativo=True)


@app.put("/usuarios/{email}", response_model=UsuarioResponse)
async def atualizar_usuario(email: str, req: AtualizarUsuarioRequest, user: dict = Depends(verify_token)):
    if user.get("perfil") not in PERFIS_ADMIN:
        raise HTTPException(status_code=403, detail="Acesso restrito a gestores e diretores")
    if email not in USERS:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    u = USERS[email]
    if req.nome is not None:
        u["nome"] = req.nome
    if req.perfil is not None and req.perfil in PERFIS_VALIDOS:
        u["perfil"] = req.perfil
    if req.ativo is not None:
        u["ativo"] = req.ativo
    return UsuarioResponse(email=email, nome=u["nome"], perfil=u["perfil"], ativo=u.get("ativo", True))


@app.delete("/usuarios/{email}")
async def desativar_usuario(email: str, user: dict = Depends(verify_token)):
    perfil_atual = user.get("perfil")
    if perfil_atual not in PERFIS_ADMIN:
        raise HTTPException(status_code=403, detail="Acesso restrito a gestores e diretores")
    if email not in USERS:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    alvo = USERS[email]
    if perfil_atual == "gestor" and alvo["perfil"] != "agente":
        raise HTTPException(status_code=403, detail="Gestores só podem desativar contas de agentes")

    USERS[email]["ativo"] = False
    return {"mensagem": f"Usuário {email} desativado"}


# --- Onboarding (Upload de Dados) ---

@app.post("/onboarding/upload", response_model=OnboardingResponse)
async def upload_dados(file: UploadFile = File(...), user: dict = Depends(verify_token)):
    """Recebe CSV ou XLSX via form-data, gera embeddings e adiciona à base RAG."""
    if user.get("perfil") not in PERFIS_ADMIN:
        raise HTTPException(status_code=403, detail="Acesso restrito a gestores e diretores")

    from rag import rag_store

    content = await file.read()
    filename = file.filename or ""

    try:
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {e}")

    col_texto = None
    for candidate in ["texto", "text", "Document", "Ticket Description", "description", "descricao"]:
        if candidate in df.columns:
            col_texto = candidate
            break
    if col_texto is None:
        raise HTTPException(status_code=400, detail=f"Coluna de texto não encontrada. Colunas: {list(df.columns)}")

    col_resolucao = None
    for candidate in ["resolucao", "resolution", "Resolution", "resposta"]:
        if candidate in df.columns:
            col_resolucao = candidate
            break

    col_categoria = None
    for candidate in ["categoria", "category", "Topic_group", "Ticket Type", "tipo"]:
        if candidate in df.columns:
            col_categoria = candidate
            break

    novos_docs = []
    categorias = set()
    for _, row in df.iterrows():
        texto = str(row[col_texto]).strip()
        if not texto or len(texto) < 5:
            continue
        cat = str(row[col_categoria]) if col_categoria else "Diversos"
        novos_docs.append({
            "texto": texto,
            "resolucao": str(row[col_resolucao]) if col_resolucao else "",
            "categoria": cat,
            "origem": "upload",
        })
        categorias.add(cat)

    if not novos_docs:
        raise HTTPException(status_code=400, detail="Nenhum registro válido encontrado no arquivo")

    rag_store.reindexar(novos_docs)

    return OnboardingResponse(
        registros_importados=len(novos_docs),
        categorias_encontradas=sorted(categorias),
        rag_atualizado=rag_store.ready,
        mensagem=f"{len(novos_docs)} registros importados e indexados com sucesso",
    )


@app.post("/onboarding/upload-json", response_model=OnboardingResponse)
async def upload_dados_json(dados: list[dict], user: dict = Depends(verify_token)):
    """Recebe lista de documentos JSON e adiciona à base RAG."""
    if user.get("perfil") not in PERFIS_ADMIN:
        raise HTTPException(status_code=403, detail="Acesso restrito a gestores e diretores")

    from rag import rag_store

    novos_docs = []
    categorias = set()
    for item in dados:
        texto = item.get("texto", "")
        if not texto:
            continue
        novos_docs.append({
            "texto": texto,
            "resolucao": item.get("resolucao", ""),
            "categoria": item.get("categoria", "Diversos"),
            "origem": "upload",
        })
        categorias.add(item.get("categoria", "Diversos"))

    if not novos_docs:
        raise HTTPException(status_code=400, detail="Nenhum documento válido encontrado")

    rag_store.reindexar(novos_docs)

    return OnboardingResponse(
        registros_importados=len(novos_docs),
        categorias_encontradas=sorted(categorias),
        rag_atualizado=rag_store.ready,
        mensagem=f"{len(novos_docs)} registros importados e indexados com sucesso",
    )


# --- Webhook ---

WEBHOOK_API_KEYS = {"g4-webhook-key-2026"}

@app.post("/webhook/ticket", response_model=TriagemResponse)
async def webhook_ticket(req: WebhookTicketRequest, x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key obrigatória (header X-API-Key)")
    if x_api_key not in WEBHOOK_API_KEYS:
        raise HTTPException(status_code=403, detail="API key inválida")

    return processar_triagem(req.texto, req.cliente, req.canal)


# --- Sistema ---

@app.get("/health")
async def health():
    from rag import rag_store
    from llm import llm_disponivel
    return {
        "status": "ok",
        "projeto": PROJECT_NAME,
        "versao": PROJECT_VERSION,
        "motor_ia": "gemini" if llm_disponivel() else "fallback_deberta",
        "rag_ativo": rag_store.ready,
        "rag_documentos": rag_store.size,
        "tickets": len(db.tickets),
        "agentes_online": len(db.obter_agentes_online()),
        "alertas_ativos": len(db.obter_alertas(apenas_ativos=True)),
    }
