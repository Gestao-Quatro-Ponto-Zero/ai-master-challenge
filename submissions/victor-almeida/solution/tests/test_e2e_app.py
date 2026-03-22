"""
Testes E2E do Lead Scorer com Playwright.

Sobe o Streamlit, abre o browser e testa o fluxo completo:
1. Tela principal carrega com metricas
2. Filtros funcionam (selecionar vendedor, cascade)
3. Limpar filtros reseta tudo
4. Pipeline mostra deals com botao Ver
5. Clicar Ver abre modal com detalhe do deal
6. Score breakdown e acoes recomendadas aparecem no modal
"""

import subprocess
import time
import sys
import os
import signal

import pytest

# Path setup
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def streamlit_app():
    """Sobe o Streamlit como subprocess e retorna a URL."""
    app_path = os.path.join(os.path.dirname(__file__), "..", "app.py")
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.headless", "true",
            "--server.port", "8599",
            "--browser.gatherUsageStats", "false",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )

    # Esperar o app subir
    url = "http://localhost:8599"
    for _ in range(30):
        time.sleep(1)
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=2)
            break
        except Exception:
            continue
    else:
        proc.kill()
        raise RuntimeError("Streamlit nao subiu em 30 segundos")

    yield url

    # Teardown
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture(scope="module")
def browser_page(streamlit_app):
    """Cria browser Playwright e retorna page conectada ao app."""
    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(streamlit_app, wait_until="networkidle")
    # Esperar o app renderizar completamente
    page.wait_for_selector("text=Lead Scorer", timeout=15000)
    time.sleep(2)  # Dar tempo pro scoring calcular

    yield page

    browser.close()
    pw.stop()


# ===================================================================
# 1. Tela principal — metricas e graficos
# ===================================================================

class TestTelaInicial:
    """Verifica que a tela principal carrega com todos os elementos."""

    def test_titulo_lead_scorer(self, browser_page):
        """Titulo 'Lead Scorer' aparece na pagina."""
        assert browser_page.locator("text=Lead Scorer").first.is_visible()

    def test_metrica_deals_ativos(self, browser_page):
        """Metrica 'Deals Ativos' aparece com valor numerico."""
        metric = browser_page.get_by_test_id("stMainBlockContainer").get_by_text(
            "Deals Ativos", exact=True
        )
        assert metric.is_visible()
        # Valor 2089 deve aparecer na pagina
        page_text = browser_page.get_by_test_id("stMainBlockContainer").inner_text()
        assert "2089" in page_text or "2,089" in page_text, (
            f"Expected 2089 deals somewhere in main content"
        )

    def test_metrica_pipeline_total(self, browser_page):
        """Metrica 'Pipeline Total' aparece."""
        assert browser_page.locator("text=Pipeline Total").is_visible()

    def test_metrica_deals_zumbi(self, browser_page):
        """Metrica 'Deals Zumbi' aparece."""
        metric = browser_page.get_by_test_id("stMainBlockContainer").get_by_text(
            "Deals Zumbi", exact=True
        )
        assert metric.is_visible()

    def test_metrica_taxa_conversao(self, browser_page):
        """Metrica 'Taxa de Conversao' aparece com percentual."""
        metric = browser_page.locator("text=Taxa de Conversao")
        assert metric.is_visible()

    def test_grafico_distribuicao_score(self, browser_page):
        """Grafico de distribuicao por faixa de score aparece."""
        assert browser_page.locator("text=Distribuicao por Faixa de Score").is_visible()

    def test_grafico_saude_pipeline(self, browser_page):
        """Grafico de saude do pipeline aparece."""
        assert browser_page.locator("text=Saude do Pipeline").is_visible()

    def test_faixas_todas_populadas(self, browser_page):
        """Todas as 4 faixas de score aparecem no grafico."""
        for faixa in ["Critico", "Risco", "Atencao", "Alta Prioridade"]:
            assert browser_page.locator(f"text={faixa}").first.is_visible(), (
                f"Faixa '{faixa}' nao encontrada"
            )

    def test_pipeline_section_visivel(self, browser_page):
        """Secao Pipeline com deals aparece."""
        assert browser_page.locator("text=Pipeline").first.is_visible()
        assert browser_page.locator("text=deals ativos").first.is_visible()


# ===================================================================
# 2. Filtros
# ===================================================================

class TestFiltros:
    """Verifica que filtros funcionam corretamente."""

    def test_sidebar_filtros_visiveis(self, browser_page):
        """Sidebar com filtros esta visivel."""
        assert browser_page.locator("text=Filtros").first.is_visible()

    def test_filtrar_por_vendedor(self, browser_page):
        """Selecionar vendedor filtra o pipeline."""
        page = browser_page

        # Encontrar o selectbox "Vendedor" na sidebar pelo label
        sidebar = page.locator("[data-testid='stSidebar']")

        # Streamlit renderiza selectbox com data-testid="stSelectbox"
        # Encontrar pelo label "Vendedor"
        vendedor_container = sidebar.locator(
            "[data-testid='stSelectbox']"
        ).filter(has_text="Vendedor")

        # Clicar para abrir o dropdown
        vendedor_container.click()
        time.sleep(0.5)

        # Selecionar "Anna Snelling" na lista de opcoes
        # Streamlit mostra opcoes em um popover/listbox
        option = page.get_by_role("option", name="Anna Snelling")
        if option.count() == 0:
            # Fallback: tentar locator por texto
            option = page.locator("text=Anna Snelling").last
        option.click()
        time.sleep(3)  # Esperar rerender

        # Verificar que o pipeline filtrou (deals ativos < 2089)
        main_text = page.get_by_test_id("stMainBlockContainer").inner_text()
        assert "2089" not in main_text, (
            "Apos filtrar por Anna Snelling, nao deveria ter 2089 deals"
        )

    def test_limpar_filtros(self, browser_page):
        """Botao 'Limpar filtros' reseta tudo."""
        page = browser_page

        # Clicar em Limpar filtros
        limpar_btn = page.locator("text=Limpar filtros")
        if limpar_btn.is_visible():
            limpar_btn.click()
            time.sleep(2)

            # Verificar que voltou ao total
            page_text = page.inner_text("body")
            assert "2089" in page_text or "2,089" in page_text, (
                "Apos limpar filtros, deveria voltar a 2089 deals"
            )


# ===================================================================
# 3. Pipeline e botao Ver
# ===================================================================

class TestPipelineView:
    """Verifica pipeline e interacao com deals."""

    def test_botao_ver_existe(self, browser_page):
        """Botoes 'Ver' aparecem no pipeline."""
        ver_buttons = browser_page.locator("button:has-text('Ver')")
        assert ver_buttons.count() > 0, "Nenhum botao 'Ver' encontrado no pipeline"

    def test_clicar_ver_abre_modal(self, browser_page):
        """Clicar 'Ver' abre modal com detalhe do deal."""
        page = browser_page

        # Clicar no primeiro botao Ver
        ver_buttons = page.locator("button:has-text('Ver')")
        ver_buttons.first.click()
        time.sleep(2)

        # Verificar que modal abriu (dialog do Streamlit)
        dialog = page.locator("[role='dialog']")
        assert dialog.is_visible(), "Modal de detalhe nao abriu"

    def test_modal_tem_composicao_score(self, browser_page):
        """Modal mostra composicao do score."""
        dialog = browser_page.locator("[role='dialog']")
        dialog_text = dialog.inner_text()

        # Labels em PT-BR
        assert "Etapa" in dialog_text, "Label 'Etapa' nao encontrado no modal"
        assert "Valor do Deal" in dialog_text, "Label 'Valor do Deal' nao encontrado"
        assert "Velocidade" in dialog_text, "Label 'Velocidade' nao encontrado"

    def test_modal_tem_acoes_recomendadas(self, browser_page):
        """Modal mostra acoes recomendadas."""
        dialog = browser_page.locator("[role='dialog']")
        dialog_text = dialog.inner_text()

        # Deve ter alguma acao (deal detail ou NBA)
        has_action = (
            "Acoes Recomendadas" in dialog_text
            or "Proxima acao recomendada" in dialog_text
            or "Prioridade maxima" in dialog_text
            or "Deal em risco" in dialog_text
            or "Deal parado" in dialog_text
            or "Deal em andamento" in dialog_text
            or "Deal em fase inicial" in dialog_text
            or "Deal saudavel" in dialog_text
        )
        assert has_action, f"Nenhuma acao encontrada no modal. Texto: {dialog_text[:500]}"

    def test_modal_sem_jargao_ingles(self, browser_page):
        """Modal nao contem jargao em ingles (WR, NBA, Seller Fit, etc)."""
        dialog = browser_page.locator("[role='dialog']")
        dialog_text = dialog.inner_text()

        jargoes = ["(NBA", "NBA-", "Seller Fit", "Account Health", "Expected Value", "Win Rate"]
        for jargao in jargoes:
            assert jargao not in dialog_text, (
                f"Jargao '{jargao}' encontrado no modal — deveria estar em PT-BR"
            )

    def test_fechar_modal(self, browser_page):
        """Fechar modal (Escape) volta ao pipeline."""
        page = browser_page

        # Fechar dialog com Escape
        page.keyboard.press("Escape")
        time.sleep(1)

        # Dialog deve ter fechado
        dialog = page.locator("[role='dialog']")
        assert not dialog.is_visible(), "Modal deveria ter fechado apos Escape"

        # Pipeline ainda visivel
        assert page.locator("text=Pipeline").first.is_visible()


# ===================================================================
# 4. Robustez
# ===================================================================

class TestRobustez:
    """Testes de robustez basicos."""

    def test_recarregar_pagina(self, browser_page):
        """Recarregar a pagina nao quebra o app."""
        page = browser_page
        page.reload(wait_until="networkidle")
        time.sleep(3)
        assert page.locator("text=Lead Scorer").first.is_visible()

    def test_sem_erros_streamlit(self, browser_page):
        """Nenhum erro Streamlit visivel na pagina."""
        page_text = browser_page.inner_text("body")
        error_indicators = [
            "StreamlitAPIException",
            "KeyError",
            "TypeError",
            "ValueError",
            "AttributeError",
            "Traceback",
        ]
        for err in error_indicators:
            assert err not in page_text, f"Erro '{err}' encontrado na pagina"
