from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class NivelSeveridade(str, Enum):
    BAIXO = "baixo"
    MEDIO = "medio"
    CRITICO = "critico"


class StatusTicket(str, Enum):
    NOVO = "novo"
    EM_ANDAMENTO = "em_andamento"
    RESOLVIDO = "resolvido"
    ESCALADO = "escalado"


class StatusAgente(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    OCUPADO = "ocupado"


# --- Requisições ---

class LoginRequest(BaseModel):
    email: str
    senha: str


class ClassificarRequest(BaseModel):
    texto: str


class TriagemRequest(BaseModel):
    texto: str
    nome_cliente: str = "Cliente"
    canal: str = "chat"


class SugerirRespostaRequest(BaseModel):
    texto: str
    quantidade: int = 3


class AtualizarStatusTicketRequest(BaseModel):
    status: StatusTicket
    nome_agente: str | None = None


class StatusAgenteRequest(BaseModel):
    nome: str
    status: StatusAgente


# --- Respostas ---

class LoginResponse(BaseModel):
    token: str
    nome: str
    email: str
    perfil: str


class ClassificarResponse(BaseModel):
    categoria: str
    confianca: float
    todas_pontuacoes: dict[str, float]


class TriagemResponse(BaseModel):
    ticket_id: str
    categoria: str
    confianca: float
    severidade: NivelSeveridade
    acao: str
    resposta_ia: str | None = None
    resumo_ia: str | None = None
    solucoes_sugeridas: list[str] | None = None
    notificar_agente: bool = False
    encaminhar_humano: bool = False
    duplicatas_possiveis: list[str] | None = None


class TicketSimilar(BaseModel):
    texto: str
    resolucao: str
    pontuacao_similaridade: float


class SugerirRespostaResponse(BaseModel):
    consulta: str
    tickets_similares: list[TicketSimilar]


class DetalheTicket(BaseModel):
    id: str
    texto: str
    nome_cliente: str
    canal: str
    categoria: str
    confianca: float
    severidade: NivelSeveridade
    status: StatusTicket
    resposta_ia: str | None = None
    resumo_ia: str | None = None
    solucoes_sugeridas: list[str] | None = None
    duplicatas_possiveis: list[str] | None = None
    agente_responsavel: str | None = None
    criado_em: datetime
    resolvido_em: datetime | None = None


class InfoAgente(BaseModel):
    nome: str
    status: StatusAgente
    tickets_atribuidos: int
    ultimo_acesso: datetime


class InfoAlerta(BaseModel):
    id: str
    tipo: str
    mensagem: str
    severidade: NivelSeveridade
    contagem: int
    limite: int
    disparado_em: datetime
    reconhecido: bool = False


class MetricasResponse(BaseModel):
    periodo: str
    total_tickets: int
    por_severidade: dict[str, int]
    por_status: dict[str, int]
    tempo_medio_resolucao_horas: float | None = None
    auto_resolvidos: int
    pct_auto_resolvidos: float


class TopMotivosResponse(BaseModel):
    periodo: str
    filtro_severidade: str
    motivos: list[dict]


# --- Gestão de Usuários ---

class CriarUsuarioRequest(BaseModel):
    nome: str
    email: str
    senha: str
    perfil: str = "agente"


class AtualizarUsuarioRequest(BaseModel):
    nome: str | None = None
    perfil: str | None = None
    ativo: bool | None = None


class UsuarioResponse(BaseModel):
    email: str
    nome: str
    perfil: str
    ativo: bool = True


# --- Onboarding ---

class OnboardingResponse(BaseModel):
    registros_importados: int
    categorias_encontradas: list[str]
    rag_atualizado: bool
    mensagem: str


# --- Webhook ---

class WebhookTicketRequest(BaseModel):
    texto: str
    cliente: str = "Cliente Externo"
    canal: str = "webhook"
    metadata: dict | None = None
