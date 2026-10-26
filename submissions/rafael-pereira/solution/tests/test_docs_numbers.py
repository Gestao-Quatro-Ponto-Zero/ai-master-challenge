"""Todo número dos documentos sai de um arquivo gerado.

(a) Os blocos AUTO batem com o re-render dos JSONs de fatos.
(b) Os números da prosa (fora dos blocos AUTO) batem com algum valor dos JSONs ou com uma constante
    estrutural de `config.ALLOWED_CONSTANTS`. Regras de extração e de comparação em `scorer.docs`.
Os testes do fim do arquivo garantem que o próprio verificador acusa número errado e ignora o que não é fato.
"""

import pytest

from scorer import config, docs

DOCS = pytest.mark.parametrize("path", config.COVERED_DOCS, ids=lambda p: p.name)


@pytest.fixture(scope="module")
def sources():
    return docs.load_sources()


@pytest.fixture(scope="module")
def pool(sources):
    return docs.number_pool(sources)


@DOCS
def test_auto_blocks_match_a_fresh_render(path, sources):
    text = docs.read_doc(path)
    assert docs.render_text(text, docs.render_blocks(sources)) == text, (
        f"{path.name} está desatualizado: rode `python -m scorer.docs`"
    )


@DOCS
def test_prose_numbers_come_from_the_facts(path, pool):
    bad = docs.unmatched_numbers(docs.read_doc(path), pool, docs.names_with_digits())
    report = "\n".join(f"{path.name}:{t.line}: {t.text!r}" for t in bad)
    assert not bad, f"números sem fonte em facts.json ou ALLOWED_CONSTANTS:\n{report}"


# --- o verificador em si ---------------------------------------------------------------------
FAKE_POOL = [3198664.0, 3892229.0, 0.81246, 1291.0, 0.632, 0.496, 1073986.0, 90.0]


def bad_tokens(text, ignore=()):
    return [t.text for t in docs.unmatched_numbers(text, FAKE_POOL, ignore)]


def test_checker_accepts_numbers_at_the_precision_shown():
    ok = "US$ 3,2 mi de US$ 3,9 mi; US$ 3.198.664; 81%; 81,2%; 1.291 deals; 63,2%; 0,50; US$ 1,07 mi; 90%"
    assert bad_tokens(ok) == []


def test_checker_flags_wrong_numbers():
    wrong = "US$ 3,3 mi; US$ 3.198.665; 82%; 81,3%; 1.292 deals; 0,64; 777"
    assert bad_tokens(wrong) == ["US$ 3,3 mi", "US$ 3.198.665", "82%", "81,3%", "1.292", "0,64", "777"]


def test_checker_ignores_what_is_not_a_fact():
    text = "\n".join(
        [
            "## 3. Seção numerada com 4 itens",
            "1. item numerado",
            "Datas: 31/12/2017, 2017-09-30, mar/2017, 12/2016 e os anos 2016, 2017Q1 e 2026.",
            "Código `1.234 e 99%`, link [texto](https://exemplo.com/987654) e https://exemplo.com/123456.",
            "```",
            "bloco 555 e 66,6%",
            "```",
            "<!-- comentário 4.321 -->",
            "O GTK 500 custa pouco.",
            "<!-- AUTO:x -->",
            "dentro do bloco: 123.456",
            "<!-- /AUTO:x -->",
        ]
    )
    assert bad_tokens(text, ignore=["GTK 500"]) == []
    assert bad_tokens("O GTK 500 custa pouco.") == ["500"]  # sem a lista de nomes, o 500 seria um número


def test_checker_reports_the_line_of_each_token():
    tokens = docs.unmatched_numbers("linha 1\nlinha 2 com 4.444\n\n```\nx\n```\nlinha 7 com 99,9%", FAKE_POOL)
    assert [(t.line, t.text) for t in tokens] == [(2, "4.444"), (7, "99,9%")]


def test_checker_reads_percentage_points_as_fraction_times_100():
    pool = [0.126, 0.0925]
    ok = "+12,6 pp e 12,6 pontos percentuais; 9,3 pp"
    assert [t.text for t in docs.unmatched_numbers(ok, pool)] == []
    bad = "12,7 pp, 0,126 pp e 12,6 pontos percentuais"
    assert [t.text for t in docs.unmatched_numbers(bad, pool)] == ["12,7 pp", "0,126 pp"]


def test_checker_does_not_confuse_plain_small_numbers_with_facts():
    assert bad_tokens("são 30 vendedores em 6 times; 99 não é checado, 100 é") == ["100"]


@pytest.mark.parametrize("name,old,new", [
    ("README.md", "62,5%", "93,5%"),
    ("README.md", "US$ 3,6 mi", "US$ 9,9 mi"),
    ("README.md", "1.463", "1.464"),
    ("MODEL_CARD.md", "1.425", "1.426"),
    ("MODEL_CARD.md", "0,996", "0,931"),
])
def test_checker_catches_a_wrong_number_in_the_real_readme_and_model_card(name, old, new, pool):
    path = next(p for p in config.COVERED_DOCS if p.name == name)
    text = docs.read_doc(path)
    assert old in docs.prose_text(text), f"{old!r} não está na prosa de {name}"
    mutated = docs.prose_text(text).replace(old, new, 1)
    bad = [t.text for t in docs.unmatched_numbers(mutated, pool, docs.names_with_digits())]
    assert new in " ".join(bad)


def test_auto_marker_without_renderer_is_an_error():
    with pytest.raises(KeyError):
        docs.render_text("<!-- AUTO:inexistente -->\n<!-- /AUTO:inexistente -->", {"outro": "x"})
    with pytest.raises(ValueError):
        docs.render_text("<!-- AUTO:a -->\nsem fechamento", {"a": "x"})


def test_inject_is_idempotent_and_only_touches_the_block():
    text = "antes\n<!-- AUTO:a -->\nvelho\n<!-- /AUTO:a -->\ndepois\n"
    once = docs.render_text(text, {"a": "novo"})
    assert once == "antes\n<!-- AUTO:a -->\nnovo\n<!-- /AUTO:a -->\ndepois\n"
    assert docs.render_text(once, {"a": "novo"}) == once
