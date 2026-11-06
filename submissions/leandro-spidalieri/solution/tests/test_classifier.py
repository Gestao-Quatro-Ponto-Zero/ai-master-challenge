import joblib
import numpy as np
import pandas as pd
import pytest

from supportops.classifier import classify, fit, prepare, score_rows, select_threshold, split
from supportops.policy import (
    DOMAIN_IT,
    DOMAIN_OTHER,
    MAX_CHARS,
    REVIEW,
    SUGGEST,
    decide,
    model_reasons,
)


def fixture():
    docs = [
        (f"{theme} {i} {theme} request synthetic {i} troubleshooting", label)
        for label, theme in [
            ("Hardware", "screen display"),
            ("Storage", "disk folder"),
            ("Purchase", "order invoice"),
        ]
        for i in range(25)
    ]
    # Duplicado equivalente e conflito exato, excluído inteiro.
    docs.append((docs[0][0].upper() + ".", docs[0][1]))
    docs += [("same conflicting words", "Storage"), ("same conflicting words", "Purchase")]
    return pd.DataFrame(docs, columns=["Document", "Topic_group"])


def test_split_fit_only_on_train_and_reproducible(tmp_path):
    clean, audit = prepare(fixture(), "fixture")
    assert audit["exclusoes"]["chave_exata_com_rotulo_conflitante"] == 2
    assert audit["duplicatas_normalizadas_excedentes_retidas_no_grupo"] == 1
    parts = split(clean)
    assert parts.equals(split(clean))
    assert parts.groupby("group")["particao"].nunique().max() == 1
    assert parts.groupby("particao")["Topic_group"].nunique().min() == 3
    data = clean.join(parts["particao"])
    train = data[data["particao"] == "treino"]
    val = data[data["particao"] == "validacao"].copy()
    val["key"] += " leakprobesentinel"
    test = data[data["particao"] == "teste"]
    model = fit(train)
    assert "leakprobesentinel" not in model.named_steps["tfidf"].vocabulary_
    assert np.allclose(model.predict_proba(test["key"]), fit(train).predict_proba(test["key"]))
    model_path = tmp_path / "fixture.joblib"
    joblib.dump(model, model_path)
    assert np.allclose(
        model.predict_proba(test["key"]), joblib.load(model_path).predict_proba(test["key"])
    )
    val_scored = score_rows(model, val)
    assert set(val_scored["id"]).isdisjoint(test["id"])
    assert set(val_scored["previsto"]) <= set(train["Topic_group"])


def test_threshold_selection_only_uses_eligible_rows():
    validation = pd.DataFrame(
        {
            "apto": [True] * 250 + [False] * 110,
            "real": ["Hardware"] * 360,
            "previsto": ["Hardware"] * 150 + ["Storage"] * 100 + ["Hardware"] * 110,
            "score": [0.85] * 150 + [0.48] * 100 + [0.99] * 110,
        }
    )
    threshold, curve = select_threshold(validation)
    assert threshold == 0.5
    assert curve[10]["aceitos"] == 150
    assert select_threshold(validation.iloc[:8])[0] == 1.01


@pytest.mark.parametrize(
    ("text", "domain", "priority"),
    [
        ("", DOMAIN_IT, "Normal"),
        ("hello", DOMAIN_IT, "Normal"),
        ("x" * (MAX_CHARS + 1), DOMAIN_IT, "Normal"),
        ("please check my screen", DOMAIN_OTHER, "Normal"),
        ("please check my screen", DOMAIN_IT, "Crítica"),
        ("please grant me admin access", DOMAIN_IT, "Normal"),
    ],
)
def test_policy_gates_do_not_call_the_model(text, domain, priority):
    result = classify(None, {"limiar": 0.55, "modelo_versao": "fixture"}, text, domain, priority)
    assert result["decisao"] == REVIEW
    assert result["motivos"]
    assert result["score"] is None
    assert result["prioridade_informada"] == priority


def test_low_score_vocab_and_sensitive_prediction():
    assert decide([], 0.54, 0.55)[0] == REVIEW
    assert decide([], 0.55, 0.55)[0] == SUGGEST
    assert decide(model_reasons("Hardware", 0.2, 1), 0.98, 0.55)[0] == REVIEW
    assert decide(model_reasons("Administrative rights", 0.9, 10), 0.98, 0.55)[0] == REVIEW
