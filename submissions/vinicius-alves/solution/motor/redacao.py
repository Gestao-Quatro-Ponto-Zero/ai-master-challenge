"""Redator: monta o resumo pro atendente, o rascunho pro cliente e a trava.

Os rascunhos saem de frases que a base de processos permite. A trava confere
qualquer texto (da IA, de um modelo local ou de uma pessoa) contra o que nunca
pode ser prometido. Pra IA, a trava bloqueia. Pra pessoa, avisa.
"""
import re

from sinais import normaliza

# O que nunca pode sair. Mesma lista da tela (interface/index.html).
TRAVA = [
    (r"\b(cai|caiu|cair|volta|voltar|chega|chegar|sai|sair)\b[^.?!]{0,40}\b(ate|antes|amanha|hoje|sexta|segunda|terca|quarta|quinta|sabado|domingo|\d+\s*dias?)\b", "promete prazo"),
    (r"\b\d+\s*dias?\s*uteis\b", "promete prazo"),
    (r"\baprovad[oa]\b", "confirma aprovação"),
    (r"\bgarantid[oa]\b", "garante resultado"),
    (r"\bem dobro\b", "promete devolução em dobro"),
    (r"\bindeniza", "fala em indenização"),
    (r"\b(desconto|cupom)\b[^.?!]{0,30}\b(aplic|liber|consig|dar\b|dou\b)", "concede desconto"),
    (r"\b(dar|dou|aplicar|aplico|liberar|libero|consigo|posso)\b[^.?!]{0,20}\b(desconto|cupom)\b", "concede desconto"),
    (r"\b(e normal|pode continuar usando|pode usar normalmente)\b", "minimiza risco"),
    (r"\b(culpa nossa|nossa culpa|culpa e nossa|erro nosso|erro e nosso|foi erro da loja)\b", "assume culpa"),
]


def trava(texto):
    """Lista do que a trava encontrou: [(trecho, motivo)]. Vazia = pode sair.
    Frase negada logo antes ("não é normal", "não consigo aplicar desconto") passa."""
    t = normaliza(texto)
    achados = []
    for padrao, motivo in TRAVA:
        for m in re.finditer(padrao, t):
            antes = t[max(0, m.start() - 14):m.start()]
            if re.search(r"\bnao\b", antes) or re.match(r"nao\b", m.group(0)):
                continue
            achados.append((m.group(0), motivo))
            break
    return achados


def primeiro_nome(nome):
    return (nome or "").split(" ")[0]


def _o_que_quer(t, s):
    msg = normaliza(t["mensagem_do_cliente"])
    if re.search(r"cancel", msg):
        return "Quer cancelar"
    if re.search(r"reembolso|dinheiro de volta|estorno|devolver", msg):
        return "Quer o dinheiro de volta"
    if re.search(r"troc", msg):
        return "Quer trocar"
    if "?" in t["mensagem_do_cliente"]:
        return "Tem uma dúvida"
    return "Relata um problema"


def resumo(t, s, d):
    """Resumo pro atendente: o que precisa saber sem ler a conversa toda."""
    itens = []
    valor = t.get("valor_rs")
    prod = t.get("produto") or "Sem produto identificado"
    itens.append(f"{prod}{f', R$ {float(valor):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if valor else ''}")
    if t.get("dias_desde_compra") not in (None, ""):
        itens.append(f"{t['dias_desde_compra']} dias desde a compra · {t['status_pedido']}")
    else:
        itens.append(t["status_pedido"])
    contatos = int(t.get("contatos_anteriores") or 0)
    if contatos:
        itens.append(f"Já entrou em contato {contatos} vez(es) antes")
    itens.append(_o_que_quer(t, s))
    rotulos = {
        "seguranca": "Risco físico", "irritacao": "Irritado", "ironia": "Irônico", "caixa_alta": "Escreveu em caixa alta",
        "vulneravel": "Momento difícil", "luto": "Luto", "ameaca": "Ameaça", "por_escrito": "Pede por escrito",
        "fraude_cartao": "Possível fraude", "golpe": "Possível golpe", "manipulacao": "Tentou manipular a IA",
        "saude": "Pergunta de saúde", "outro_idioma": "Outro idioma",
    }
    for k, r in rotulos.items():
        if k in s:
            itens.append(f"{r}: \"{s[k]}\"")
    return itens


def rascunho(t, s, d):
    """Mensagem pro cliente. Só frases que a base permite, sem prometer nada."""
    n = primeiro_nome(t.get("cliente"))
    oi = f"{n}, " if n else ""
    proc = d.processo

    # Situações em que a IA manda uma orientação antes de passar.
    if d.regra.startswith("R9"):
        return "Pare de usar o aparelho agora e desligue da tomada. Não carregue. Uma pessoa do nosso time já vai falar com você.", True
    if d.regra.startswith("R10"):
        return "Bloqueie o cartão no app do banco agora. Uma pessoa do nosso time vai falar com você em seguida.", True

    if d.acao == "D":
        return f"{oi}entendi, e sinto muito pelo transtorno. Uma pessoa do time já está com o seu caso e vai te responder por aqui.", False
    if d.acao == "C":
        if "PR-21" in proc:
            return f"{oi}não consigo avaliar sua saúde por aqui. Se você está se sentindo mal, procure atendimento médico. Passei seu caso pra uma pessoa do time.", False
        if d.regra.startswith("R2"):
            return f"{oi}não precisa se desculpar. Passei seu caso pra uma pessoa do time com tudo explicado, pra você não ter que contar de novo.", False
        if d.regra.startswith("R7"):
            return f"{oi}recebemos sua mensagem. Uma pessoa do time vai analisar e responder.", False
        return f"{oi}registrei seu caso com todos os detalhes. Uma pessoa do time vai cuidar dele.", False
    if d.acao == "E":
        if "falta_codigo" in s:
            return f"{oi}quando a luz piscar de novo, aparece alguma letra ou número no visor? Com isso a gente já abre o chamado da assistência.", False
        return f"Oi{', ' + n if n else ''}! Me conta um pouco mais: qual pedido e o que aconteceu?", False

    # A e B: resposta pelo processo.
    textos = {
        "PR-01": f"Pode sim, {n}. Você tem até 7 dias do recebimento pra devolver, sem precisar justificar. Já abri a devolução e mandei as instruções pro seu e-mail.",
        "PR-02": f"{oi}o prazo de arrependimento é de 7 dias do recebimento, e o seu pedido passou disso. Se quiser, passo seu pedido pra equipe avaliar.",
        "PR-03": f"{oi}sinto muito pelo defeito. Já abri a troca. Se preferir devolver, também dá, porque você está dentro dos 7 dias.",
        "PR-04": f"{oi}já abri o envio do item que faltou. Você recebe o código de rastreio por e-mail.",
        "PR-07": f"{oi}o pedido chegou um dia depois do previsto, e peço desculpas por isso. Atrasos pequenos assim não dão reembolso de frete.",
        "PR-08": f"Consegue sim, {n}. Cancelei o pedido e pedi o estorno pra operadora do cartão.",
        "PR-09": f"{oi}o pedido já saiu. Você pode recusar na entrega ou, depois de receber, devolver em até 7 dias. Nos dois casos o valor volta inteiro.",
        "PR-11": f"{oi}a garantia estendida é um seguro. Depois de 7 dias da contratação, o cancelamento devolve a parte proporcional ao tempo que falta. O valor exato quem calcula é a seguradora.",
        "PR-12": f"{oi}recebi o print, obrigado. Já abri o pedido de estorno da cobrança repetida.",
        "PR-19": f"{oi}por segurança, não posso receber nem enviar dados de cartão ou documentos de outra pessoa por aqui.",
        "PR-23": f"{oi}todo produto tem garantia legal de 90 dias, mais a garantia do fabricante que vem no manual. A cobertura depende da análise da assistência.",
        "PR-25": f"{oi}não consigo fazer isso por aqui. Se quiser, te ajudo com o que estiver ao meu alcance.",
    }
    for chave, texto in textos.items():
        if proc.startswith(chave):
            return texto, False
    return f"{oi}aqui vai a informação que está na ficha do produto e nas nossas regras escritas.", False
