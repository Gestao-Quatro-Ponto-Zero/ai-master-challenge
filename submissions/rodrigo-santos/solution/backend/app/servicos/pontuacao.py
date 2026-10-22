"""
Pontuação (score) dos negócios abertos.

A lógica foi definida a partir da validação com o histórico
(app/servicos/validacao.py), que mostrou duas coisas:

1. Nenhum atributo do dataset (vendedor, produto, setor, conta, porte,
   região...) prevê quem ganha melhor que o acaso. Por isso a "chance"
   é a mesma para todos os negócios vivos: a taxa média da empresa.
2. Nenhum negócio do histórico, ganho ou perdido, ficou aberto mais que
   ~138 dias, e nenhum negócio que passou disso fechou depois. Esses
   negócios estão "parados": provavelmente foram abandonados.

O score vai de 0 a 100 e é a soma de três partes:

    SITUAÇÃO   (até 40) ativo = 40 · em prospecção = 20 · parado = 0
    VALOR      (até 40) preço do produto em escala logarítmica
                        (de US$ 55 a US$ 26.768; sem o log só o mais caro importaria)
    RETA FINAL (até 20) para negócios ativos: quanto mais perto do prazo em que
                        os negócios se resolvem, mais urgente conduzir à decisão

Negócio parado é sempre prioridade Baixa, com a ação "atualize ou encerre".
Pontos e limites ficam em app/config.py.
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pandas as pd

from app import config
from app.dados.carregador import ETAPA_PROSPECCAO, ETAPAS_ABERTAS, carregar_deals, obter_data_referencia
from app.servicos.estatisticas import EstatisticasHistoricas, calcular_estatisticas

PRIORIDADE_ALTA = "Alta"
PRIORIDADE_MEDIA = "Média"
PRIORIDADE_BAIXA = "Baixa"

SITUACAO_ATIVO = "ativo"
SITUACAO_PROSPECCAO = "prospeccao"
SITUACAO_PARADO = "parado"

# Partes do score, na ordem em que aparecem para o vendedor.
PARTES = ["situacao", "valor", "reta_final"]

NOMES_PARTES = {
    "situacao": "Situação do negócio",
    "valor": "Valor do negócio",
    "reta_final": "Reta final",
}

# A partir desta fração do prazo, o negócio ativo está "na reta final".
INICIO_RETA_FINAL = 0.75


# ---------------------------------------------------------------------------
# Cálculo do score
# ---------------------------------------------------------------------------

def _classificar_situacao(deals: pd.DataFrame, estat: EstatisticasHistoricas) -> pd.Series:
    situacao = pd.Series(SITUACAO_ATIVO, index=deals.index)
    situacao[deals["dias_aberto"] > estat.limite_dias] = SITUACAO_PARADO
    situacao[deals["deal_stage"] == ETAPA_PROSPECCAO] = SITUACAO_PROSPECCAO
    return situacao


def _classificar_prioridade(deal: pd.Series) -> str:
    if deal["parado"]:
        return PRIORIDADE_BAIXA
    if deal["score"] >= config.LIMITE_PRIORIDADE_ALTA:
        return PRIORIDADE_ALTA
    if deal["score"] >= config.LIMITE_PRIORIDADE_MEDIA:
        return PRIORIDADE_MEDIA
    return PRIORIDADE_BAIXA


def pontuar(deals: pd.DataFrame, estat: EstatisticasHistoricas, hoje: pd.Timestamp) -> pd.DataFrame:
    """
    Pontua os negócios recebidos, como se "hoje" fosse a data informada.

    Função pura (não lê arquivos): a tela usa com todo o histórico, e a
    validação usa com datas e estatísticas do passado.
    """
    deals = deals.copy()
    deals["dias_aberto"] = (hoje - deals["engage_date"]).dt.days  # NaN em prospecção
    deals["situacao"] = _classificar_situacao(deals, estat)
    deals["parado"] = deals["situacao"] == SITUACAO_PARADO

    # Fatores de 0 a 1.
    deals["fator_situacao"] = deals["situacao"].map({
        SITUACAO_ATIVO: 1.0,
        SITUACAO_PROSPECCAO: config.FRACAO_SITUACAO_PROSPECCAO,
        SITUACAO_PARADO: 0.0,
    })
    minimo, maximo = np.log(estat.preco_minimo), np.log(estat.preco_maximo)
    deals["fator_valor"] = ((np.log(deals["sales_price"]) - minimo) / (maximo - minimo)).clip(0, 1)
    deals["fator_reta_final"] = np.where(
        deals["situacao"] == SITUACAO_ATIVO,
        (deals["dias_aberto"] / estat.limite_dias).clip(0, 1),
        0.0,
    )

    # Pontos de cada parte; o score é a soma dos pontos já arredondados,
    # para que a conta mostrada ao vendedor feche exatamente.
    for parte in PARTES:
        deals[f"pontos_{parte}"] = (config.PONTOS_MAXIMOS[parte] * deals[f"fator_{parte}"]).round().astype(int)
    deals["score"] = sum(deals[f"pontos_{parte}"] for parte in PARTES)
    deals["prioridade"] = deals.apply(_classificar_prioridade, axis=1)

    # Valor esperado: a chance é a média da empresa (nenhum atributo a
    # diferenciou na validação), exceto para parados.
    deals["valor"] = deals["sales_price"]
    deals["chance"] = np.where(deals["parado"], config.CHANCE_PARADO, estat.taxa_vitoria_geral)
    deals["valor_esperado"] = deals["chance"] * deals["valor"]

    deals["motivo_principal"] = deals.apply(lambda d: motivo_principal(d, estat), axis=1)
    return deals.sort_values(["score", "valor"], ascending=False).reset_index(drop=True)


@lru_cache(maxsize=1)
def pontuar_deals_abertos() -> pd.DataFrame:
    """Negócios abertos de hoje, pontuados e ordenados do mais para o menos prioritário."""
    deals = carregar_deals()
    abertos = deals[deals["deal_stage"].isin(ETAPAS_ABERTAS)]
    return pontuar(abertos, calcular_estatisticas(), obter_data_referencia())


# ---------------------------------------------------------------------------
# Explicações em linguagem simples
# ---------------------------------------------------------------------------

def _formatar_moeda(valor: float) -> str:
    """Formata em dólar no padrão brasileiro: US$ 5.482."""
    return "US$ " + f"{valor:,.0f}".replace(",", ".")


def _na_reta_final(deal: pd.Series) -> bool:
    return deal["situacao"] == SITUACAO_ATIVO and deal["fator_reta_final"] >= INICIO_RETA_FINAL


def motivo_principal(deal: pd.Series, estat: EstatisticasHistoricas) -> str:
    """Frase curta para o cartão: o ponto forte (prioridade alta) ou o que segurou a nota."""
    valor = _formatar_moeda(deal["sales_price"])

    if deal["parado"]:
        return f"Parado há {deal['dias_aberto']:.0f} dias: fora do padrão"
    if deal["prioridade"] == PRIORIDADE_ALTA:
        if deal["fator_valor"] >= 0.65:
            return f"Alto valor ({valor})"
        if _na_reta_final(deal):
            return f"Reta final: dia {deal['dias_aberto']:.0f} de até {estat.limite_dias}"
        return f"Negociação ativa no prazo ({deal['dias_aberto']:.0f} dias)"
    if deal["fator_valor"] < 0.5:
        return f"Valor baixo ({valor})"
    if deal["situacao"] == SITUACAO_PROSPECCAO:
        return "Negociação ainda não começou"
    return f"Início da negociação ({deal['dias_aberto']:.0f} dias)"


@dataclass(frozen=True)
class ParteExplicada:
    """Quanto uma parte contribuiu para o score e por quê."""

    chave: str
    nome: str
    pontos: int
    maximo: int
    explicacao: str


def explicar_partes(deal: pd.Series) -> list[ParteExplicada]:
    """Detalha os pontos de cada parte. A soma dos pontos é o score do negócio."""
    estat = calcular_estatisticas()
    limite = estat.limite_dias
    dias = deal["dias_aberto"]

    if deal["situacao"] == SITUACAO_PROSPECCAO:
        situacao = "Em prospecção: a negociação ainda não começou, por isso vale metade dos pontos"
        reta = "Ainda não começou a contar: o prazo corre a partir do início da negociação"
    elif deal["parado"]:
        situacao = (
            f"Aberto há {dias:.0f} dias. Nenhum negócio do histórico, ganho ou perdido, "
            f"ficou aberto mais de {limite} dias: este provavelmente foi abandonado"
        )
        reta = f"Já passou do prazo de {limite} dias"
    else:
        situacao = f"Em negociação há {dias:.0f} dias, dentro do prazo em que os negócios se resolvem (até {limite} dias)"
        reta = f"Dia {dias:.0f} de até {limite}: quanto mais perto do prazo, mais urgente conduzir à decisão"

    explicacoes = {
        "situacao": situacao,
        "valor": (
            f"Preço de {_formatar_moeda(deal['sales_price'])}. Os produtos vão de "
            f"{_formatar_moeda(estat.preco_minimo)} a {_formatar_moeda(estat.preco_maximo)}"
        ),
        "reta_final": reta,
    }

    return [
        ParteExplicada(
            chave=parte,
            nome=NOMES_PARTES[parte],
            pontos=int(deal[f"pontos_{parte}"]),
            maximo=config.PONTOS_MAXIMOS[parte],
            explicacao=explicacoes[parte],
        )
        for parte in PARTES
    ]


@dataclass(frozen=True)
class Motivo:
    """Uma frase explicando algo que pesou no score."""

    texto: str
    tipo: str  # "positivo", "negativo" ou "neutro"


def explicar_deal(deal: pd.Series) -> list[Motivo]:
    """Lista os motivos que explicam o score de um negócio, do mais ao menos importante."""
    estat = calcular_estatisticas()
    limite = estat.limite_dias
    motivos: list[Motivo] = []

    # Situação: o sinal mais forte encontrado nos dados.
    if deal["parado"]:
        motivos.append(Motivo(
            f"Parado há {deal['dias_aberto']:.0f} dias: nenhum negócio do histórico ficou aberto "
            f"mais de {limite} dias, e nenhum que passou disso foi fechado depois",
            "negativo",
        ))
    elif deal["situacao"] == SITUACAO_PROSPECCAO:
        motivos.append(Motivo("Ainda em prospecção: a negociação não começou", "neutro"))
    elif _na_reta_final(deal):
        motivos.append(Motivo(
            f"Na reta final: está no dia {deal['dias_aberto']:.0f}, e os negócios se resolvem "
            f"em até {limite} dias",
            "positivo",
        ))
    else:
        motivos.append(Motivo(f"Negociação ativa, dentro do prazo ({deal['dias_aberto']:.0f} dias)", "positivo"))

    # Valor.
    valor = _formatar_moeda(deal["sales_price"])
    if deal["fator_valor"] >= 0.65:
        motivos.append(Motivo(f"Alto valor: {valor}", "positivo"))
    elif deal["fator_valor"] < 0.5:
        motivos.append(Motivo(f"Valor baixo: {valor}", "negativo"))

    # Chance: igual para todos os negócios vivos (explicado para evitar "achismo").
    if not deal["parado"]:
        motivos.append(Motivo(
            f"Chance de fechar: {estat.taxa_vitoria_geral:.0%}, a média da empresa. No histórico, "
            "vendedor, produto, setor e conta não mudaram a chance de ganhar",
            "neutro",
        ))

    if not deal["conta_informada"]:
        motivos.append(Motivo("Conta não informada: complete o cadastro no CRM", "neutro"))

    return motivos


def sugerir_acao(deal: pd.Series) -> str:
    """Recomendação direta para o vendedor."""
    if deal["parado"]:
        return (
            "Atualize ou encerre: confirme com o cliente se ainda há interesse. "
            "Se não houver, marque como perdido para limpar o pipeline."
        )
    if deal["prioridade"] == PRIORIDADE_ALTA:
        if _na_reta_final(deal):
            return "Priorize agora: negócio ativo perto do prazo de decisão. Conduza o cliente ao fechamento."
        return "Priorize: negócio ativo, dentro do prazo e com valor relevante. Dedique tempo a ele agora."
    if deal["situacao"] == SITUACAO_PROSPECCAO and deal["prioridade"] == PRIORIDADE_MEDIA:
        return "Avance: faça o primeiro contato para iniciar a negociação."
    if deal["prioridade"] == PRIORIDADE_MEDIA:
        return "Mantenha o acompanhamento regular."
    return "Baixa prioridade: dedique tempo depois dos negócios prioritários."


def regras_pontuacao() -> dict:
    """Regras atuais do score, para a tela "Como funciona a pontuação"."""
    estat = calcular_estatisticas()
    return {
        "pontos_maximos": config.PONTOS_MAXIMOS,
        "pontos_prospeccao": round(config.PONTOS_MAXIMOS["situacao"] * config.FRACAO_SITUACAO_PROSPECCAO),
        "limite_alta": config.LIMITE_PRIORIDADE_ALTA,
        "limite_media": config.LIMITE_PRIORIDADE_MEDIA,
        "taxa_vitoria_geral": round(estat.taxa_vitoria_geral, 4),
        "ciclo_mediano_dias": estat.ciclo_mediano_dias,
        "limite_dias": estat.limite_dias,
        "preco_minimo": estat.preco_minimo,
        "preco_maximo": estat.preco_maximo,
    }
