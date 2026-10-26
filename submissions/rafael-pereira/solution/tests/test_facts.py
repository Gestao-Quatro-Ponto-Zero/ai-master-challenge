"""Testes dos fatos: os números da fase 0 e as evidências das investigações 2a, 2b e 2c."""

import math

import pytest

from scorer import clean, config, facts


@pytest.fixture(scope="module")
def built():
    raw = clean.load_raw(config.RAW_DIR)
    deals = clean.build_deals(raw, config.DEFAULT_REFERENCE_DATE)
    return facts.build_facts(raw, deals, config.DEFAULT_REFERENCE_DATE)


def test_phase0_numbers_are_reproduced(built):
    pipeline = built["pipeline"]
    assert pipeline["deals_por_estagio"] == {"Won": 4238, "Lost": 2473, "Engaging": 1589, "Prospecting": 500}
    assert pipeline["win_rate_fechados"] == pytest.approx(0.632, abs=5e-4)
    assert built["qualidade"]["linhas_gtxpro"] == 1480
    assert built["qualidade"]["sem_conta"]["total"] == 1425
    assert built["qualidade"]["sem_conta"]["por_estagio"]["Engaging"] == 1088
    assert built["qualidade"]["sem_conta"]["fechados"] == 0
    assert built["qualidade"]["prospecting_sem_engage_date"] == 500
    assert built["ciclos"]["ciclo_maximo_fechados"] == 138
    assert built["ciclos"]["perdidos_ciclo_rapido"] == 1249
    bands = built["idade_hoje"]["faixas"]
    assert [bands[k]["n"] for k in bands] == [110, 188, 1291]
    assert bands["acima_do_ciclo_maximo"]["valor_tabela"] == 3198664
    assert built["idade_hoje"]["valor_tabela_engaging"] == 3892229
    assert built["prospecting"]["valor_tabela"] == 1073986


def test_numbers_cited_by_scope_are_facts(built):
    products = built["produtos"]
    assert products["produto_com_mais_deals"] == "GTX Basic"  # o briefing erra ao dizer MG Special
    assert products["segundo_produto_em_deals"] == "MG Special"
    assert products["deals_fechados_do_produto_maior_preco"] == 25
    assert products["receita_ganha_top3_share"] == pytest.approx(0.835, abs=5e-4)
    attributes = built["atributos"]
    in_sample = attributes["auc_categoricas_target_encoding_na_amostra_inflado"]
    assert round(min(in_sample.values()), 2) == 0.51 and round(max(in_sample.values()), 2) == 0.54
    assert all(abs(v - 0.5) < 0.01 for v in attributes["auc_numericas"].values())
    assert attributes["qui_quadrado_p"]["vendedor"] == pytest.approx(0.26, abs=5e-3)
    assert built["evidencia_2a_q1"]["win_rate_depois_do_primeiro_trimestre"] == pytest.approx(0.61, abs=5e-3)
    snapshot = built["fotos_do_briefing"]["2017-09-30"]["faixas"]
    assert [round(f["pct_ganhos"], 2) for f in snapshot[:4]] == [0.50, 0.34, 0.07, 0.0]


def test_evidence_2a_q1_is_a_cut_artifact(built):
    ev = built["evidencia_2a_q1"]
    months = {r["mes"]: r for r in ev["por_mes_de_fechamento"]}
    assert ev["primeiro_fechamento"] == "2017-03-01"
    assert ev["primeiro_mes_com_fechamento"] == "2017-03"
    assert [round(months[m]["win_rate"], 3) for m in ["2017-03", "2017-04", "2017-05", "2017-06"]] == [
        0.821, 0.486, 0.544, 0.828,
    ]
    cohorts = {r["mes"]: r for r in ev["por_coorte_de_engajamento"]}
    assert [cohorts[m]["ciclo_min"] for m in ["2016-10", "2016-11", "2016-12", "2017-01", "2017-02"]] == [
        123, 96, 63, 36, 5,
    ]
    assert ev["fechados_fora_da_regra_q_q1"] == 1
    criteria = ev["criterio"]
    assert criteria["c1_vale"] and criteria["c2_vale"] and criteria["c3_vale"]
    assert criteria["artefato_de_recorte"] is True


def test_evidence_2b_sellers_without_deals(built):
    ev = built["evidencia_2b_vendedores"]
    assert (ev["vendedores_cadastro"], ev["vendedores_com_deals"], ev["vendedores_sem_deals"]) == (35, 30, 5)
    assert ev["vendedores_com_deals_abertos"] == 27
    assert ev["vendedores_so_com_fechados"] == 3
    assert ev["managers"] == 6
    assert sorted(r["sales_agent"] for r in ev["sem_deals"]) == [
        "Carl Lin", "Carol Thompson", "Elizabeth Anderson", "Mei-Mei Johns", "Natalya Ivanova",
    ]
    assert ev["managers_sem_vendedor_sem_deals"] == ["Dustin Brinkmann"]


def test_evidence_2c_list_price_is_a_good_deal_value(built):
    ev = built["evidencia_2c_close_value"]
    assert ev["geral"]["media"] == pytest.approx(0.996, abs=5e-4)
    assert ev["geral"]["min"] == pytest.approx(0.657, abs=5e-4)
    assert ev["geral"]["max"] == pytest.approx(1.342, abs=5e-4)
    assert ev["perdidos_com_close_value_zero"] == ev["perdidos_n"] == 2473
    assert ev["ganhos_com_close_value_zero"] == 0
    assert ev["criterio"]["preco_de_tabela_serve_como_valor_do_deal_aberto"] is True


def test_facts_json_has_no_nan_and_only_json_types(built):
    def walk(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                assert isinstance(key, str)
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)
        else:
            assert obj is None or isinstance(obj, (str, bool, int, float))
            if isinstance(obj, float):
                assert math.isfinite(obj)

    walk(built)
