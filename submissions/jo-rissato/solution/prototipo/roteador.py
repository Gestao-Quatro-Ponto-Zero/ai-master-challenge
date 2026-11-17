"""Regras do roteador: funções puras, sem rede, testáveis.

Regra do Jó (rodada 59, 2026-11-11): a IA conduz o atendimento até o fim e só reembolso e cancelamento
passam para o time. Cobrança em dobro ou indevida é pedido de dinheiro de volta, então entra como
reembolso. Defeito de aparelho (bateria, aquecimento, não liga, peça, tela) vai para a assistência técnica
autorizada da empresa depois dos passos de verificação (rodada 60). A única outra passagem é quando a IA está fora do ar: aí uma pessoa assume, porque não há
quem converse com o cliente.

Regra do Jó (2026-11-16), que retoma o fluxo aprovado nas rodadas 47 e 48:
- Assunto incerto: se a confiança do classificador não passar do limite (0,8) depois de até MAX_PERGUNTAS
  perguntas de esclarecimento, ou quando a IA já iria dar a solução, uma pessoa assume a conversa e tem de
  fechar a chamada com um posicionamento.
- Comando restrito (mudar ou contornar política, excluir site ou domínio, mexer na infraestrutura: porta,
  firewall, servidor, DNS, VPN, acesso de administrador): a IA não executa, não altera e não repassa nenhum
  dado. A conversa vai direto ao departamento especializado, com etiqueta de atenção. A trava é por regra, antes
  de o texto ir para a IA externa.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from config import LIMITE_CONFIANCA, MAX_PERGUNTAS

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

# Comandos restritos (Jó, 2026-11-16), em português e inglês. O verbo de ação precisa vir junto do objeto, porque
# "abri o site e deu erro" é suporte comum, e "excluir o site" não é.
_VERBO_MUDA = r"(alter\w*|mud\w*|substitu\w*|troc\w*|desativ\w*|desabilit\w*|ignor\w*|burl\w*|contorn\w*|suspend\w*|remov\w*|tir\w*)"
_VERBO_ABRE = (r"(abr\w*|liber\w*|alter\w*|mud\w*|desativ\w*|desabilit\w*|desbloque\w*|reconfigur\w*|configur\w*|"
               r"apont\w*|reinici\w* o servidor|deslig\w*)")
_ART = r"(a |as |o |os |um |uma |essa |esta |esse |este |nossa |nosso |minha |meu |sua |seu |da |do |de )*"
PADROES_RESTRITOS = {
    "política": (rf"\b{_VERBO_MUDA} {_ART}(pol[ií]tica|regra) (de |da |do )?(seguran\w*|senha\w*|acesso|backup|"
                 rf"privacidade|uso|reten\w*|bloqueio)|\b(override|bypass|disable|change|ignore) (the |this |our )?"
                 rf"(security |password |access |backup )?polic\w*|\bpol[ií]tica\w* (de \w+ )?(substitu\w*|nova no lugar)"),
    "exclusão de site": (rf"\b(exclu\w*|delet\w*|apag\w*|remov\w*|derrub\w*|tir\w* do ar|desativ\w*|desligar) "
                         rf"{_ART}(site|sites|dom[ií]nio\w*|p[áa]gina\w* do site|hospedagem|portal)\b|"
                         r"\b(delete|remove|take down|shut down) (the |our |my |this )?(web ?site|site|domain|portal)\b"),
    "infraestrutura": (rf"\b{_VERBO_ABRE} {_ART}(porta\w*|firewall|vpn|dns|servidor\w*|banco de dados|"
                       rf"acesso (de |como )?(admin\w*|root)|permiss\w* de (admin\w*|root)|regra\w* de rede|proxy|"
                       rf"infraestrutura|backup\w*)\b|\b(senha|credencia\w*|acesso) (do|ao|de) (servidor|root|banco de dados|"
                       rf"firewall|roteador)\b|\b(acesso|permiss\w*|senha) (de |como )?(admin\w*|root) (no|ao|do|na|da) "
                       rf"(servidor|rede|dom[ií]nio|firewall|banco de dados)\b|\b(open|change|disable|reconfigure) (the |a )?(port|firewall|dns|vpn|"
                       rf"server|proxy)\b|\b(admin|root) (access|rights|password) (to|for|on) (the )?(server|network)\b"),
}
TIPOS_RESTRITOS = tuple(PADROES_RESTRITOS)
# Departamento especializado por tipo de comando. A setorização real do atendimento não está nos dados (lacuna 2):
# os nomes são de exemplo e ficam nos placeholders do LEIAME.
DEPARTAMENTO = {"política": "Segurança da informação", "exclusão de site": "Web e sistemas",
                "infraestrutura": "Infraestrutura"}

# Palavras de cortesia e de pedido genérico, usadas no modo sem IA para saber se o cliente já contou algo.
VAZIAS = set("""hi hello hey dear good morning afternoon evening please thanks thank you regards kind best
help need i a an the have has is am are my me we us it this that to for with and or problem issue
question something urgent asap support team hope well olá ola oi bom dia boa tarde noite obrigado obrigada
por favor ajuda preciso de um uma o a e meu minha problema quero tenho estou
tudo bem bom como vai você voce vc td beleza blz alô alo opa salve tranquilo joia jóia aí ai e com""".split())
MIN_PALAVRAS_UTEIS = 2

# Cliente desiste por texto (régua 2.4): a conversa fecha sem encaminhar.
DESISTENCIA = r"(\bn[ãa]o quero mais\b(?!\s+\w)|\bpode esquecer\b|\bdeixa (pra|para) l[áa]\b|\bdesisto\b|\bnever ?mind\b|\bforget it\b)"

ATENDENDO = "IA atendendo"
RESOLVIDA = "resolvida pela IA"
EXECUCAO = "pessoa executa"
ENCERRADA = "cliente desistiu"
ASSISTENCIA = "assistência técnica"   # defeito de aparelho (rodada 60): vai para a assistência autorizada
TRIAGEM = "triagem humana"      # só quando a IA está fora do ar
INCERTO = "assunto incerto"     # confiança abaixo do limite: uma pessoa assume e dá o posicionamento (2026-11-16)
ESPECIALISTA = "departamento especializado"   # comando restrito: atenção, sem executar nem alterar (2026-11-16)
COM_PESSOA = (EXECUCAO, TRIAGEM, INCERTO, ESPECIALISTA)   # destinos que exigem posicionamento de uma pessoa
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


def comando_restrito(texto: str) -> str | None:
    """Devolve o tipo de comando restrito (política, exclusão de site, infraestrutura), ou None."""
    t = texto.lower()
    for nome, padrao in PADROES_RESTRITOS.items():
        if re.search(padrao, t):
            return nome
    return None


def assunto_incerto(confianca: float, perguntas: int, ia_vai_resolver: bool, limite: float = LIMITE_CONFIANCA,
                    max_perguntas: int = MAX_PERGUNTAS) -> bool:
    """Regra das rodadas 47 e 48, retomada em 2026-11-16: abaixo do limite, a IA só segue enquanto pergunta.
    Passa para uma pessoa quando a IA já iria dar a solução ou quando esgotou as perguntas de esclarecimento."""
    return confianca < limite and (ia_vai_resolver or perguntas >= max_perguntas)


def palavras_uteis(texto: str) -> int:
    """Quantas palavras do texto não são cortesia nem pedido genérico."""
    return sum(1 for w in re.findall(r"[a-zà-ú]+", texto.lower()) if w not in VAZIAS)


def desistiu(texto: str) -> bool:
    return re.search(DESISTENCIA, texto.lower()) is not None


def decidir(categoria: str, confianca: float, sensivel: str | None, resolvido: bool = False,
            desistencia: bool = False, assistencia: bool = False, restrito: str | None = None) -> Decisao:
    """Decide o que acontece com a conversa nesta rodada."""
    rotulo = ROTULOS.get(categoria, categoria)
    if restrito:
        return Decisao(ESPECIALISTA, f"{restrito}: comando restrito, sem executar nem alterar dado; vai ao departamento de "
                                     f"{DEPARTAMENTO[restrito]} com etiqueta de atenção", categoria, confianca)
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
