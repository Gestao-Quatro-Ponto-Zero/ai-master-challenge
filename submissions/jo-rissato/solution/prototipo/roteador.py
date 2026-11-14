"""Regras do roteador: funções puras, sem rede, testáveis.

Regra do Jó (rodada 59, 2026-11-11): a IA conduz o atendimento até o fim e só reembolso e cancelamento
passam para o time. Cobrança em dobro ou indevida é pedido de dinheiro de volta, então entra como
reembolso. Defeito de aparelho (bateria, aquecimento, não liga, peça, tela) vai para a assistência técnica
autorizada da empresa depois dos passos de verificação (rodada 60). A única outra passagem é quando a IA está fora do ar: aí uma pessoa assume, porque não há
quem converse com o cliente.

O limite de confiança e a fila por assunto continuam valendo só para a simulação em lote sobre o
Dataset 2 (`decidir_lote`), que mede o classificador.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from config import LIMITE_CONFIANCA

ROTULOS = {"Hardware": "Hardware", "HR Support": "Suporte de RH", "Access": "Acesso",
           "Miscellaneous": "Diversos", "Storage": "Armazenamento", "Purchase": "Compra",
           "Internal Project": "Projeto interno", "Administrative rights": "Direitos de administrador"}

# Pedidos que passam para o time. A trava é por regra, em português e inglês, e a IA conversacional
# também sinaliza. Os padrões de cancelamento pedem o objeto ("cancelar a assinatura"), porque numa
# conversa de suporte "cliquei em cancelar" é comum e não é pedido de cancelamento.
PADROES_SENSIVEIS = {
    "cobrança duplicada": r"\b(cobran\w* (duplicad\w*|em dobro|repetid\w*)|cobrad\w* (duas vezes|em dobro|2 vezes)"
                          r"|charged twice|double charged|duplicate charge)\b",
    "cobrança indevida": (r"\b(cobran\w* (indevid\w*|errad\w*|a mais)|cobrad\w* a mais|contest\w* (a |uma )?cobran\w*"
                          r"|wrong charge|overcharg\w*|dispute\w* (a |the )?charge)\b"),
    "reembolso": r"\b(reembols\w*|refund\w*|estorn\w*|chargeback|money back|dinheiro de volta|devolu\w* (do|o) (dinheiro|valor))\b",
    "cancelamento": (r"\b(cancel\w* (a |o |minha |meu |the |my )?(assinatura|plano|pedido|compra|conta|contrato|servi\w*"
                     r"|subscription|plan|order|account)|quero cancelar|i want to cancel)\b"),
}
TIPOS_SENSIVEIS = tuple(PADROES_SENSIVEIS)

# Palavras de cortesia e de pedido genérico, usadas no modo sem IA para saber se o cliente já contou algo.
VAZIAS = set("""hi hello hey dear good morning afternoon evening please thanks thank you regards kind best
help need i a an the have has is am are my me we us it this that to for with and or problem issue
question something urgent asap support team hope well olá ola oi bom dia boa tarde noite obrigado obrigada
por favor ajuda preciso de um uma o a e meu minha problema quero tenho estou""".split())
MIN_PALAVRAS_UTEIS = 2

# Cliente desiste por texto (régua 2.4): a conversa fecha sem encaminhar.
DESISTENCIA = r"(\bn[ãa]o quero mais\b(?!\s+\w)|\bpode esquecer\b|\bdeixa (pra|para) l[áa]\b|\bdesisto\b|\bnever ?mind\b|\bforget it\b)"

ATENDENDO = "IA atendendo"
RESOLVIDA = "resolvida pela IA"
EXECUCAO = "pessoa executa"
ENCERRADA = "cliente desistiu"
ASSISTENCIA = "assistência técnica"   # defeito de aparelho (rodada 60): vai para a assistência autorizada
TRIAGEM = "triagem humana"      # só quando a IA está fora do ar
FILA = "fila"                   # só na simulação em lote


@dataclass(frozen=True)
class Decisao:
    destino: str
    motivo: str
    categoria: str
    confianca: float


def acao_sensivel(texto: str) -> str | None:
    """Devolve o tipo de pedido que passa para o time, ou None."""
    t = texto.lower()
    for nome, padrao in PADROES_SENSIVEIS.items():
        if re.search(padrao, t):
            return nome
    return None


def palavras_uteis(texto: str) -> int:
    """Quantas palavras do texto não são cortesia nem pedido genérico."""
    return sum(1 for w in re.findall(r"[a-zà-ú]+", texto.lower()) if w not in VAZIAS)


def desistiu(texto: str) -> bool:
    return re.search(DESISTENCIA, texto.lower()) is not None


def decidir(categoria: str, confianca: float, sensivel: str | None, resolvido: bool = False,
            desistencia: bool = False, assistencia: bool = False) -> Decisao:
    """Decide o que acontece com a conversa nesta rodada."""
    rotulo = ROTULOS.get(categoria, categoria)
    if desistencia:
        return Decisao(ENCERRADA, "o cliente desistiu: conversa encerrada sem encaminhar", categoria, confianca)
    if sensivel:
        return Decisao(EXECUCAO, f"{sensivel}: a IA registra o pedido e uma pessoa decide e executa "
                                 f"(assunto previsto: {rotulo}, confiança {confianca:.2f})", categoria, confianca)
    if assistencia:
        # Defeito de aparelho vale mais que "resolvido": o sintoma pode ter aliviado (rodada 60, chamada 84).
        return Decisao(ASSISTENCIA, f"defeito de aparelho: o cliente é encaminhado à assistência técnica autorizada "
                                    f"(assunto previsto: {rotulo})", categoria, confianca)
    if resolvido:
        return Decisao(RESOLVIDA, f"o cliente confirmou que resolveu (assunto previsto: {rotulo})", categoria, confianca)
    return Decisao(ATENDENDO, f"a IA segue o atendimento (assunto previsto: {rotulo}, confiança {confianca:.2f})",
                   categoria, confianca)


def decidir_lote(confianca: float, limite: float = LIMITE_CONFIANCA) -> str:
    """Decisão sem conversa, para rodar sobre tickets já escritos (simulação em lote do classificador)."""
    return FILA if confianca >= limite else TRIAGEM
