import numpy as np
import pandas as pd
import shap


def run_shap(model, X, max_features=10):
    print("\n🔍 INICIANDO SHAP...\n")

    if X is None or X.empty:
        print("⚠️ SHAP não executado: matriz de features vazia.")
        return pd.DataFrame(columns=["feature", "impact"])

    X = X.copy().fillna(0)

    try:
        explainer = shap.Explainer(model, X)
        shap_values = explainer(X)

        # Para classificação binária, usar valores absolutos médios
        values = shap_values.values

        # Se vier 3D, reduzir corretamente
        if len(values.shape) == 3:
            values = values[:, :, 1]

        mean_abs_shap = np.abs(values).mean(axis=0)

        shap_importance = pd.DataFrame({
            "feature": X.columns,
            "impact": mean_abs_shap
        }).sort_values(by="impact", ascending=False)

        shap_importance = shap_importance.head(max_features).reset_index(drop=True)

        print("✅ SHAP calculado com sucesso!")
        print("\n📊 Importância global SHAP:")
        print(shap_importance)

        return shap_importance

    except Exception as e:
        print(f"⚠️ Erro ao calcular SHAP: {e}")
        return pd.DataFrame(columns=["feature", "impact"])