"""DealSignal V2 — Feature Engineering Experiments
=================================================

Executa 8 grupos de experimentos de forma organizada e comparável:

  1. Análise das features existentes (correlação, variância, redundância)
  2. Features derivadas (within-seller/product percentiles, etc.)
  3. Buckets (deal_age, deal_value, account_size)
  4. Flags de risco (deal_estagnado, deal_muito_antigo, etc.)
  5. Interações entre features
  6. Comparação de modelos (LR, RF, GBM)
  7. Ablation study por grupo de features
  8. Conclusão: limite de sinal do dataset

Uso:
    cd solution/dealsignal
    python -m experiments.v2_experiments

Saída (em experiments/results/):
    comparison_table.csv   — AUC por experimento
    ablation_table.csv     — AUC por grupo de features
    feature_importance.csv — features mais importantes
    feature_analysis.csv   — correlação/variância/redundância
    summary.txt            — conclusão em texto
"""

import sys
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

# Resolve paths
EXPERIMENTS_DIR = Path(__file__).parent
ROOT = EXPERIMENTS_DIR.parent
sys.path.insert(0, str(ROOT))

from features.feature_engineering import build_features
from features.interaction_features import (
    ABLATION_GROUPS,
    FEATURE_COLS_V2,
    FEATURE_COLS_V3,
    add_v3_features,
)
from model.feature_selection_iv import select_features_by_iv
from model.woe_transformer import WoETransformer

DATA_DIR = ROOT / "data"
OUTPUT_DIR = EXPERIMENTS_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

CV_FOLDS = 5
RANDOM_STATE = 42
IV_THRESHOLD = 0.02


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Data loading
# ═══════════════════════════════════════════════════════════════════════════════

def load_and_build_features() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Load CSVs, run V2 feature engineering, add V3 features."""
    print("▶ Carregando dados e construindo features...")
    accounts = pd.read_csv(DATA_DIR / "accounts.csv")
    products  = pd.read_csv(DATA_DIR / "products.csv")
    pipeline  = pd.read_csv(DATA_DIR / "sales_pipeline.csv")
    teams     = pd.read_csv(DATA_DIR / "sales_teams.csv")
    enriched  = pd.read_csv(DATA_DIR / "enriched_accounts.csv")

    feature_df, target = build_features(pipeline, accounts, products, teams, enriched)

    train_mask = target.notna()
    feature_df = add_v3_features(feature_df, train_mask)

    print(f"   Train (Won/Lost): {train_mask.sum():,} | Score (open): {(~train_mask).sum():,}")
    print(f"   Features V2: {len(FEATURE_COLS_V2)} | Features V3: {len(FEATURE_COLS_V3)}")
    return feature_df, target, train_mask


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Cross-validated AUC — core helper
# ═══════════════════════════════════════════════════════════════════════════════

def cv_auc(X: pd.DataFrame, y: pd.Series, estimator, n_splits: int = CV_FOLDS) -> dict:
    """Return mean CV AUC-ROC and Average Precision."""
    available = [c for c in X.columns if c in X.columns]
    X_clean = X[available].fillna(X[available].median())

    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_validate(
        estimator, X_clean, y,
        cv=cv,
        scoring={"auc": "roc_auc", "ap": "average_precision"},
        n_jobs=-1,
        error_score="raise",
    )
    return {
        "cv_auc_mean": scores["test_auc"].mean(),
        "cv_auc_std":  scores["test_auc"].std(),
        "cv_ap_mean":  scores["test_ap"].mean(),
        "cv_ap_std":   scores["test_ap"].std(),
    }


def make_lr() -> Pipeline:
    return Pipeline([
        ("scaler", StandardScaler()),
        ("clf",    LogisticRegression(
            C=1.0,
            class_weight="balanced",
            solver="lbfgs",
            max_iter=1000,
            random_state=RANDOM_STATE,
        )),
    ])


def make_rf() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        min_samples_leaf=20,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )


def make_gbm() -> GradientBoostingClassifier:
    return GradientBoostingClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        min_samples_leaf=20,
        random_state=RANDOM_STATE,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Experimento 1 — Análise das features existentes
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_features(X_train: pd.DataFrame, y_train: pd.Series) -> pd.DataFrame:
    """Compute variance, IV, and top correlations for all V3 features."""
    print("\n▶ Exp 1 — Análise das features existentes...")

    available = [c for c in FEATURE_COLS_V3 if c in X_train.columns]
    X = X_train[available].fillna(X_train[available].median())

    rows = []
    for col in available:
        variance = X[col].var()
        n_unique  = X[col].nunique()
        corr_target = X[col].corr(y_train)
        rows.append({
            "feature":      col,
            "variance":     round(variance, 6),
            "n_unique":     n_unique,
            "corr_target":  round(corr_target, 4),
        })

    analysis = pd.DataFrame(rows).sort_values("corr_target", key=abs, ascending=False)

    # Highly correlated pairs (|r| > 0.85)
    corr_matrix = X.corr().abs()
    high_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            r = corr_matrix.iloc[i, j]
            if r > 0.85:
                high_corr_pairs.append((
                    corr_matrix.columns[i],
                    corr_matrix.columns[j],
                    round(r, 3),
                ))

    if high_corr_pairs:
        print(f"   Features altamente correlacionadas (|r| > 0.85): {len(high_corr_pairs)} pares")
        for a, b, r in high_corr_pairs[:10]:
            print(f"     {a} ↔ {b}: r={r}")
    else:
        print("   Nenhum par com |r| > 0.85")

    # Low variance features (variance < 0.01)
    low_var = analysis[analysis["variance"] < 0.01]["feature"].tolist()
    if low_var:
        print(f"   Baixa variância (< 0.01): {low_var}")

    # WoE / IV
    woe = WoETransformer(n_bins=10)
    woe.fit(X, y_train)
    iv_df = pd.DataFrame(list(woe.iv_scores_.items()), columns=["feature", "iv"])
    analysis = analysis.merge(iv_df, on="feature", how="left")
    analysis["iv_label"] = analysis["iv"].apply(_iv_label)

    print(f"\n   Top 10 features por |corr com target|:")
    print(analysis[["feature", "corr_target", "iv", "variance"]].head(10).to_string(index=False))

    analysis.to_csv(OUTPUT_DIR / "feature_analysis.csv", index=False)
    print(f"   → Salvo: experiments/results/feature_analysis.csv")
    return analysis


def _iv_label(iv: float) -> str:
    if iv >= 0.3:  return "Strong"
    if iv >= 0.1:  return "Medium"
    if iv >= 0.02: return "Weak"
    return "Useless"


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Experimentos 2–5 — Comparação de feature sets com LR
# ═══════════════════════════════════════════════════════════════════════════════

def run_feature_set_experiments(X_train: pd.DataFrame, y_train: pd.Series) -> list[dict]:
    """LR com diferentes conjuntos de features: baseline WoE, V2, V3."""
    results = []

    # ── Baseline: WoE + IV + 3 features (pipeline atual) ────────────────────
    print("\n▶ Exp Baseline — LR + WoE + IV (pipeline atual)...")
    feat_v2_avail = [c for c in FEATURE_COLS_V2 if c in X_train.columns]
    X_v2 = X_train[feat_v2_avail].fillna(X_train[feat_v2_avail].median())

    woe = WoETransformer(n_bins=10)
    woe.fit(X_v2, y_train)
    selected = select_features_by_iv(woe.iv_scores_, threshold=IV_THRESHOLD)
    if not selected:
        selected = feat_v2_avail
    X_woe = woe.transform(X_v2[selected])
    lr_base = LogisticRegression(C=1.0, class_weight="balanced", solver="lbfgs",
                                 max_iter=1000, random_state=RANDOM_STATE)
    scores_base = cv_auc(X_woe, y_train, lr_base)
    results.append({
        "experimento": "1. Baseline LR + WoE + IV",
        "features_input": len(feat_v2_avail),
        "features_selecionadas": len(selected),
        "modelo": "LogisticRegression",
        "feature_set": "V2 (WoE+IV)",
        **scores_base,
    })
    print(f"   AUC={scores_base['cv_auc_mean']:.4f} ± {scores_base['cv_auc_std']:.4f}  "
          f"[{len(selected)} features selecionadas de {len(feat_v2_avail)}]")

    # ── LR + todas as V2 sem WoE ─────────────────────────────────────────────
    print("▶ Exp 2a — LR + todas as V2 features (sem WoE)...")
    scores = cv_auc(X_v2, y_train, make_lr())
    results.append({
        "experimento": "2a. LR + V2 features (sem WoE)",
        "features_input": len(feat_v2_avail),
        "features_selecionadas": len(feat_v2_avail),
        "modelo": "LogisticRegression",
        "feature_set": "V2",
        **scores,
    })
    print(f"   AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}")

    # ── LR + todas as V3 features (derivadas + buckets + flags + interações) ─
    print("▶ Exp 2b — LR + V3 features (todas as novas)...")
    feat_v3_avail = [c for c in FEATURE_COLS_V3 if c in X_train.columns]
    X_v3 = X_train[feat_v3_avail].fillna(X_train[feat_v3_avail].median())
    scores = cv_auc(X_v3, y_train, make_lr())
    results.append({
        "experimento": "2b. LR + V3 features (todas)",
        "features_input": len(feat_v3_avail),
        "features_selecionadas": len(feat_v3_avail),
        "modelo": "LogisticRegression",
        "feature_set": "V3",
        **scores,
    })
    print(f"   AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}")

    # ── LR + apenas features derivadas (novas, excl. V2 originals) ───────────
    print("▶ Exp 2c — LR + apenas features novas (derivadas + buckets + flags + interações)...")
    new_only = [
        "deal_value_percentile_within_seller", "deal_value_percentile_within_product",
        "deal_value_vs_account_size", "seller_product_win_rate",
        "product_relative_performance",
        "bucket_deal_age", "bucket_deal_value", "bucket_account_size",
        "deal_estagnado", "deal_muito_antigo", "produto_fraco", "conta_fraca",
        "interact_seller_product", "interact_seller_value",
        "interact_product_age", "interact_account_value",
    ]
    new_avail = [c for c in new_only if c in X_train.columns]
    X_new = X_train[new_avail].fillna(X_train[new_avail].median())
    if new_avail:
        scores = cv_auc(X_new, y_train, make_lr())
        results.append({
            "experimento": "2c. LR + apenas features novas",
            "features_input": len(new_avail),
            "features_selecionadas": len(new_avail),
            "modelo": "LogisticRegression",
            "feature_set": "New only",
            **scores,
        })
        print(f"   AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Experimento 6 — Comparação de modelos
# ═══════════════════════════════════════════════════════════════════════════════

def run_model_comparison(X_train: pd.DataFrame, y_train: pd.Series) -> list[dict]:
    """Compare LR, RF, GBM on V3 feature set."""
    print("\n▶ Exp 6 — Comparação de modelos (LR, RF, GBM)...")
    feat_v3_avail = [c for c in FEATURE_COLS_V3 if c in X_train.columns]
    X = X_train[feat_v3_avail].fillna(X_train[feat_v3_avail].median())

    models = [
        ("LogisticRegression", make_lr()),
        ("RandomForest",       make_rf()),
        ("GradientBoosting",   make_gbm()),
    ]

    results = []
    for name, estimator in models:
        print(f"   {name}...", end=" ", flush=True)
        scores = cv_auc(X, y_train, estimator)
        results.append({
            "experimento": f"6. {name} + V3",
            "features_input": len(feat_v3_avail),
            "features_selecionadas": len(feat_v3_avail),
            "modelo": name,
            "feature_set": "V3",
            **scores,
        })
        print(f"AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}")

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Experimento 7 — Ablation study
# ═══════════════════════════════════════════════════════════════════════════════

def run_ablation_study(X_train: pd.DataFrame, y_train: pd.Series) -> pd.DataFrame:
    """Evaluate each feature group independently + all combined."""
    print("\n▶ Exp 7 — Ablation study por grupo de features...")

    rows = []
    for group_name, group_cols in ABLATION_GROUPS.items():
        avail = [c for c in group_cols if c in X_train.columns]
        if not avail:
            print(f"   [{group_name}] — nenhuma feature disponível, pulando")
            continue

        X_group = X_train[avail].fillna(X_train[avail].median())

        # Use RF for ablation — more robust to feature scale and number
        scores = cv_auc(X_group, y_train, make_rf())
        rows.append({
            "grupo":              group_name,
            "n_features":         len(avail),
            "features":           ", ".join(avail),
            "cv_auc_mean":        round(scores["cv_auc_mean"], 4),
            "cv_auc_std":         round(scores["cv_auc_std"], 4),
            "cv_ap_mean":         round(scores["cv_ap_mean"], 4),
        })
        print(f"   [{group_name:12s}] n={len(avail):2d}  "
              f"AUC={scores['cv_auc_mean']:.4f} ± {scores['cv_auc_std']:.4f}  "
              f"AP={scores['cv_ap_mean']:.4f}")

    ablation_df = pd.DataFrame(rows).sort_values("cv_auc_mean", ascending=False)
    ablation_df.to_csv(OUTPUT_DIR / "ablation_table.csv", index=False)
    print(f"   → Salvo: experiments/results/ablation_table.csv")
    return ablation_df


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Feature importance — RF + GBM treinados no conjunto completo V3
# ═══════════════════════════════════════════════════════════════════════════════

def compute_feature_importance(X_train: pd.DataFrame, y_train: pd.Series) -> pd.DataFrame:
    """Train RF and GBM on full train set; extract and rank feature importances."""
    print("\n▶ Feature importance (RF + GBM)...")
    feat_v3_avail = [c for c in FEATURE_COLS_V3 if c in X_train.columns]
    X = X_train[feat_v3_avail].fillna(X_train[feat_v3_avail].median())

    rf = make_rf()
    rf.fit(X, y_train)
    rf_imp = pd.Series(rf.feature_importances_, index=feat_v3_avail).rename("rf_importance")

    gbm = make_gbm()
    gbm.fit(X, y_train)
    gbm_imp = pd.Series(gbm.feature_importances_, index=feat_v3_avail).rename("gbm_importance")

    importance_df = (
        pd.concat([rf_imp, gbm_imp], axis=1)
        .assign(avg_importance=lambda d: (d["rf_importance"] + d["gbm_importance"]) / 2)
        .sort_values("avg_importance", ascending=False)
        .reset_index()
        .rename(columns={"index": "feature"})
    )
    importance_df["rf_importance"]  = importance_df["rf_importance"].round(5)
    importance_df["gbm_importance"] = importance_df["gbm_importance"].round(5)
    importance_df["avg_importance"] = importance_df["avg_importance"].round(5)

    importance_df.to_csv(OUTPUT_DIR / "feature_importance.csv", index=False)
    print(f"   Top 15 features por importância média (RF+GBM):")
    print(importance_df[["feature", "avg_importance", "rf_importance", "gbm_importance"]].head(15).to_string(index=False))
    print(f"   → Salvo: experiments/results/feature_importance.csv")
    return importance_df


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Consolidação e relatório final
# ═══════════════════════════════════════════════════════════════════════════════

def consolidate_results(exp_results: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(exp_results)
    for col in ["cv_auc_mean", "cv_auc_std", "cv_ap_mean", "cv_ap_std"]:
        if col in df.columns:
            df[col] = df[col].round(4)
    df = df.sort_values("cv_auc_mean", ascending=False)
    df.to_csv(OUTPUT_DIR / "comparison_table.csv", index=False)
    return df


def write_summary(
    comparison: pd.DataFrame,
    ablation: pd.DataFrame,
    importance: pd.DataFrame,
    baseline_auc: float,
) -> None:
    best = comparison.iloc[0]
    best_group = ablation.iloc[0]
    top5_features = importance.head(5)["feature"].tolist()

    summary = f"""
DealSignal V2 — Resultado dos Experimentos
===========================================
Data: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

BASELINE (pipeline atual)
  Modelo:  LR + WoE + IV (3 features: seller_win_rate, seller_rank_percentile, log_days_since_engage)
  CV AUC:  {baseline_auc:.4f}

MELHOR EXPERIMENTO
  Modelo:  {best['modelo']}
  Features: {best['feature_set']} ({int(best['features_selecionadas'])} features)
  CV AUC:  {best['cv_auc_mean']:.4f} ± {best['cv_auc_std']:.4f}
  Delta vs baseline: {best['cv_auc_mean'] - baseline_auc:+.4f}

MELHOR GRUPO DE FEATURES (ablation)
  Grupo:   {best_group['grupo']}
  N:       {int(best_group['n_features'])}
  AUC:     {best_group['cv_auc_mean']:.4f} ± {best_group['cv_auc_std']:.4f}

TOP 5 FEATURES MAIS IMPORTANTES (RF+GBM)
  {chr(10).join(f'  {i+1}. {f}' for i, f in enumerate(top5_features))}

TABELA COMPARATIVA COMPLETA
{comparison[['experimento', 'features_selecionadas', 'modelo', 'cv_auc_mean', 'cv_auc_std', 'cv_ap_mean']].to_string(index=False)}

ABLATION STUDY
{ablation[['grupo', 'n_features', 'cv_auc_mean', 'cv_auc_std']].to_string(index=False)}

CONCLUSÃO
---------
O dataset possui {_signal_conclusion(baseline_auc, best['cv_auc_mean'])}

A engenharia de features {'conseguiu' if best['cv_auc_mean'] - baseline_auc > 0.01 else 'não conseguiu significativamente'} elevar o AUC sem adicionar novos dados externos.
Delta AUC = {best['cv_auc_mean'] - baseline_auc:+.4f} (baseline → melhor modelo).

Os grupos com mais sinal: {', '.join(ablation.head(3)['grupo'].tolist())}
"""
    with open(OUTPUT_DIR / "summary.txt", "w", encoding="utf-8") as f:
        f.write(summary)

    print("\n" + "═" * 60)
    print(summary)
    print(f"→ Salvo: experiments/results/summary.txt")


def _signal_conclusion(baseline_auc: float, best_auc: float) -> str:
    delta = best_auc - baseline_auc
    if best_auc >= 0.75:
        return "sinal moderado-alto (AUC ≥ 0.75)."
    if best_auc >= 0.65:
        return "sinal moderado (AUC 0.65–0.75). Melhorias de feature engineering ajudam, mas o teto está próximo."
    return ("sinal limitado (AUC < 0.65). O dataset sintético tem variabilidade insuficiente "
            "para discriminação mais precisa — novos dados externos seriam necessários para avançar.")


# ═══════════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("=" * 60)
    print("DealSignal V2 — Experimentos de Feature Engineering")
    print("=" * 60)

    # 1. Load data & build features
    feature_df, target, train_mask = load_and_build_features()

    train_df = feature_df[train_mask].copy()
    y_train  = target[train_mask].astype(int)

    all_v3_avail = [c for c in FEATURE_COLS_V3 if c in train_df.columns]
    X_train = train_df[all_v3_avail]

    # 2. Feature analysis
    feature_analysis = analyze_features(X_train, y_train)

    all_results = []

    # 3. Feature-set experiments (LR): baseline + V2 + V3 + new-only
    all_results += run_feature_set_experiments(train_df, y_train)

    # 4. Model comparison (LR, RF, GBM) — all on V3
    all_results += run_model_comparison(train_df, y_train)

    # 5. Ablation study (RF per group)
    ablation_df = run_ablation_study(train_df, y_train)

    # 6. Feature importance (RF + GBM full fit)
    importance_df = compute_feature_importance(train_df, y_train)

    # 7. Consolidate and write outputs
    comparison_df = consolidate_results(all_results)

    # Baseline AUC from metadata (or from experiment results)
    metadata_path = ROOT / "model" / "artifacts" / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path) as f:
            meta = json.load(f)
        baseline_auc = meta.get("cv_auc", 0.6241)
    else:
        baseline_row = comparison_df[comparison_df["feature_set"] == "V2 (WoE+IV)"]
        baseline_auc = baseline_row["cv_auc_mean"].iloc[0] if len(baseline_row) else 0.6241

    write_summary(comparison_df, ablation_df, importance_df, baseline_auc)

    print(f"\n✓ Todos os resultados salvos em: {OUTPUT_DIR}/")
    print(f"  comparison_table.csv  — AUC por experimento")
    print(f"  ablation_table.csv    — AUC por grupo de features")
    print(f"  feature_importance.csv— importância de features")
    print(f"  feature_analysis.csv  — correlação/variância/IV")
    print(f"  summary.txt           — conclusão")


if __name__ == "__main__":
    main()
