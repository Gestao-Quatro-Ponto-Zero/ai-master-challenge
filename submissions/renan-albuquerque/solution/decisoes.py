"""Guarda as decisões do vendedor (Manter / Encerrar / Recomeçar) num CSV e
aplica essas decisões aos dados antes do cálculo do score.

O CRM não tem nenhuma coluna de último contato. Cada clique em "Manter"
passa a ser esse registro: a ferramenta gera o dado que faltava.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd

from dados import DATA_REFERENCIA

ARQUIVO = Path(__file__).parent / "decisoes.csv"
COLUNAS = ["opportunity_id", "acao", "idade_na_decisao", "registrado_em"]

MANTER = "manter"
ENCERRAR = "encerrar"
RECOMECAR = "recomecar"


def carregar() -> pd.DataFrame:
    if not ARQUIVO.exists():
        return pd.DataFrame(columns=COLUNAS)
    return pd.read_csv(ARQUIVO)


def salvar(opportunity_id: str, acao: str, idade: int) -> None:
    novas = carregar()
    novas = novas[novas["opportunity_id"] != opportunity_id]  # vale a decisão mais recente
    linha = pd.DataFrame([{
        "opportunity_id": opportunity_id,
        "acao": acao,
        "idade_na_decisao": idade,
        # Data real do clique, para auditoria. O cálculo usa DATA_REFERENCIA.
        "registrado_em": datetime.now().isoformat(timespec="seconds"),
    }])
    pd.concat([novas, linha], ignore_index=True).to_csv(ARQUIVO, index=False)


def remover(opportunity_id: str) -> None:
    """Desfaz a decisão de um deal (botão "Desfazer")."""
    restantes = carregar()
    restantes[restantes["opportunity_id"] != opportunity_id].to_csv(ARQUIVO, index=False)


def apagar_tudo() -> None:
    ARQUIVO.unlink(missing_ok=True)


def aplicar(df: pd.DataFrame, decisoes: pd.DataFrame) -> pd.DataFrame:
    """Devolve uma cópia dos dados com as decisões aplicadas."""
    df = df.copy()
    df["decisao"] = None
    df["idade_antes"] = None
    for _, d in decisoes.iterrows():
        linha = df["opportunity_id"] == d["opportunity_id"]
        df.loc[linha, "decisao"] = d["acao"]
        df.loc[linha, "idade_antes"] = d["idade_na_decisao"]
        if d["acao"] == MANTER:
            # Contato confirmado "hoje": a idade volta a contar a partir daqui.
            df.loc[linha, "engage_date"] = DATA_REFERENCIA
        elif d["acao"] == ENCERRAR:
            # Sai do pipeline, mas NÃO entra no histórico de perdidos:
            # um deal de 400 dias como "perdido" distorceria a curva de idade.
            df.loc[linha, "deal_stage"] = "Encerrado manualmente"
        elif d["acao"] == RECOMECAR:
            df.loc[linha, "deal_stage"] = "Prospecting"
            df.loc[linha, "engage_date"] = pd.NaT
    df["idade_dias"] = (DATA_REFERENCIA - df["engage_date"]).dt.days
    return df
