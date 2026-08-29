"""Valida em holdout (80/20) que a tabela de sobrevivência por dias tem sinal real,
com baseline de comparação. Toda métrica citada no README vem daqui.

Roda: python -m src.validar_modelo (a partir de submissions/carlos-persike/solution/)
Gera: outputs/validacao_modelo.json
"""
import json
from pathlib import Path

from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from ingestao import carregar_pipeline_enriquecido
from probabilidade import calcular_tabela_sobrevivencia, probabilidade_por_dias

OUTPUTS_DIR = Path(__file__).resolve().parents[1] / "outputs"


def rodar_validacao() -> dict:
    df = carregar_pipeline_enriquecido()
    fechados = df[df["deal_stage"].isin(["Won", "Lost"])].copy()
    fechados["ganhou"] = (fechados["deal_stage"] == "Won").astype(int)
    fechados["dias_ciclo"] = (fechados["close_date"] - fechados["engage_date"]).dt.days
    fechados = fechados.dropna(subset=["dias_ciclo"])

    treino, teste = train_test_split(
        fechados, test_size=0.2, random_state=42, stratify=fechados["ganhou"]
    )

    tabela = calcular_tabela_sobrevivencia(treino)
    teste = teste.copy()
    teste["proba_prevista"] = teste["dias_ciclo"].apply(lambda d: probabilidade_por_dias(d, tabela))
    teste["previsao"] = (teste["proba_prevista"] >= 0.5).astype(int)

    baseline_acc = max(teste["ganhou"].mean(), 1 - teste["ganhou"].mean())

    resultado = {
        "n_treino": len(treino),
        "n_teste": len(teste),
        "auc_holdout": round(roc_auc_score(teste["ganhou"], teste["proba_prevista"]), 3),
        "acuracia_holdout": round(accuracy_score(teste["ganhou"], teste["previsao"]), 3),
        "acuracia_baseline_classe_majoritaria": round(baseline_acc, 3),
        "tabela_sobrevivencia_dias_para_producao": calcular_tabela_sobrevivencia(fechados),
        "observacao": (
            "AUC 0.59 = sinal real e estatisticamente significativo (ver auditoria.txt), "
            "porém modesto. A acuracia do holdout nao supera o baseline porque nenhuma faixa "
            "de dias cruza 50% de chance de vitoria isolada — o sinal move a probabilidade, "
            "nao decide o resultado sozinho. Por isso o score final combina probabilidade x "
            "valor do negocio, em vez de uma decisao binaria ganha/perde."
        ),
    }
    return resultado


if __name__ == "__main__":
    OUTPUTS_DIR.mkdir(exist_ok=True)
    resultado = rodar_validacao()
    (OUTPUTS_DIR / "validacao_modelo.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
