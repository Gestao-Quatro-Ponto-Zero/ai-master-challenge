"""Leitor: procura no ticket os sinais que as regras da política usam.

Tudo com regras e palavras em português, sem modelo e sem chave de API.
Cada sinal guarda o trecho que disparou, pra decisão poder mostrar o porquê.
"""
import re
import unicodedata


def normaliza(texto):
    """Minúsculo e sem acento, pra comparar sem depender de como o cliente digitou."""
    t = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


# Cada sinal é uma lista de padrões (já sem acento).
PADROES = {
    "seguranca": [
        r"estufad", r"cheiro de queimad", r"fumaca", r"faisca", r"pegou fogo", r"superaquec", r"explod", r"levei (um )?choque",
    ],
    "irritacao": [
        r"\bmerda\b", r"\bporra\b", r"\bcaralho\b", r"\bladro(es|oes)\b", r"\bporcaria\b", r"\bpalhacada\b", r"\bvergonha\b",
        r"(terceira|quarta|quinta) vez", r"de brincadeira", r"ninguem (me )?(responde|da uma posicao)",
        r"nunca mais compro", r"pior experiencia", r"nao quero mais falar com robo",
    ],
    "ironia": [
        r"que maravilha", r"parabens pelo atendimento", r"realmente incrive", r"que rapidez", r"atendimento de excelencia",
        r"correio do ano que vem",
    ],
    "pede_pessoa": [
        r"falar com (uma )?pessoa", r"atendente humano", r"falar com (um )?humano", r"nao quero (mais )?falar com robo",
    ],
    "luto": [r"faleceu", r"falecimento", r"\bmorreu\b", r"\bluto\b"],
    "vulneravel": [
        r"demitid", r"desempregad", r"perdi o emprego", r"nao sei mais o que fazer", r"aluguel vence",
        r"tenho ([7-9]\d) anos", r"nao sei mexer",
    ],
    "fraude_cartao": [r"nao comprei nada", r"nao reconheco", r"alguem esta usando meu cartao", r"cartao (foi )?clonad"],
    "golpe": [r"cai num golpe", r"\bgolpe\b", r"anuncio (falso|do instagram)"],
    "ameaca": [
        r"reclame aqui", r"\bprocon\b", r"\bprocesso\b", r"advogad", r"\bjustica\b", r"chargeback", r"nao vai ficar assim",
        r"indeniza",
    ],
    "por_escrito": [r"por escrito", r"guardar o print"],
    "manipulacao": [
        r"ignore (todas )?as instrucoes", r"a partir de agora responda", r"voce agora e", r"como se voce fosse",
        r"sou funcionario", r"supervisores sempre", r"ja aprovou",
    ],
    "saude": [r"batimentos", r"pressao (arterial)?", r"frequencia cardiaca", r"preciso me preocupar", r"seguro pra crianca"],
    "dados_pessoais": [r"apaguem (todos )?(os )?meus dados", r"\blgpd\b"],
    "dado_de_terceiro": [r"(da|de) minha (esposa|mae|filha|irma)\b.*\bcpf\b", r"\bcpf (dela|dele)\b", r"cpf dela"],
    "cartao_no_chat": [r"numero do cartao", r"codigo de seguranca"],
    "responsabilidade": [r"tijolo", r"caixa vazia", r"veio outro produto", r"produto errado", r"veio trocado"],
    "valor_diferente": [r"veio so r?\$?", r"cade o resto", r"valor maior", r"cobrando juros", r"e nao r\$", r"descontaram"],
    # "queimou" sozinho: o cliente escreve "o iPhone queimou" tanto quanto "queimou meu iPhone".
    "dano_outro": [r"\bqueimou\b", r"danificou (meu|o)", r"estragou (meu|o)", r"paguem o"],
    "falsificado": [r"falsificad", r"vendem produto falso"],
    "excecao": [
        r"desconto", r"cobrem o preco", r"devolvem a diferenca", r"\bcupom\b", r"frete gratis", r"influenciador",
    ],
    "quer_dinheiro": [r"nao quero conserto", r"quero o dinheiro de volta, nao", r"nao quero trocar"],
    "faltando_item": [r"veio sem", r"faltando", r"faltou"],
    "duplicada": [r"(cobrado|cobrança|cobranca) duas vezes", r"cobrado duas", r"duas cobrancas", r"apareceu a cobranca duas"],
    "defeito": [
        r"nao (acende|liga)", r"parou de (ligar|funcionar)", r"com defeito", r"nao gira", r"linha vertical", r"tela (preta|trincada)",
        r"barulho", r"cai do wi-?fi", r"desconect",
    ],
    "rastreio_parado": [r"rastreio .*parado", r"parado no mesmo lugar"],
    "atraso_pequeno": [r"um dia depois do prazo", r"chegou .*atrasad"],
    "falta_codigo": [r"piscando uma luz"],
}


def _procura(chave, texto_norm, original):
    """Devolve o trecho do texto ORIGINAL (com acento), estendido até palavras inteiras.
    Tirar acento de letra já composta não muda o tamanho, então as posições batem."""
    for p in PADROES[chave]:
        m = re.search(p, texto_norm)
        if m:
            ini, fim = m.start(), m.end()
            while ini > 0 and texto_norm[ini - 1].isalnum():
                ini -= 1
            while fim < len(texto_norm) and texto_norm[fim].isalnum():
                fim += 1
            if len(original) == len(texto_norm):
                return original[ini:fim].strip()
            return texto_norm[ini:fim].strip()
    return None


def le(ticket):
    """Devolve {sinal: trecho que disparou} só com os sinais encontrados."""
    msg = ticket["mensagem_do_cliente"]
    t = normaliza(msg)
    achados = {}
    for chave in PADROES:
        trecho = _procura(chave, t, msg)
        if trecho:
            achados[chave] = trecho

    # Caixa alta: mais de 60% das letras maiúsculas numa mensagem que não é curtinha.
    letras = [c for c in msg if c.isalpha()]
    if len(letras) >= 15 and sum(c.isupper() for c in letras) / len(letras) > 0.6:
        achados["caixa_alta"] = "mensagem em caixa alta"

    # Recorrência: voltou várias vezes e já mostra frustração.
    if int(ticket.get("contatos_anteriores") or 0) >= 3 and ("irritacao" in achados or "caixa_alta" in achados):
        achados["recorrente"] = f"{ticket['contatos_anteriores']}º contato"

    # Idioma: sem nenhuma palavra comum de português.
    if not re.search(r"\b(de|que|nao|meu|minha|voces|o|a|e|pra|com)\b", t) and re.search(r"\b(the|my|is|and|you|help)\b", t):
        achados["outro_idioma"] = "mensagem em outro idioma"

    # Mensagem curta demais pra saber o que fazer.
    palavras = re.findall(r"\w+", t)
    if len(palavras) <= 3:
        achados["vago"] = f"só {len(palavras)} palavra(s)"

    return achados
