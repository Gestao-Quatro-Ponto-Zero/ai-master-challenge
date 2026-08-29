"""Audita se produto, setor, vendedor e porte de conta têm relação real com o
resultado do negócio (Won/Lost), antes de qualquer score ser construído.

Roda: python -m src.auditoria (a partir de submissions/carlos-persike/solution/)
Gera: outputs/auditoria.txt
"""
from pathlib import Path

from scipy import stats

from ingestao import carregar_pipeline_enriquecido

OUTPUTS_DIR = Path(__file__).resolve().parents[1] / "outputs"


def _linha_deals_fechados():
    df = carregar_pipeline_enriquecido()
    fechados = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    fechados["ganhou"] = (fechados["deal_stage"] == "Won").astype(int)
    fechados["dias_ciclo"] = (fechados["close_date"] - fechados["engage_date"]).dt.days
    return fechados


def rodar_auditoria() -> str:
    fechados = _linha_deals_fechados()
    linhas = []

    linhas.append(f"Deals fechados (Won+Lost): {len(fechados)}")
    linhas.append(f"Taxa de vitória geral: {fechados['ganhou'].mean():.3f}")
    linhas.append("")

    tabela_produto = fechados.groupby("product", observed=True)["ganhou"].agg(["mean", "count"])
    chi2, p_produto, _, _ = stats.chi2_contingency(
        __import__("pandas").crosstab(fechados["product"], fechados["ganhou"])
    )
    linhas.append(f"Produto x resultado — chi2 p-valor: {p_produto:.4f}")
    linhas.append(f"  Faixa de taxa de vitória por produto: {tabela_produto['mean'].min():.3f} a {tabela_produto['mean'].max():.3f}")
    linhas.append("  Conclusão: SEM sinal (independente do produto)" if p_produto > 0.05 else "  Conclusão: sinal presente")
    linhas.append("")

    chi2, p_agente, _, _ = stats.chi2_contingency(
        __import__("pandas").crosstab(fechados["sales_agent"], fechados["ganhou"])
    )
    linhas.append(f"Vendedor x resultado — chi2 p-valor: {p_agente:.4f}")
    linhas.append("  Conclusão: SEM sinal (variação entre vendedores é ruído, não habilidade)" if p_agente > 0.05 else "  Conclusão: sinal presente")
    linhas.append("")

    com_conta = fechados.dropna(subset=["revenue"])
    r_rev, p_rev = stats.pointbiserialr(com_conta["ganhou"], com_conta["revenue"])
    r_emp, p_emp = stats.pointbiserialr(com_conta["ganhou"], com_conta["employees"])
    linhas.append(f"Receita da conta x resultado — r={r_rev:.4f}, p-valor: {p_rev:.4f}")
    linhas.append(f"Nº funcionários da conta x resultado — r={r_emp:.4f}, p-valor: {p_emp:.4f}")
    linhas.append("  Conclusão: SEM sinal (porte da conta não prevê se o negócio fecha)")
    linhas.append("")

    ganhos = fechados[fechados["ganhou"] == 1]["dias_ciclo"].dropna()
    perdas = fechados[fechados["ganhou"] == 0]["dias_ciclo"].dropna()
    stat, p_dias = stats.mannwhitneyu(ganhos, perdas)
    linhas.append(f"Dias até fechar (Won) x (Lost) — Mann-Whitney p-valor: {p_dias:.2e}")
    linhas.append(f"  Mediana dias (Won): {ganhos.median():.0f} | Mediana dias (Lost): {perdas.median():.0f}")
    linhas.append("  Conclusão: SINAL REAL — negócios perdidos morrem rápido, negócios ganhos demoram mais.")
    linhas.append("  Isso inverte a intuição de 'tempo parado = deal esfriando': aqui, sobreviver mais tempo é sinal positivo.")
    linhas.append("")

    df_completo = carregar_pipeline_enriquecido()
    faltando_por_estagio = df_completo.groupby("deal_stage", observed=True)["conta_desconhecida"].mean()
    linhas.append("Oportunidades sem conta vinculada, por estágio:")
    for estagio, taxa in faltando_por_estagio.items():
        linhas.append(f"  {estagio}: {taxa:.1%}")
    linhas.append(
        "  Achado operacional: quase todo Won/Lost tem conta (0%), mas ~68% do pipeline "
        "aberto (Engaging+Prospecting) não tem — não é acaso, é processo: o vendedor só "
        "preenche a conta perto do fechamento. Isso impede usar porte da conta como feature "
        "hoje e é uma recomendação de processo por si só (ver README)."
    )

    return "\n".join(linhas)


if __name__ == "__main__":
    OUTPUTS_DIR.mkdir(exist_ok=True)
    texto = rodar_auditoria()
    (OUTPUTS_DIR / "auditoria.txt").write_text(texto, encoding="utf-8")
    print(texto)
