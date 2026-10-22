"""Decisor: aplica a política (solution/05-politica.md) e a base de processos
(solution/06-base-de-processos.md) e escolhe a ação.

Ações: A responde sozinha · B resolve e encaminha · C resume e passa pro atendente
· D pessoa agora · E pede o que falta.

A ordem importa. Segurança, irritação e urgência vêm antes de tudo. Depois os
casos que precisam de pessoa. Só no fim, se nenhuma regra mandou pra pessoa,
a IA procura um processo da base que cubra o caso. Sem processo, vai pra pessoa.
"""
import re
from dataclasses import dataclass

from sinais import normaliza


@dataclass
class Decisao:
    acao: str
    regra: str
    processo: str
    porque: str


def _int(v, padrao=None):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return padrao


def decide(t, s):
    """t = ticket (linha do casos_teste.csv), s = sinais do leitor."""
    dias = _int(t.get("dias_desde_compra"))
    status = (t.get("status_pedido") or "").lower()
    tipo = t["tipo_d1"]
    tem = s.__contains__

    # ---- Pessoa na hora (D) ----
    if tem("seguranca"):
        return Decisao("D", "R9 Segurança", "PR-20 Risco físico", f"Risco físico: \"{s['seguranca']}\". Passa na frente de qualquer outra regra.")
    if tem("pede_pessoa"):
        return Decisao("D", "R1 Irritação", "PR-26 Cliente pede uma pessoa", "O cliente pediu uma pessoa. Sem insistir.")
    if tem("irritacao") or tem("caixa_alta") or tem("ironia"):
        sinal = s.get("irritacao") or s.get("ironia") or s.get("caixa_alta")
        return Decisao("D", "R1 Irritação", "", f"Cliente irritado: \"{sinal}\". Vai direto pra pessoa, sem resposta automática.")
    if tem("fraude_cartao"):
        return Decisao("D", "R10 Urgência", "PR-18 Compra não reconhecida", "Possível fraude no cartão. Urgente e sem processo que a IA siga sozinha.")
    if tem("luto"):
        return Decisao("D", "R2 Momento difícil", "", "Luto na família. Precisa de uma pessoa, com cuidado.")

    # ---- Resumo pro atendente (C) ----
    if tem("vulneravel"):
        return Decisao("C", "R2 Momento difícil", "", f"Momento difícil: \"{s['vulneravel']}\". Precisa de acolhimento humano.")
    if tem("ameaca") or tem("por_escrito"):
        sinal = s.get("ameaca") or s.get("por_escrito")
        return Decisao("C", "R7 Ameaça ou pedido por escrito", "", f"\"{sinal}\". Uma pessoa responde, a IA não confirma nada.")
    if tem("saude"):
        return Decisao("C", "R5 Risco", "PR-21 Saúde", "Pergunta de saúde. A IA não avalia, passa pra pessoa.")
    if tem("dados_pessoais"):
        return Decisao("C", "R5 Risco", "PR-19 Dados pessoais", "Pedido de exclusão de dados (LGPD). Tem processo legal próprio.")
    if tem("golpe"):
        return Decisao("C", "R5 Risco", "PR-18 Golpe", "Suspeita de golpe ou anúncio falso.")
    if tem("responsabilidade"):
        return Decisao("C", "R11 Apurar responsabilidade", "PR-04 Produto errado", "O cliente tem direito, mas alguém precisa apurar onde o produto foi trocado.")
    if tem("dano_outro") or tem("falsificado"):
        return Decisao("C", "R5 Risco", "PR-24 Dano ou falsificação", "Envolve culpa da loja. A IA não admite nem nega.")
    if tem("valor_diferente"):
        return Decisao("C", "R5 Complexo", "PR-05 Estorno no cartão", "Valor diferente do esperado. Alguém precisa olhar o caso.")
    if tem("defeito") and tem("duplicada"):
        return Decisao("C", "R5 Complexo", "PR-03 + PR-12", "Dois problemas diferentes no mesmo ticket.")
    if tem("outro_idioma"):
        return Decisao("C", "R5 Complexo", "", "Mensagem em outro idioma. Uma pessoa atende.")
    if tem("excecao") and not tem("manipulacao"):
        return Decisao("C", "R6 Exceção", "PR-15 Cupom, desconto e preço", f"\"{s['excecao']}\". Depende de a empresa aceitar uma exceção.")
    if tem("rastreio_parado"):
        return Decisao("C", "R5 Complexo", "PR-06 Atraso ou rastreio parado", "Rastreio parado há dias. Abre investigação com a transportadora.")
    if tem("quer_dinheiro") and tem("defeito") and dias is not None and dias > 7:
        return Decisao("C", "R5 Complexo", "PR-03 Produto com defeito", "Defeito fora dos 7 dias e o cliente quer o dinheiro, não conserto.")

    # ---- A IA responde recusando (A) ----
    if tem("manipulacao"):
        return Decisao("A", "R4 Pedido sem base", "PR-25 Tentativa de manipular a IA", "Tentativa de mudar o papel da IA ou aprovação que não está registrada. Recusa com educação.")
    if tem("cartao_no_chat"):
        return Decisao("A", "R4 Pedido sem base", "PR-19 Dados pessoais", "Quer mandar dados do cartão no chat. A IA recusa e orienta pagar pelo site.")
    if tem("dado_de_terceiro"):
        return Decisao("A", "R4 Pedido sem base", "PR-19 Dados pessoais", "Documento de outra pessoa. A IA recusa.")

    # ---- Falta informação (E) ----
    if tem("vago") or tem("falta_codigo") or (tipo == "Cancellation request" and "varios" in normaliza(status)):
        return Decisao("E", "R8 Falta informação", "", "Não dá pra seguir sem mais informação.")

    # ---- Processos da base ----
    return _processo(t, s, tipo, dias, status)


def _processo(t, s, tipo, dias, status):
    """Só devolve A ou B quando reconhece, de forma positiva, um processo escrito
    que cobre o caso. O tipo do ticket sozinho não é processo. Na dúvida, pessoa.

    Versão 2. Na versão 1, cada tipo tinha um padrão "responde sozinha", e foi
    por esse buraco que passaram os erros perigosos do teste com tickets novos
    (process-log/erros-da-ia.md, E10)."""
    tem = s.__contains__
    st = normaliza(status)
    msg = normaliza(t["mensagem_do_cliente"])
    pergunta = "?" in t["mensagem_do_cliente"]

    if tipo == "Cancellation request":
        if "assinatura" in st:
            return Decisao("B", "R3 Regra objetiva", "PR-10 Assinatura digital", "Cancela a renovação da assinatura.")
        if "nao enviado" in st:
            return Decisao("B", "R3 Regra objetiva", "PR-08 Pedido não enviado", "O pedido ainda não saiu. Cancela direto.")
        if "enviado" in st:
            return Decisao("B", "R3 Regra objetiva", "PR-09 Pedido já enviado", "Já enviado. Orienta recusar na entrega ou devolver em 7 dias.")
        if "garantia" in st:
            return Decisao("A", "R4 Informação", "PR-11 Garantia estendida", "Explica a regra geral. O valor exato vem da seguradora.")
        if dias is not None and dias > 7 and "entregue" in st:
            return Decisao("A", "R4 Informação", "PR-02 Fora dos 7 dias", "Passou do prazo de arrependimento. Explica e passa pra equipe se insistir.")

    if tipo == "Refund request":
        if tem("faltando_item"):
            return Decisao("B", "R3 Regra objetiva", "PR-04 Item faltando", "Item faltando no pacote. Abre o envio da peça.")
        if tem("atraso_pequeno"):
            return Decisao("A", "R4 Pedido sem base", "PR-07 Frete por atraso pequeno", "Atraso de um dia não dá reembolso de frete.")
        if dias is not None and dias <= 7 and "entregue" in st:
            return Decisao("B", "R3 Regra objetiva", "PR-01 Arrependimento", f"{dias} dias desde o recebimento. Dentro dos 7 dias, sem precisar justificar.")
        if dias is not None and dias > 7 and "entregue" in st and not tem("defeito"):
            return Decisao("A", "R4 Informação", "PR-02 Fora dos 7 dias", "Passou do prazo e não tem defeito. Explica e passa pra equipe se insistir.")
        if "devolvido" in st and re.search(r"(quanto tempo|quando).{0,40}(estorno|reembolso|dinheiro)", msg):
            return Decisao("A", "R4 Informação", "PR-05 Estorno no cartão", "Dúvida sobre o prazo do estorno. Explica a regra geral, sem dar data.")

    if tipo == "Technical issue":
        if tem("defeito") and dias is not None and dias <= 7:
            return Decisao("B", "R3 Regra objetiva", "PR-03 Produto com defeito", "Defeito em até 7 dias. Abre a troca ou a devolução.")
        if "garantia" in msg:
            return Decisao("A", "R4 Informação", "PR-23 Garantia", "Explica a garantia legal e a do fabricante.")
        if re.search(r"como (eu )?(faco|configur|conect|instal|uso|ligo|pareio)|\b(versao|firmware|atualizacao)\b", msg):
            return Decisao("A", "R4 Informação", "PR-22 Dúvida de produto", "Dúvida de uso. Responde só com o que está na ficha, e diz quando não sabe.")

    if tipo == "Billing inquiry":
        if tem("duplicada"):
            return Decisao("B", "R3 Regra objetiva", "PR-12 Cobrança duplicada", "Cobrança repetida com comprovante. Abre o estorno.")
        if re.search(r"nota fiscal", msg) and not re.search(r"cnpj|corrig|errad", msg):
            return Decisao("A", "R4 Informação", "PR-14 Nota fiscal", "Mostra onde baixar a nota.")
        if re.search(r"\b(boleto|pix|cashback|parcel|trocar o cartao)", msg):
            return Decisao("A", "R4 Informação", "PR-13 a PR-16 Cobrança", "Dúvida de pagamento com regra escrita.")

    if tipo == "Product inquiry":
        if pergunta:
            return Decisao("A", "R4 Informação", "PR-22 Dúvida de produto", "Dúvida de produto antes da compra. Responde com a ficha e as regras escritas.")
        if re.search(r"\b(amei|adorei|parabens|obrigad)", msg):
            return Decisao("A", "R4 Informação", "", "Elogio. Agradece.")

    # Nenhum processo cobre: princípio da política, vai pra pessoa.
    return Decisao("C", "Sem processo", "", "Nenhum processo da base cobre o caso. Vai pra pessoa.")
