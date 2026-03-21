"""Linguagem comercial para explicações do score (CRP-FIN-06 / FIN-07)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.scoring.engine import ScoreResult


@dataclass(frozen=True)
class _Ctx:
    opportunity_id: str
    deal_stage: str

    def pick(self, *phrases: str) -> str:
        if len(phrases) == 1:
            return phrases[0]
        h = abs(hash(f"{self.opportunity_id}:{phrases[0]}")) % len(phrases)
        return phrases[h]


def _map_line(line: str, ctx: _Ctx) -> str:
    m = re.match(r"^deal_stage (\w+) contribuiu \+(\d+)\.$", line)
    if m:
        st, d = m.group(1), m.group(2)
        if st == "Won":
            return ctx.pick(
                f"Negócio já ganho elevou a prioridade neste ranking (+{d}).",
                f"Estado comercial «ganho» confirma conversão e reforça o score (+{d}).",
                f"Fecho positivo registado: o histórico ganho pesa a favor (+{d}).",
            )
        if st == "Engaging":
            return ctx.pick(
                f"Negócio em fase de engajamento ativo aumentou a prioridade (+{d}).",
                f"Avanço para engajamento comercial foi valorizado no score (+{d}).",
            )
        if st == "Prospecting":
            return ctx.pick(
                f"Prospecção ainda em curso contribui moderadamente (+{d}).",
                f"Topo de funil (prospecção) entrou no cálculo com peso positivo (+{d}).",
            )
        return f"O estágio «{st}» influenciou o score (+{d})."

    m = re.match(r"^deal_stage (\w+) contribuiu (-?\d+)\.$", line)
    if m:
        st, d = m.group(1), m.group(2)
        if st == "Lost":
            return ctx.pick(
                f"Negócio marcado como perdido reduz a prioridade ({d}).",
                f"Estado «perdido» puxa o score para baixo ({d}).",
            )
        return f"O estágio «{st}» puxou o score ({d})."

    if line.startswith("deal_stage fora do mapeamento"):
        return ctx.pick(
            "Estágio comercial não mapeado nas regras: sem bónus de maturidade.",
            "Estágio fora do catálogo esperado; prioridade não foi ajustada por maturidade.",
        )

    if line == "close_value alto elevou prioridade.":
        return ctx.pick(
            "Valor de negócio elevado aumentou a priorização.",
            "Ticket alto reforça o potencial comercial no score.",
        )
    if line == "close_value medio trouxe bonus moderado.":
        return ctx.pick(
            "Valor médio do negócio trouxe um reforço moderado à prioridade.",
            "Ticket intermédio acrescentou peso positivo equilibrado.",
        )
    if line == "close_value baixo sem bonus de valor.":
        return ctx.pick(
            "Valor ainda modesto não acrescenta bónus de montante.",
            "Ticket baixo não impulsiona o score pelo critério de valor.",
        )

    if "idade no pipeline" in line and "fresh" in line:
        return ctx.pick(
            "Entrada recente no pipeline: boa cadência comercial.",
            "Recência desde o engajamento favorece a prioridade.",
        )
    if "idade no pipeline" in line and "stale" in line:
        return ctx.pick(
            "Tempo longo no pipeline sem fecho reduz urgência operacional.",
            "Negócio aberto há muito tempo sem desfecho penaliza o score.",
        )
    if "idade no pipeline" in line and "active" in line:
        return ctx.pick(
            "Maturidade média no pipeline: ajuste moderado ao score.",
            "Pipeline em ritmo intermédio desde o engajamento.",
        )

    m = re.match(r"^stage_rank (\d+) afinou ([+-]?\d+)\.$", line)
    if m:
        return f"Subestágio (rank {m.group(1)}) afinou o resultado ({m.group(2)})."

    m = re.match(r"^conta (\w+) por receita \(\+(\d+)\)\.$", line)
    if m:
        return ctx.pick(
            f"Porte da conta por receita ({m.group(1)}) reforçou a prioridade (+{m.group(2)}).",
            f"Conta classificada como {m.group(1)} por receita aumentou o score (+{m.group(2)}).",
        )

    m = re.match(r"^receita da conta desconhecida ou baixa \((\w+)\) (-?\d+)\.$", line)
    if m:
        return "Dados de receita incompletos ou fracos reduzem confiança no registro."

    m = re.match(r"^porte por headcount (\w+) \(\+(\d+)\)\.$", line)
    if m:
        return (
            f"Dimensão da equipa na conta ({m.group(1)}) contribuiu positivamente (+{m.group(2)})."
        )

    m = re.match(r"^headcount desconhecido \((\w+)\) (-?\d+)\.$", line)
    if m:
        return "Número de colaboradores da conta ausente: sinal de cadastro incompleto."

    m = re.match(r"^serie de produto (\w+) \(\+(\d+)\)\.$", line)
    if m:
        return f"A linha de produto ({m.group(1)}) é vista como favorável (+{m.group(2)})."

    m = re.match(r"^serie de produto (\w+) (-?\d+)\.$", line)
    if m:
        return f"A linha ({m.group(1)}) não acrescenta bónus neste contexto ({m.group(2)})."

    if line == "preco de lista do produto elevado reforcou prioridade.":
        return "Preço de catálogo elevado reforça o valor potencial do negócio."
    if line == "preco de lista do produto moderado trouxe bonus leve.":
        return "Preço de lista moderado acrescenta um impulso leve."

    m = re.match(r"^regiao comercial (\w+) \(\+(\d+)\)\.$", line)
    if m:
        return f"Região comercial ({m.group(1)}) entrou como fator de ajuste (+{m.group(2)})."

    if "escritorio regional identificado" in line:
        return ctx.pick(
            "Escritório regional identificado: melhor completude de equipa.",
            "Dados de escritório preenchidos reforçam rastreabilidade comercial.",
        )

    if line == "manager atribuido (completude de equipe).":
        return ctx.pick(
            "Gestor comercial atribuído: cadastro de equipa mais completo.",
            "Há gestor nomeado, o que melhora a governança do registro.",
        )

    m = re.match(r"^data de engage ausente ou invalida \((-?\d+)\)\.$", line)
    if m:
        return ctx.pick(
            "Data de engajamento ausente ou inválida reduz fiabilidade do pipeline.",
            "Sem engage_date consistente, a idade no funil é menos confiável.",
        )

    m = re.match(r"^oportunidade terminal sem close_date \((-?\d+)\)\.$", line)
    if m:
        return "Negócio fechado sem data de fecho: qualidade de registro a melhorar."

    if "close_date presente para oportunidade fechada" in line:
        return ctx.pick(
            "Data de fecho registada: melhor qualidade de dados em negócio terminal.",
            "Registo de fecho completo aumenta confiança no histórico.",
        )

    m = re.match(r"^account ausente aplicou penalidade (-?\d+)\.$", line)
    if m:
        return ctx.pick(
            f"Conta não associada penaliza a prioridade ({m.group(1)}).",
            "Sem conta vinculada, a ação comercial fica menos direcionada.",
        )

    if line.startswith("Prospecção com ticket ainda baixo"):
        return line

    return line


def _map_risk(line: str, ctx: _Ctx) -> str:
    if "taxonomia de estagio divergente" in line:
        return ctx.pick(
            "Risco: estágio comercial pode não seguir o dicionário esperado.",
            "Verificar alinhamento do estágio ao modelo oficial do desafio.",
        )
    if "engage_date confiavel" in line:
        return "Risco operacional: sem data de engajamento fiável, o timing é aproximado."
    if "Registro sem account" in line:
        return "Risco: falta de conta dificulta priorização por cliente."
    return line


def humanize_score_explanations(
    result: ScoreResult,
    *,
    deal_stage: str,
    opportunity_id: str = "",
) -> tuple[list[str], list[str], list[str]]:
    ctx = _Ctx(opportunity_id=opportunity_id or "unknown", deal_stage=deal_stage or "")
    pos = [_map_line(p, ctx) for p in result.positives]
    neg = [_map_line(n, ctx) for n in result.negatives]
    risks = [_map_risk(r, ctx) for r in result.risks]
    return pos, neg, risks
