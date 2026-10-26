"""O README segue o template do G4 e os documentos de submissão estão coerentes.

Estrutura (títulos na ordem, resumo executivo curto, marcas obrigatórias) e links relativos que existem.
Os números do README e do MODEL_CARD são conferidos em `test_docs_numbers.py`.
"""

import re

import pytest

from scorer import config, docs

README = config.SUBMISSION_DIR / "README.md"
MODEL_CARD = config.DOCS_DIR / "MODEL_CARD.md"
SCREENSHOTS = ["final_inicio_1280.png", "final_inicio_390.png"]

TITLES_IN_ORDER = [
    "# Submissão — Rafael Pereira — Challenge 003",
    "## Sobre mim",
    "## Executive Summary",
    "## Solução",
    "### Como rodar (setup)",
    "### Abordagem",
    "### Resultados / Findings",
    "### Recomendações",
    "### Limitações",
    "## Process Log — Como usei IA",
    "### Ferramentas usadas",
    "### Workflow",
    "### Onde a IA errou e como corrigi",
    "### O que eu adicionei que a IA sozinha não faria",
    "## Evidências",
]
SENTENCE_END = re.compile(r"[.!?](\s|$)")
LINK = re.compile(r"\]\(([^)\s]+)\)")


@pytest.fixture(scope="module")
def text():
    return docs.read_doc(README)


def section(text: str, title: str) -> str:
    """Texto entre o título e o próximo título de qualquer nível (ou separador ---)."""
    start = text.index(f"\n{title}\n") + len(title) + 2
    end = re.search(r"\n(#{1,6} |---\n)", text[start:])
    return text[start : start + end.start()] if end else text[start:]


def test_titles_appear_once_and_in_template_order(text):
    positions = []
    for title in TITLES_IN_ORDER:
        assert text.count(f"\n{title}\n") + (1 if text.startswith(title + "\n") else 0) == 1, f"título ausente ou repetido: {title}"
        positions.append(text.index(title))
    assert positions == sorted(positions)


def test_template_separators_and_last_line(text):
    assert text.count("\n---\n") >= 4  # depois de Sobre mim, do resumo, de Limitações e de Evidências
    last = text.rstrip().splitlines()[-1]
    assert re.fullmatch(r"_Submissão enviada em: (\[preencher ao abrir o PR\]|\d{2}/\d{2}/\d{4})_", last), last


def test_executive_summary_has_at_most_five_sentences(text):
    summary = section(text, "## Executive Summary").strip()
    sentences = len(SENTENCE_END.findall(summary))
    assert 3 <= sentences <= 5, f"o resumo tem {sentences} frases"


def test_executive_summary_opens_with_the_finding_and_closes_with_the_recommendation(text):
    summary = section(text, "## Executive Summary").strip()
    assert summary.startswith("O que separa os deals")
    assert "frescor" in summary.split(".")[0]
    assert "US$ 3,6 mi" in summary  # a lista Limpe de hoje, com a curva v2 (antes da correção: US$ 3,2 mi)
    assert "depois do backtest" in summary  # a troca de curva é declarada no resumo
    assert summary.rstrip().split(". ")[-1].startswith("Recomendo")


def test_about_me_has_linkedin_and_challenge(text):
    about = section(text, "## Sobre mim")
    assert "https://www.linkedin.com/in/rafael-pereira-30122003-" in about
    assert "**Nome:** Rafael Pereira" in about
    assert "003 — Lead Scorer" in about


def test_added_value_section_is_final_and_ties_to_the_ai_master_profile(text):
    added = section(text, "### O que eu adicionei que a IA sozinha não faria")
    assert "[RASCUNHO" not in added  # revisado pelo Rafael no bloco 7
    for needle in ["AI Master", "governança", "não automatizar"]:
        assert needle in added, needle


def test_ai_errors_are_labelled_by_origin(text):
    errors = section(text, "### Onde a IA errou e como corrigi")
    bullets = [b for b in errors.split("\n- ")[1:]]
    assert len(bullets) >= 8
    for bullet in bullets:
        head = bullet.split("\n")[0]
        assert "(fase 0, com Rafael)" in head or "(execução delegada)" in head, head[:80]


def test_evidence_map_and_chat_export_exist():
    log = config.SUBMISSION_DIR / "process-log"
    for name in ["README.md", "07_revisao-do-rafael.md", "chat-exports/sessao-orquestracao-claude-code.md"]:
        assert (log / name).exists(), name


def test_tools_table_and_evidence_checklist_exist(text):
    tools = section(text, "### Ferramentas usadas")
    assert "| Ferramenta | Para que usou |" in tools
    for needle in ["Opus 5.5", "Sonnet", "Haiku", "contexto limpo"]:
        assert needle in tools
    evidence = section(text, "## Evidências")
    assert evidence.count("- [") >= 5
    assert "LEIA-ME" in evidence or "chat-exports" in evidence


def test_required_limitations_are_stated(text):
    limits = section(text, "### Limitações")
    for needle in ["16:28 e 19:01", "dulwich", "chat-exports"]:
        assert needle in limits, needle


def test_workflow_has_one_item_per_block_from_0_to_6(text):
    flow = section(text, "### Workflow")
    for n in range(7):
        assert re.search(rf"^{n}\. ", flow, re.M), f"falta o item {n}"


def test_setup_has_pages_placeholder_and_commands(text):
    setup = section(text, "### Como rodar (setup)")
    assert "https://rafael-pereira-silva.github.io/ai-master-challenge/submissions/rafael-pereira/solution/app/" in setup
    for cmd in ["pip install -r requirements.txt", "python -m pytest", "python -m scorer.build --reference-date 2017-12-31",
                "pip install -r requirements-dev.txt", "python tools/check_app.py --prefix final"]:
        assert cmd in setup, cmd


def test_auto_blocks_of_the_readme_exist(text):
    for name in ["readme-achados", "readme-backtest", "readme-hoje"]:
        assert f"<!-- AUTO:{name} -->" in text and name in docs.BLOCKS


def test_model_card_has_the_required_sections():
    card = docs.read_doc(MODEL_CARD).replace("**", "")
    for needle in ["Propósito e uso pretendido", "Uso NÃO pretendido", "Dados e período", "Desempenho", "Limitações",
                   "Riscos e mitigação", "Quando recalibrar", "Dono e revisão", "<!-- AUTO:mc-desempenho -->",
                   "<!-- AUTO:mc-recalibracao -->", "Limpe significa confirmar"]:
        assert needle in card, needle
    for banned in ["avaliar ou ranquear vendedores", "forecast financeiro", "encerrar deals automaticamente"]:
        assert banned in card.lower().replace("**", "")


def test_readme_and_model_card_are_covered_by_the_number_check():
    names = {p.name for p in config.COVERED_DOCS}
    assert {"README.md", "MODEL_CARD.md"} <= names


def relative_links(text: str) -> list[str]:
    plain = re.sub(r"```.*?```", "", text, flags=re.S)
    found = [m.group(1) for m in LINK.finditer(plain)]
    return [link.split("#")[0] for link in found if not link.startswith(("http://", "https://", "mailto:"))]


@pytest.mark.parametrize("path", [README, MODEL_CARD], ids=lambda p: p.name)
def test_relative_links_point_to_existing_files(path):
    base = path.parent
    missing = []
    for link in relative_links(docs.read_doc(path)):
        if link.endswith(tuple(SCREENSHOTS)):
            continue  # os screenshots têm teste próprio (são gerados no fim do bloco 4)
        if link and not (base / link).exists():
            missing.append(link)
    assert not missing, f"links quebrados em {path.name}: {missing}"


@pytest.mark.parametrize("name", SCREENSHOTS)
def test_screenshot_files_linked_by_the_readme_exist(name, text):
    assert f"process-log/screenshots/{name}" in text
    assert (config.SUBMISSION_DIR / "process-log" / "screenshots" / name).exists(), (
        f"{name} ainda não existe: rode `python tools/check_app.py --prefix final`"
    )
