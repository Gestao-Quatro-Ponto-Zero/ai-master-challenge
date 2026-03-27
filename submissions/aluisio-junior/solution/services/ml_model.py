import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from xgboost import XGBClassifier


FEATURES = [
    "avg_mrr",
    "avg_arr",
    "avg_seats",
    "avg_usage_count",
    "avg_usage_duration",
    "avg_errors",
    "avg_resolution_time",
    "avg_first_response",
    "avg_satisfaction",
    "total_escalations"
]


def run_ml_model(df):
    print("\n🤖 INICIANDO MODELO DE CHURN\n")

    missing_features = [col for col in FEATURES if col not in df.columns]
    if missing_features:
        raise ValueError(f"❌ Features ausentes para o modelo: {missing_features}")

    if "churned" not in df.columns:
        raise ValueError("❌ Coluna alvo 'churned' não encontrada no dataset.")

    df_model = df[FEATURES + ["churned"]].copy().fillna(0)

    X = df_model[FEATURES]
    y = df_model["churned"]

    if y.nunique() < 2:
        raise ValueError("❌ A variável alvo 'churned' precisa ter pelo menos 2 classes.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=42,
        stratify=y
    )

    negative = (y_train == 0).sum()
    positive = (y_train == 1).sum()
    scale_pos_weight = (negative / positive) if positive > 0 else 1.0

    model = XGBClassifier(
        n_estimators=250,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    print(f"\n🎯 Acurácia do modelo: {acc:.2%}")
    print(f"📈 ROC AUC: {auc:.4f}\n")

    print("📊 Classification Report:")
    print(classification_report(y_test, y_pred))

    importance = pd.DataFrame({
        "feature": FEATURES,
        "importance": model.feature_importances_
    }).sort_values(by="importance", ascending=False).reset_index(drop=True)

    print("\n🔥 Importância das variáveis:")
    print(importance)

    return model, importance