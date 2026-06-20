"""Testes do núcleo de scoring. Rodar: pytest -q (ou make test)."""
import pandas as pd
import pytest

from scoring.features import smoothed_winrate, aging_subscore
from scoring.config import (
    GLOBAL_WIN_RATE, CYCLE_MEDIAN_DAYS, CYCLE_P75_DAYS, WON_MAX_DAYS,
    URGENCY_FLOOR,
)
from scoring.model import score_open_deals, brief_do_dia, brief_must_acts
from app.theme import brief_panel_html


# ---------- smoothing bayesiano ----------
def test_smoothing_celula_vazia_volta_para_base():
    # sem histórico -> deve retornar a base global
    assert smoothed_winrate(0, 0) == pytest.approx(GLOBAL_WIN_RATE)


def test_smoothing_celula_pequena_puxa_para_base():
    # 1 win em 1 deal: cru=100%, suavizado deve ficar bem abaixo (perto da base)
    s = smoothed_winrate(1, 1)
    assert GLOBAL_WIN_RATE < s < 1.0
    assert s < 0.75  # não acredita em 100% com n=1


def test_smoothing_celula_grande_converge_para_real():
    # 700 wins / 1000: suavizado ~ 0.70
    s = smoothed_winrate(700, 1000)
    assert abs(s - 0.70) < 0.01


def test_smoothing_monotonico_no_winrate():
    # mais wins (mesmo n) => maior prob
    assert smoothed_winrate(80, 100) > smoothed_winrate(50, 100)


def test_smoothing_clampado_em_intervalo_valido():
    # dado inconsistente (wins > closed) não pode exceder 1 — distorceria
    # expected_value e o "% fecha" do breakdown.
    assert smoothed_winrate(0, 0) == pytest.approx(GLOBAL_WIN_RATE)
    assert smoothed_winrate(5, 0) <= 1.0
    assert 0.0 <= smoothed_winrate(1000, 1) <= 1.0


# ---------- aging (urgência: curva SINO ancorada no ciclo dos Won) ----------
def test_aging_deal_novo_baixa_urgencia():
    # recém-engajado: ainda esquentando, baixa urgência, saudável
    sub, label, sev = aging_subscore(5, "Engaging")
    assert 0 <= sub < 30 and sev == "ok"


def test_aging_janela_ideal_plato_no_pico():
    # dentro da janela 57-88d (mediana→p75 dos Won): platô no máximo, saudável
    sub1, _, sev1 = aging_subscore(CYCLE_MEDIAN_DAYS, "Engaging")
    sub2, _, sev2 = aging_subscore(CYCLE_P75_DAYS, "Engaging")
    assert sub1 == 100.0 and sev1 == "ok"
    assert sub2 == 100.0 and sev2 == "ok"


def test_aging_decai_apos_a_janela():
    # entre p75 (88) e o Won máx (138): urgência cai, severidade alerta
    sub, label, sev = aging_subscore((CYCLE_P75_DAYS + WON_MAX_DAYS) // 2, "Engaging")
    assert URGENCY_FLOOR < sub < 100 and sev == "alerta"


def test_aging_stale_alem_do_max_won():
    # além de qualquer fechamento histórico: piso, severidade crítica
    sub, label, sev = aging_subscore(WON_MAX_DAYS + 50, "Engaging")
    assert sub == URGENCY_FLOOR and sev == "critico"


def test_aging_prospecting_excluido():
    # Prospecting não tem engage_date -> sem componente de urgência
    assert aging_subscore(None, "Prospecting") is None


def test_aging_curva_sino_nao_monotonica():
    # sino: a janela ideal (70d) supera tanto o deal novo (20d) quanto o velho (200d)
    novo = aging_subscore(20, "Engaging")[0]
    pico = aging_subscore(70, "Engaging")[0]
    velho = aging_subscore(200, "Engaging")[0]
    assert pico > novo and pico > velho
    assert velho <= novo   # deal morto não é mais "urgente" que um deal novo


# ---------- modelo (integração com fixtures, sem DB) ----------
@pytest.fixture
def mini():
    open_deals = pd.DataFrame([
        # Engaging, vendedor bom, deal grande, esfriando (alerta, não stale) -> alto
        dict(opportunity_id="A", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Pro", series="GTX", sales_price=4821, account="X", sector="tech",
             deal_stage="Engaging", engage_date="2017-01-01", days_open=70),
        # Prospecting, vendedor fraco, deal pequeno -> baixo (sem urgência)
        dict(opportunity_id="B", sales_agent="Bob", manager="M", regional_office="West",
             product="GTX Basic", series="GTX", sales_price=550, account=None, sector=None,
             deal_stage="Prospecting", engage_date=None, days_open=None),
        # Engaging muito além do ciclo (200d > p90=106 e crítico) -> stale
        dict(opportunity_id="C", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Plus Pro", series="GTX", sales_price=5482, account="Y", sector="tech",
             deal_stage="Engaging", engage_date="2016-10-01", days_open=200),
    ])
    agent_wr = pd.DataFrame([
        dict(sales_agent="Ace", wins=700, closed=1000, win_rate=0.70),
        dict(sales_agent="Bob", wins=300, closed=600, win_rate=0.50),
    ])
    return open_deals, agent_wr


def test_score_breakdown_soma_igual_score(mini):
    df = score_open_deals(*mini)
    for _, r in df.iterrows():
        soma = sum(b["pontos"] for b in r["breakdown"])
        assert round(soma) == r["score"], f"breakdown não audita o score em {r['opportunity_id']}"


def test_prospecting_sem_componente_urgencia(mini):
    df = score_open_deals(*mini)
    bob = df[df["opportunity_id"] == "B"].iloc[0]
    urg = [b for b in bob["breakdown"] if b["feature"] == "Urgência"][0]
    assert urg["pontos"] == 0.0  # renormalizado sem urgência


def test_deal_forte_supera_deal_fraco(mini):
    df = score_open_deals(*mini).set_index("opportunity_id")
    assert df.loc["A", "score"] > df.loc["B", "score"]


def test_score_no_intervalo_0_100(mini):
    df = score_open_deals(*mini)
    assert df["score"].between(0, 100).all()


# ---------- regressões de qualidade (refino do scoring) ----------
def test_value_independe_de_P(mini):
    """o componente de valor usa o tamanho do deal puro — P não entra duas vezes."""
    open_deals, agent_wr = mini
    # dois deals idênticos em preço, vendedores com P bem diferente
    deals = pd.DataFrame([
        dict(opportunity_id="V1", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Pro", series="GTX", sales_price=4821, account="X", sector="tech",
             deal_stage="Prospecting", engage_date=None, days_open=None),
        dict(opportunity_id="V2", sales_agent="Bob", manager="M", regional_office="West",
             product="GTX Pro", series="GTX", sales_price=4821, account="Y", sector="tech",
             deal_stage="Prospecting", engage_date=None, days_open=None),
    ])
    df = score_open_deals(deals, agent_wr).set_index("opportunity_id")
    assert df.loc["V1", "value_sub"] == df.loc["V2", "value_sub"], \
        "mesmo preço deve dar o mesmo sub-score de valor, independente do vendedor"


def test_stale_fora_do_foco_agora(mini):
    """deal muito além do ciclo vencedor é marcado is_stale e rebaixado de tier
    por construção (nunca "Foco Agora"), mesmo com rep forte + deal grande."""
    df = score_open_deals(*mini).set_index("opportunity_id")
    assert bool(df.loc["C", "is_stale"]) is True
    assert bool(df.loc["A", "is_stale"]) is False
    assert df.loc["C", "tier"] == "Baixa Prioridade"   # tier EFETIVO, não o do score cru
    assert "descartar" in df.loc["C", "action"].lower()


def test_stale_nunca_e_foco_agora_mesmo_com_score_alto():
    """garante a consistência sidebar==lista: um stale de altíssimo valor/reputação
    ainda assim cai fora de "Foco Agora" (não conta como prioridade do dia)."""
    deals = pd.DataFrame([
        dict(opportunity_id="HOT", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Pro", series="GTX", sales_price=26768, account="Big", sector="tech",
             deal_stage="Engaging", engage_date="2016-06-01", days_open=400),  # bem além de 138d
    ])
    wr = pd.DataFrame([dict(sales_agent="Ace", wins=950, closed=1000, win_rate=0.95)])
    df = score_open_deals(deals, wr).iloc[0]
    assert bool(df["is_stale"]) is True
    assert df["tier"] != "Foco Agora"      # morto nunca é prioridade do dia
    assert df["tier"] == "Baixa Prioridade"


def test_brief_exclui_deal_sem_conta():
    """deal sem conta não entra no brief do dia — não dá para priorizar quem o
    rep não identifica (vira alerta de higiene na UI)."""
    deals = pd.DataFrame([
        dict(opportunity_id="COM", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Pro", series="GTX", sales_price=4821, account="Acme", sector="tech",
             deal_stage="Engaging", engage_date="2017-01-01", days_open=70),
        dict(opportunity_id="SEM", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Pro", series="GTX", sales_price=6000, account=None, sector=None,
             deal_stage="Engaging", engage_date="2017-01-01", days_open=70),
    ])
    wr = pd.DataFrame([dict(sales_agent="Ace", wins=700, closed=1000, win_rate=0.70)])
    df = score_open_deals(deals, wr)
    brief = brief_do_dia(df, "Ace")
    assert "COM" in brief or "Acme" in brief
    assert "SEM" not in brief      # sem conta fica de fora do brief


def test_brief_retorna_top_n(mini):
    """brief do dia lista os must-acts do vendedor e exclui deals stale."""
    df = score_open_deals(*mini)
    brief = brief_do_dia(df, "Ace")
    assert brief.startswith("Bom dia, Ace.")  # abertura humana
    assert "GTX Pro" in brief          # deal vivo entra
    assert "GTX Plus Pro" not in brief  # deal stale (C) fica fora


def test_brief_traz_motivo_por_driver():
    """cada must-act deve trazer o MOTIVO ancorado num driver real do deal
    (win-rate / ticket / janela), não só nome + score."""
    deals = pd.DataFrame([
        dict(opportunity_id="D1", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Pro", series="GTX", sales_price=4821, account="Acme", sector="tech",
             deal_stage="Engaging", engage_date="2017-01-01", days_open=120),  # 88<120<138 -> janela fechando
    ])
    wr = pd.DataFrame([dict(sales_agent="Ace", wins=700, closed=1000, win_rate=0.70)])
    df = score_open_deals(deals, wr)
    brief = brief_do_dia(df, "Ace")

    assert brief.startswith("Bom dia, Ace.")
    must = [l for l in brief.splitlines() if l.startswith("1.")]
    assert must, "deve haver pelo menos um must-act numerado"
    linha = must[0]
    assert "GTX Pro" in linha and "Acme" in linha          # identifica o deal
    assert "(score" not in linha                            # não é o dump antigo "(score X)"
    # motivo ancorado em driver REAL: win-rate, ticket ou janela
    assert any(k in linha for k in ("fecha", "R$", "janela", "esquentando"))
    # 120d (janela fechando, severity alerta) deve liderar com a janela + ação urgente
    assert "janela está fechando (120d)" in linha
    assert "Aja hoje." in linha
    # win-rate real do vendedor aparece como reforço (não inventado)
    assert "70%" in linha


def test_brief_driver_varia_por_deal():
    """o brief lidera por drivers DIFERENTES conforme o que pesa em cada deal:
    janela fechando (urgência) vs vendedor forte na janela ideal (probabilidade)."""
    deals = pd.DataFrame([
        # vendedor forte, janela ideal (70d), severity ok -> lidera por win-rate
        dict(opportunity_id="P", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Pro", series="GTX", sales_price=4821, account="Acme", sector="tech",
             deal_stage="Engaging", engage_date="2017-01-01", days_open=70),
        # janela fechando (120d), severity alerta -> lidera pela urgência
        dict(opportunity_id="U", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Basic", series="GTX", sales_price=550, account="Beta", sector="tech",
             deal_stage="Engaging", engage_date="2017-01-01", days_open=120),
    ])
    wr = pd.DataFrame([dict(sales_agent="Ace", wins=700, closed=1000, win_rate=0.70)])
    df = score_open_deals(deals, wr)
    brief = brief_do_dia(df, "Ace")
    linha_acme = [l for l in brief.splitlines() if "Acme" in l][0]
    linha_beta = [l for l in brief.splitlines() if "Beta" in l][0]
    # Beta (janela fechando) lidera com a janela; Acme (janela ideal/forte) não lidera com "fechando"
    assert "a janela está fechando (120d)" in linha_beta
    assert "fechando" not in linha_acme


def test_brief_txt_e_painel_mesma_fonte():
    """painel visual e brief .txt saem da MESMA fonte (brief_must_acts) — não
    podem divergir: mesmo nº de itens, mesmos deals e o mesmo motivo opinativo."""
    deals = pd.DataFrame([
        dict(opportunity_id="P", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Pro", series="GTX", sales_price=4821, account="Acme", sector="tech",
             deal_stage="Engaging", engage_date="2017-01-01", days_open=70),
        dict(opportunity_id="U", sales_agent="Ace", manager="M", regional_office="West",
             product="GTX Basic", series="GTX", sales_price=550, account="Beta", sector="tech",
             deal_stage="Engaging", engage_date="2017-01-01", days_open=120),
    ])
    wr = pd.DataFrame([dict(sales_agent="Ace", wins=700, closed=1000, win_rate=0.70)])
    df = score_open_deals(deals, wr)

    ma = brief_must_acts(df, "Ace")
    txt = brief_do_dia(df, "Ace")
    painel = brief_panel_html(ma, show_header=False)

    # nº de itens bate entre fonte, .txt e abertura do painel
    assert ma["count"] == len([l for l in txt.splitlines() if l[:2] in ("1.", "2.")])
    assert f"{ma['count']} deals quentes" in painel  # mesma abertura do .txt

    # cada must-act aparece com deal + motivo idênticos nos dois formatos
    for it in ma["items"]:
        assert it["product"] in txt and it["product"] in painel
        assert it["account"] in txt and it["account"] in painel
        assert it["motivo"] in txt and it["motivo"] in painel
        assert it["action"] in txt and it["action"] in painel
