"""Testes automáticos do motor do Lead Scorer.

Rodar:  python -m pytest -v tests/   (de dentro da pasta solution/motor)
Cada teste confere uma regra aprovada (docs/ficha-da-logica.md) ou uma garantia de qualidade.
"""
import copy
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

AQUI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AQUI))
import gerar_scores as m  # noqa: E402

DADOS = AQUI.parent / "data"
CONFIG = AQUI / "config.json"

# Números da configuração aprovada (Registro 08). Mudou a configuração? Atualize aqui e registre no log.
NUM_FOCO, NUM_REQ, NUM_INICIAR, NUM_AUTO = 228, 1301, 500, 60
NUM_LIGAR, NUM_ENCERRAR = 354, 947


@pytest.fixture(scope="module")
def cfg():
    return m.carregar_config(CONFIG)


@pytest.fixture(scope="module")
def base(cfg):
    return m.carregar_dados(DADOS, cfg)


@pytest.fixture(scope="module")
def resultado():
    return m.gerar(DADOS, CONFIG)


@pytest.fixture(scope="module")
def deals(resultado):
    return pd.DataFrame(resultado["deals"])


# ------------------------------------------------------------------ cobertura e textos
def test_todo_deal_aberto_recebe_exatamente_uma_lista(deals):
    bruto = pd.read_csv(DADOS / "sales_pipeline.csv")
    abertos = bruto[bruto.deal_stage.isin(["Engaging", "Prospecting"])]
    assert len(deals) == len(abertos) == 2089, "nem todo deal aberto foi classificado"
    assert deals.id.is_unique, "deal repetido na saída"
    assert set(deals.lista) == set(m.ORDEM_LISTAS)


def test_todo_deal_tem_acao_porque_e_texto_da_nota(deals):
    for col in ["acao", "porque", "nota_texto"]:
        vazios = deals[col].isna() | (deals[col].str.strip() == "")
        assert not vazios.any(), f"{vazios.sum()} deals sem '{col}'"
    textos = deals.acao + " " + deals.porque + " " + deals.nota_texto
    assert not textos.str.contains(r"\bnan\b|\bNone\b|\bNaN\b", regex=True).any(), "texto com valor vazio aparente"


def test_aviso_de_empresa_aparece_em_todas_as_listas_quando_falta_empresa(deals):
    sem = deals.empresa.isna()
    assert (deals.loc[sem, "aviso"] == "Empresa não cadastrada: complete o cadastro no CRM").all()
    assert deals.loc[~sem, "aviso"].isna().all()
    assert deals.loc[sem, "lista"].nunique() == 4, "aviso deve valer nas 4 listas (decisão do Registro 06)"


# ------------------------------------------------------------------ regras das listas
def test_regras_das_4_listas(deals, resultado, cfg):
    lim = resultado["limite_ciclo_dias"]
    foco = deals[deals.lista == "Foco"]
    assert (foco.idade_dias <= lim).all() and (foco.preco_usd >= cfg["valor_minimo_foco_usd"]).all()
    req = deals[deals.lista == "Requalificar ou encerrar"]
    if cfg["mover_chance_zero_para_requalificar"]:
        assert ((req.idade_dias > lim) | (req.chance == 0)).all()
        assert not ((foco.chance == 0).any()), "deal com chance 0% não pode ficar no Foco"
    else:
        assert (req.idade_dias > lim).all()
    assert ((req.acao == "Ligar para requalificar") == (req.preco_usd >= cfg["valor_deal_grande_usd"])).all()
    ini = deals[deals.lista == "Iniciar contato"]
    assert (ini.etapa == "Prospecção").all() and ini.chance.isna().all() and ini.nota.isna().all()
    auto = deals[deals.lista == "Automatizar"]
    assert (auto.preco_usd < cfg["valor_minimo_foco_usd"]).all() and (auto.idade_dias <= lim).all()


def test_nota_existe_so_no_foco_e_segue_o_valor_esperado(deals):
    foco = deals[deals.lista == "Foco"].sort_values("ordem_na_lista")
    assert foco.nota.between(0, 100).all() and foco.nota.max() == 100 and foco.nota.min() == 0
    assert deals[deals.lista != "Foco"].nota.isna().all()
    assert foco.valor_esperado_usd.is_monotonic_decreasing, "Foco fora da ordem de valor esperado"
    assert foco.nota.is_monotonic_decreasing


def test_valor_esperado_e_a_conta_chance_vezes_preco(deals):
    f = deals[deals.lista.isin(["Foco", "Automatizar"])]
    assert np.allclose(f.valor_esperado_usd, f.chance * f.preco_usd, atol=1.0)


# ------------------------------------------------------------------ números aprovados
def test_numeros_batem_com_a_ficha_aprovada(resultado, deals):
    r = resultado["resumo_por_lista"]
    # Registro 08: os 10 deals de 138 dias (chance 0%) saíram do Foco (8) e do Automatizar (2) para Requalificar
    assert [r[l]["deals"] for l in m.ORDEM_LISTAS] == [NUM_FOCO, NUM_REQ, NUM_INICIAR, NUM_AUTO]
    assert (deals.acao == "Ligar para requalificar").sum() == NUM_LIGAR
    assert (deals.acao == "Encerrar no CRM").sum() == NUM_ENCERRAR
    assert resultado["limite_ciclo_dias"] == 138
    curva = {c["idade_dias"]: c["chance"] for c in resultado["curva_chance"]}
    assert round(curva[0], 3) == 0.473 and round(curva[90], 3) == 0.262 and curva[138] == 0


def test_volta_no_tempo_reproduz_o_resultado_da_fase_2(resultado):
    v = resultado["validacao_volta_no_tempo"]
    assert v["deals_em_negociacao"] == 2409
    assert 0.66 <= v["captura_top20_nossa_logica"] <= 0.70
    assert v["captura_top20_nossa_logica"] > v["captura_top20_so_valor"] + 0.15


# ------------------------------------------------------------------ garantias
def test_sem_vazamento_de_futuro_sabotando_tudo_que_aconteceu_depois(base, cfg):
    """Se trocarmos ao acaso tudo o que aconteceu depois de 30/09/2017 (quem ganhou, quem perdeu,
    datas e valores), a priorização feita em 30/09 tem que continuar idêntica."""
    corte = pd.Timestamp("2017-09-30")
    original, _ = m.classificar(m.visao_na_data(base, corte), corte, cfg)

    sab = base.copy()
    rng = np.random.default_rng(7)
    depois = sab.close_date > corte
    sab.loc[depois, "deal_stage"] = rng.choice(["Won", "Lost"], depois.sum())
    sab.loc[depois, "close_value"] = rng.integers(1, 99999, depois.sum())
    sab.loc[depois, "close_date"] = corte + pd.to_timedelta(rng.integers(1, 90, depois.sum()), unit="D")
    novos = sab.engage_date > corte
    sab.loc[novos, "sales_price"] = 999999
    sabotado, _ = m.classificar(m.visao_na_data(sab, corte), corte, cfg)

    cols = ["opportunity_id", "lista", "acao", "nota", "valor_esperado", "porque"]
    pd.testing.assert_frame_equal(original[cols].reset_index(drop=True), sabotado[cols].reset_index(drop=True))


def test_mudar_a_configuracao_muda_o_resultado_sem_mexer_no_codigo(base, cfg):
    data_ref = pd.Timestamp(cfg["data_referencia"])
    c2 = copy.deepcopy(cfg); c2["valor_deal_grande_usd"] = 1000; c2["valor_minimo_foco_usd"] = 600
    c2["mover_chance_zero_para_requalificar"] = False  # mesma regra usada nos Registros 04 e 05
    d2, _ = m.classificar(m.visao_na_data(base, data_ref), data_ref, c2)
    assert (d2.acao == "Ligar para requalificar").sum() == 766   # números do Registro 04 (limite provisório)
    assert (d2.lista == "Foco").sum() == 178                     # opção "US$ 600" do Registro 05


def test_nenhum_nome_de_produto_escrito_no_codigo():
    codigo = (AQUI / "gerar_scores.py").read_text(encoding="utf-8")
    produtos = pd.read_csv(DADOS / "products.csv")["product"].tolist() + ["GTXPro"]
    achados = [p for p in produtos if re.search(re.escape(p), codigo)]
    assert not achados, f"nome de produto no código (deveria estar na config): {achados}"


def test_saida_json_valida_para_a_tela(resultado):
    txt = json.dumps(resultado, ensure_ascii=False)
    assert json.loads(txt)["deals"][0]["lista"] == "Foco"
    assert len(resultado["vendedores"]) == 35

def test_chance_texto_igual_ao_texto_do_porque(deals):
    """A tela mostra 'chance_texto'; ele precisa ser idêntico à chance citada no 'porquê' (Registro 10)."""
    assert deals[deals.chance.notna()].chance_texto.notna().all()
    c = deals[deals.lista.isin(["Foco", "Automatizar"])]  # as listas em que a tela mostra a chance
    assert all(f"{ct} de chance" in pq for ct, pq in zip(c.chance_texto, c.porque))
    assert deals[deals.chance.isna()].chance_texto.isna().all()
