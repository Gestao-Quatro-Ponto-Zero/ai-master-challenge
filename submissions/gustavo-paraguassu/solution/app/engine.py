"""Núcleo independente de canal: recebe o texto do cliente e decide o próximo passo.

Política (P5 em 04_cost_of_error.py):
  - vai direto para a fila só se a confiança passa do limiar daquela fila (meta 95% de acerto),
    a fila não é sensível, a trava de sensibilidade não disparou e não há sinal de risco;
  - caso contrário vai para a triagem humana, com as 3 filas mais prováveis como sugestão;
  - falta campo obrigatório -> pergunta ao cliente uma única vez, antes de ocupar um atendente;
  - resposta automática só para o caso delimitado de troca de senha (com saída para pessoa);
  - toda resposta ao cliente sai de conteudo_aprovado.json, revisada por um atendente.
Telegram, WhatsApp ou e-mail são só adaptadores em volta disto.
"""
import json
import re
from dataclasses import dataclass, field, asdict

from . import config, llm, pii
from .router import Router, Rota, SENSIVEIS

CONTEUDO = json.loads(config.CONTENT_PATH.read_text())
FILAS = CONTEUDO["filas"]
RISCOS_QUE_EXIGEM_HUMANO = {"dado_pessoal", "acao_irreversivel", "compromisso_financeiro", "seguranca"}
NOME_RISCO = {"dado_pessoal": "dado pessoal", "acao_irreversivel": "ação irreversível",
              "compromisso_financeiro": "compromisso financeiro", "seguranca": "segurança",
              "cliente_irritado": "cliente irritado"}


@dataclass
class Decisao:
    destino: str                 # "fila" (direto para a equipe) | "triagem" (humano escolhe a fila)
    fila: str                    # fila prevista (top-1)
    conf: float
    limiar: float
    top3: list
    p_sens: float
    motivos: list = field(default_factory=list)   # por que foi para humano
    faltando: list = field(default_factory=list)  # campos obrigatórios que faltam (chaves de pergunta)
    pergunta: str | None = None  # texto para o cliente, se for perguntar
    auto: str | None = None      # chave de resposta automática, se elegível
    rascunho: str = ""           # resposta sugerida para o atendente revisar
    discordancia_llm: str | None = None  # fila que o LLM sugeriu, quando difere do classificador

    def to_dict(self):
        return asdict(self)


def preencher(modelo: str, campos: dict, extras: dict) -> str:
    """Troca {campo} e {campo|padrão} pelo valor dito pelo cliente (ou pelo padrão)."""
    def troca(m):
        chave, _, padrao = m.group(1).partition("|")
        v = campos.get(chave) or extras.get(chave)
        return str(v) if v else padrao
    return re.sub(r"\{([^{}]+)\}", troca, modelo)


def faltando(fila: str, campos: dict) -> list[str]:
    """Cada grupo de obrigatórios se satisfaz com qualquer um dos campos do grupo."""
    return [grupo[0] for grupo in FILAS[fila]["obrigatorios"] if not any(campos.get(c) for c in grupo)]


def rascunho(fila: str, campos: dict) -> str:
    f = FILAS[fila]
    return preencher(f["resposta_padrao"], campos, {"prazo": f["prazo"]})


def decidir(tri: llm.Triagem, rota: Rota, ja_perguntou: bool, forcar_humano: bool = False) -> Decisao:
    campos = tri.campos.model_dump()
    d = Decisao(destino="fila", fila=rota.fila, conf=rota.conf, limiar=rota.limiar, top3=rota.top3, p_sens=rota.p_sens)
    if rota.fila in SENSIVEIS:
        d.motivos.append(f"fila sensível ({FILAS[rota.fila]['sensivel']}): humano confirma")
    elif rota.p_sens >= config.G_SENS:
        d.motivos.append(f"pode ser RH/permissão de admin ({rota.p_sens:.0%}): humano confirma")
    riscos = [r for r in tri.sinais_de_risco if r in RISCOS_QUE_EXIGEM_HUMANO]
    if riscos:
        d.motivos.append("risco: " + ", ".join(NOME_RISCO[r] for r in riscos))
    if rota.conf < rota.limiar:
        d.motivos.append(f"confiança {rota.conf:.0%} abaixo do limiar da fila ({rota.limiar:.0%})")
    if tri.pede_humano or forcar_humano:
        d.motivos.append("cliente pediu atendente")
    if d.motivos:
        d.destino = "triagem"

    # Perguntar ao cliente (uma vez só). Três casos:
    #  - nada foi extraído (mensagem vaga): pede descrição, sem supor fila;
    #  - fila conhecida (confiança mínima e LLM concorda, ou acima do limiar): pergunta o que falta nela;
    #  - fila incerta (LLM e classificador discordam): não pergunta; a triagem humana resolve.
    d.faltando = faltando(rota.fila, campos)
    pode_perguntar = not ja_perguntou and not (tri.pede_humano or forcar_humano)
    fila_conhecida = rota.conf >= config.MIN_CONF_PERGUNTAR and (
        tri.fila_sugerida_llm == rota.fila or rota.conf >= rota.limiar)
    if pode_perguntar and not any(campos.values()):
        d.faltando = ["descricao"]
        d.pergunta = CONTEUDO["perguntas"]["descricao"]
    elif pode_perguntar and d.faltando and fila_conhecida:
        d.pergunta = CONTEUDO["mensagens"]["antes_das_perguntas"] + "\n" + "\n".join(
            f"• {CONTEUDO['perguntas'][k]}" for k in d.faltando[:2])
    if tri.fila_sugerida_llm != rota.fila:
        d.discordancia_llm = tri.fila_sugerida_llm

    pedido = f"{campos.get('tipo_acesso') or ''} {campos.get('sistema') or ''}"
    if d.destino == "fila" and rota.fila == "Access" and re.search(r"senha|password|reset|desbloq|bloque", pedido, re.I):
        d.auto = "reset_senha"
    d.rascunho = rascunho(rota.fila, campos)
    return d


class Motor:
    """Triagem completa de um texto: mascara PII -> LLM -> roteador -> política."""

    def __init__(self, router: Router | None = None):
        self.router = router or Router()

    def processar(self, texto: str, ja_perguntou=False, forcar_humano=False):
        mascarado = pii.mascarar(texto)
        tri, meta = llm.triar(mascarado)
        rota = self.router.prever(tri.texto_ingles)
        return tri, meta, decidir(tri, rota, ja_perguntou, forcar_humano)
