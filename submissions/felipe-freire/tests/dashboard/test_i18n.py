"""Language and theme-facing contract tests."""

from dashboard.i18n import LANGUAGES, UI, text


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
