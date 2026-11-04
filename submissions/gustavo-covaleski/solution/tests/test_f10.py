import json
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from comum import OUT_DIR, SUBMISSAO, ler_ds1, ler_ds2  # noqa: E402

DATA_JS = SUBMISSAO / "console" / "data.js"


@pytest.fixture(scope="module")
def bruto():
    return DATA_JS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dados(bruto):
    m = re.fullmatch(r"window\.DADOS = (.*);\s*", bruto, flags=re.S)
    assert m, "data.js fora do formato window.DADOS = {...};"
    return json.loads(m.group(1))


def test_data_js_valido(dados):
    for chave in ("meta", "politicas", "fila", "ataques", "governanca", "kpis"):
        assert chave in dados
    assert set(dados["politicas"]) == {"F9", "F8", "F4"}


def test_fila_300_em_20_dias(dados):
    fila = dados["fila"]
    assert len(fila) == 300 and len({t["id"] for t in fila}) == 300
    assert sorted({t["dia"] for t in fila}) == list(range(1, 21))
    assert all(sum(t["dia"] == d for t in fila) == 15 for d in range(1, 21))
    assert len(dados["ataques"]) == 300 and all(len(v) == 5 for v in dados["ataques"].values())


def test_checagem_dia_20(dados):
    tab = pd.read_csv(OUT_DIR / "f8_politica_por_categoria.csv")
    ult = dados["governanca"][-1]
    for r in tab.itertuples():
        if r.politica_implantada == "IA decide":
            assert ult["categorias"][r.categoria_prevista]["li"] == pytest.approx(r.li_ia_decide, abs=1e-4)
    fx = json.loads((OUT_DIR / "f8_faixas.json").read_text(encoding="utf-8"))
    cob = 100 * ult["faixas"]["F9"]["IA decide"]["n"] / ult["n_total"]
    assert cob == pytest.approx(fx["implantada"]["faixas"]["IA decide"]["cobertura_pct"], abs=0.005)
    assert ult["n_total"] == 9567


def test_sem_nome_ou_email_do_ds1(bruto):
    d1 = ler_ds1()
    assert not any(n in bruto for n in d1["Customer Name"])
    assert not any(e in bruto for e in d1["Customer Email"])


def test_texto_so_dos_300_ids_da_fila(dados, bruto):
    def ng(ws, n=8):
        return {" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)}
    ids = {t["id"] for t in dados["fila"]}
    ds2 = ler_ds2()
    fora = set()
    for doc in ds2.loc[~ds2["id"].isin(ids), "Document"].dropna():
        fora |= ng(str(doc).split())
    # tira da busca os 8-gramas que também existem em algum dos 300 (quase-duplicados legítimos)
    dentro = set()
    for doc in ds2.loc[ds2["id"].isin(ids), "Document"].dropna():
        dentro |= ng(str(doc).split())
    texto = re.sub(r"[^\w]+", " ", bruto.lower()).split()
    vazados = [g for g in ng(texto) if g in fora and g not in dentro]
    assert not vazados, vazados[:3]
