import io
import json
import os
import re
from pathlib import Path

import pandas as pd

SUBMISSAO = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("DATA_DIR", SUBMISSAO / "../../../data")).resolve()
PLANNING_DIR = (SUBMISSAO / "../../../planning").resolve()
# chave de API fica fora do repositório, em challenge-g4-ai-master/.env
ENV_PATH = (SUBMISSAO / "../../../.env").resolve()
REVISAO_DIR = PLANNING_DIR / "F1-revisao"
F3_DIR = PLANNING_DIR / "F3"
OUT_DIR = SUBMISSAO / "solution" / "outputs"
PROCESS_LOG_DIR = SUBMISSAO / "process-log"
SEED = 42

DS1_ARQUIVO = "customer_support_tickets.csv"
DS2_ARQUIVO = "all_tickets_processed_improved_v3.csv"


def ler_ds1() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / DS1_ARQUIVO)


def ler_ds2() -> pd.DataFrame:
    # id = índice da linha no CSV original (base 0); nunca reordenar antes de atribuir.
    df = pd.read_csv(DATA_DIR / DS2_ARQUIVO)
    df.insert(0, "id", range(len(df)))
    return df


def normalizar(texto) -> str:
    t = str(texto).lower() if isinstance(texto, str) else ""
    t = re.sub(r"\d", "0", t)
    t = re.sub(r"[\W_]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def salvar_json(obj, nome: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    p = OUT_DIR / nome
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=_conv), encoding="utf-8")
    return p


def salvar_csv_excel(df: pd.DataFrame, caminho: Path) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, sep=";", index=False, encoding="utf-8-sig")
    return caminho


def ler_csv_excel(caminho: Path) -> pd.DataFrame:
    # o Excel (desktop ou online) pode devolver `,` e cp1252 em vez do `;` + UTF-8 com BOM que gravamos
    bruto = Path(caminho).read_bytes()
    for cod in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            texto = bruto.decode(cod)
            break
        except UnicodeDecodeError:
            continue
    cabecalho = texto.split("\n", 1)[0]
    sep = ";" if cabecalho.count(";") >= cabecalho.count(",") else ","
    return pd.read_csv(io.StringIO(texto), sep=sep, dtype=str, keep_default_na=False)


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    centro = (p + z * z / (2 * n)) / (1 + z * z / n)
    meia = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return (centro - meia, centro + meia)


def boot_ic(y, pred, metrica, n_boot=1000, seed=SEED):
    import numpy as np
    y, pred = np.asarray(y), np.asarray(pred)
    rng = np.random.default_rng(seed)
    vals = [metrica(y[i], pred[i]) for i in (rng.integers(0, len(y), len(y)) for _ in range(n_boot))]
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def ler_env_chave(nome="ANTHROPIC_API_KEY"):
    # lida do .env fora do repositório; nunca imprimir nem logar o valor
    if not ENV_PATH.exists():
        return None
    for linha in ENV_PATH.read_text(encoding="utf-8-sig").splitlines():
        if "=" in linha and linha.split("=", 1)[0].strip() == nome:
            v = linha.split("=", 1)[1].strip().strip('"').strip("'")
            return v or None
    return None


def _conv(o):
    if hasattr(o, "item"):
        return o.item()
    return str(o)
