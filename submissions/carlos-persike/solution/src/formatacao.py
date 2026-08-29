"""Formatação de números em pt-BR (ponto como separador de milhar, vírgula decimal).
O Streamlit não tem um formato de coluna "pt-BR" confiável — o preset "localized"
depende do locale do navegador de quem está vendo, não é determinístico. Por isso
formatamos como string aqui em vez de confiar em column_config para moeda.
"""


def moeda_brl(valor: float) -> str:
    """R$ 26.768 — sem centavos, ponto como separador de milhar."""
    texto = f"{valor:,.0f}".replace(",", ".")
    return f"R$ {texto}"


def moeda_brl_milhoes(valor_em_milhoes: float) -> str:
    """R$ 251,4 milhões — a coluna 'revenue' do dataset já vem em milhões de USD."""
    texto = f"{valor_em_milhoes:.1f}".replace(".", ",")
    return f"R$ {texto} milhões"
