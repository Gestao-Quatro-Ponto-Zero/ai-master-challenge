"""Language and theme-facing contract tests."""

from dashboard.i18n import LANGUAGES, UI, option_label, text


def test_language_selector_exposes_three_flagged_languages() -> None:
    assert LANGUAGES == {
        "🇧🇷 Português": "pt",
        "🇪🇸 Español": "es",
        "🇺🇸 English": "en",
    }


def test_translation_catalogs_have_the_same_contract() -> None:
    expected = set(UI["pt"])
    assert expected
    assert all(set(catalog) == expected for catalog in UI.values())


def test_unknown_language_falls_back_to_portuguese() -> None:
    assert text("unknown") == UI["pt"]


def test_technical_options_are_humanized_in_every_language() -> None:
    expected = {
        "pt": "Faixa etária da audiência",
        "es": "Edad de la audiencia",
        "en": "Audience age group",
    }
    assert {
        language: option_label(language, "audience_age_distribution") for language in expected
    } == expected
    assert option_label("en", "macro_100k_500k") == "Macro · 100K to 500K"
