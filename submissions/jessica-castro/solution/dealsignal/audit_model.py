"""
DealSignal — Auditoria de AUC 0.624

Script de diagnóstico completo. Executa:
  1. Distribuição do target
  2. Split aleatório vs temporal
  3. Baselines feature única
  4. Ablation por grupo de features
  5. Modelos não-lineares
  6. Importância de features (Random Forest)
  7. Conclusão crítica

Uso:
    cd dealsignal
    python audit_model.py
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

from enrichment.digital_enrichment import run_enrichment
from features.feature_engineering import FEATURE_COLS_V2, build_features

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

SECTION_SEP = "=" * 60


def section(title: str) -> None:
    print(f"\n{SECTION_SEP}")
    print(f"  {title}")
    print(SECTION_SEP)


def auc_cv(model, X: pd.DataFrame, y: pd.Series, cv: int = 5) -> float:
    """Cross-validated AUC. Returns mean over folds."""
    cols = [c for c in X.columns if c in X.columns and X[c].notna().any()]
    X_filled = X[cols].fillna(X[cols].median())
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    scores = cross_val_score(model, X_filled, y, cv=skf, scoring="roc_auc", n_jobs=-1)
    return float(scores.mean())


def auc_holdout(model, X_tr, y_tr, X_te, y_te) -> float:
    """Train on train split, evaluate on holdout."""
    X_tr_f = X_tr.fillna(X_tr.median())
    X_te_f = X_te.fillna(X_tr.median())
    model.fit(X_tr_f, y_tr)
    proba = model.predict_proba(X_te_f)[:, 1]
    return float(roc_auc_score(y_te, proba))


def load_data() -> tuple:
    accounts = pd.read_csv(DATA_DIR / "accounts.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    pipeline = pd.read_csv(DATA_DIR / "sales_pipeline.csv")
    teams = pd.read_csv(DATA_DIR / "sales_teams.csv")
    enriched = run_enrichment(accounts, str(DATA_DIR / "enriched_accounts.csv"), force=False)
    return accounts, products, pipeline, teams, enriched


def main() -> None:
    print("\nDealSignal — Auditoria de AUC")
    print("Carregando dados e construindo features...")

    accounts, products, pipeline, teams, enriched = load_data()
    feature_df, target = build_features(pipeline, accounts, products, teams, enriched)

    # Train rows only (Won/Lost)
    train_mask = target.notna()
    df_train = feature_df[train_mask].copy()
    y = target[train_mask].astype(int)

    # Available V2 features in this dataset
    avail_v2 = [c for c in FEATURE_COLS_V2 if c in df_train.columns]
    X_v2 = df_train[avail_v2]

    # ── 1. Target distribution ───────────────────────────────────────────────
    section("1. DISTRIBUIÇÃO DO TARGET")
    won = int(y.sum())
    lost = int((y == 0).sum())
    total = won + lost
    print(f"  Won:       {won:>5d}  ({won/total*100:.1f}%)")
    print(f"  Lost:      {lost:>5d}  ({lost/total*100:.1f}%)")
    print(f"  Total:     {total:>5d}")
    print(f"  Taxa Win:  {won/total*100:.1f}%")

    # ── 2. Split aleatório vs temporal ───────────────────────────────────────
    section("2. SPLIT ALEATÓRIO vs TEMPORAL")

    lr_base = LogisticRegression(C=0.1, class_weight="balanced", solver="lbfgs",
                                  max_iter=500, random_state=42)
    auc_random = auc_cv(lr_base, X_v2, y, cv=5)
    print(f"  Split aleatório (5-fold CV):  AUC = {auc_random:.4f}")

    # Temporal split: train on oldest ~80%, test on newest ~20%
    engage_dates = pd.to_datetime(df_train["engage_date"], errors="coerce")
    cutoff = engage_dates.quantile(0.80)
    temp_train = engage_dates <= cutoff
    temp_test = engage_dates > cutoff

    if temp_test.sum() >= 10:
        X_t_tr = X_v2[temp_train].fillna(X_v2[temp_train].median())
        X_t_te = X_v2[temp_test].fillna(X_v2[temp_train].median())
        y_t_tr = y[temp_train]
        y_t_te = y[temp_test]

        engage_min = engage_dates.min().date() if pd.notna(engage_dates.min()) else "?"
        engage_max = engage_dates.max().date() if pd.notna(engage_dates.max()) else "?"
        cutoff_date = cutoff.date() if pd.notna(cutoff) else "?"

        print(f"  Intervalo: {engage_min} → {engage_max}  |  Corte: {cutoff_date}")
        print(f"  Train temporal: {temp_train.sum()} deals | Test temporal: {temp_test.sum()} deals")

        if len(y_t_te.unique()) > 1:
            lr_base_2 = LogisticRegression(C=0.1, class_weight="balanced", solver="lbfgs",
                                            max_iter=500, random_state=42)
            lr_base_2.fit(X_t_tr, y_t_tr)
            proba_te = lr_base_2.predict_proba(X_t_te)[:, 1]
            auc_temporal = roc_auc_score(y_t_te, proba_te)
            print(f"  Split temporal (holdout):    AUC = {auc_temporal:.4f}")
            if auc_temporal < auc_random - 0.05:
                print("  ⚠  AUC temporal significativamente menor — possível drift temporal")
            else:
                print("  ✓  AUC temporal consistente com split aleatório")
        else:
            print("  ⚠  Test temporal não tem os dois labels — pulando")
    else:
        print("  ⚠  Poucos dados no split temporal — pulando")

    # ── 3. Baselines — feature única ─────────────────────────────────────────
    section("3. BASELINES — FEATURE ÚNICA (sem WoE)")
    single_features = [
        "seller_win_rate",
        "deal_age_percentile",
        "deal_value_percentile",
        "log_days_since_engage",
        "is_stale_flag",
        "product_win_rate",
        "seller_rank_percentile",
    ]
    lr_single = LogisticRegression(C=1.0, class_weight="balanced", solver="lbfgs",
                                    max_iter=200, random_state=42)
    dummy = DummyClassifier(strategy="most_frequent")

    results_single = {}
    for feat in single_features:
        if feat not in df_train.columns:
            continue
        X_f = df_train[[feat]].fillna(df_train[[feat]].median())
        score = auc_cv(lr_single, X_f, y, cv=5)
        results_single[feat] = score

    results_single["Dummy (majority)"] = auc_cv(dummy, X_v2, y, cv=5)

    for feat, score in sorted(results_single.items(), key=lambda x: -x[1]):
        bar = "█" * int(score * 20)
        print(f"  {feat:<35s}  AUC = {score:.4f}  {bar}")

    # ── 4. Ablation — grupos de features ─────────────────────────────────────
    section("4. ABLATION — GRUPOS DE FEATURES (LR sem WoE)")
    grupos = {
        "Vendedor":   ["seller_win_rate", "seller_rank_percentile", "seller_close_speed", "seller_pipeline_load"],
        "Deal":       ["log_days_since_engage", "log_deal_value", "deal_value_percentile"],
        "Produto":    ["product_win_rate", "product_rank_percentile", "product_avg_sales_cycle"],
        "Risco":      ["is_stale_flag", "deal_age_percentile"],
        "Todas V2":   avail_v2,
    }

    lr_ablation = LogisticRegression(C=0.1, class_weight="balanced", solver="lbfgs",
                                      max_iter=500, random_state=42)
    results_ablation = {}
    for grupo, feats in grupos.items():
        avail = [f for f in feats if f in df_train.columns]
        if not avail:
            print(f"  {grupo:<20s}  — sem features disponíveis")
            continue
        X_g = df_train[avail].fillna(df_train[avail].median())
        score = auc_cv(lr_ablation, X_g, y, cv=5)
        results_ablation[grupo] = score

    for grupo, score in results_ablation.items():
        n_feats = len([f for f in grupos[grupo] if f in df_train.columns])
        bar = "█" * int(score * 20)
        print(f"  {grupo:<20s} ({n_feats:2d} features)  AUC = {score:.4f}  {bar}")

    # ── 5. Modelos não-lineares ───────────────────────────────────────────────
    section("5. MODELOS NÃO-LINEARES (todas features V2, sem WoE)")
    X_all = X_v2.fillna(X_v2.median())

    modelos = {
        "LogReg (C=0.01, balanced)": LogisticRegression(
            C=0.01, class_weight="balanced", solver="lbfgs", max_iter=500, random_state=42
        ),
        "LogReg (C=0.1, balanced)": LogisticRegression(
            C=0.1, class_weight="balanced", solver="lbfgs", max_iter=500, random_state=42
        ),
        "LogReg (C=1.0, sem balance)": LogisticRegression(
            C=1.0, solver="lbfgs", max_iter=500, random_state=42
        ),
        "Random Forest (100, balanced)": RandomForestClassifier(
            n_estimators=100, class_weight="balanced", random_state=42, n_jobs=-1
        ),
        "GradientBoosting (100)": GradientBoostingClassifier(
            n_estimators=100, random_state=42
        ),
    }
    if HAS_XGB:
        modelos["XGBoost"] = XGBClassifier(
            n_estimators=100, use_label_encoder=False, eval_metric="logloss",
            random_state=42, verbosity=0
        )

    results_models = {}
    for nome, modelo in modelos.items():
        skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        scores = cross_val_score(modelo, X_all, y, cv=skf, scoring="roc_auc", n_jobs=-1)
        results_models[nome] = float(scores.mean())

    for nome, score in sorted(results_models.items(), key=lambda x: -x[1]):
        bar = "█" * int(score * 20)
        print(f"  {nome:<40s}  AUC = {score:.4f}  {bar}")

    # ── 6. Feature importance (Random Forest) ────────────────────────────────
    section("6. FEATURE IMPORTANCE — Random Forest")
    rf = RandomForestClassifier(
        n_estimators=200, class_weight="balanced", random_state=42, n_jobs=-1
    )
    rf.fit(X_all, y)
    importances = sorted(
        zip(avail_v2, rf.feature_importances_), key=lambda x: -x[1]
    )
    for feat, imp in importances:
        bar = "█" * int(imp * 200)
        print(f"  {feat:<35s}  {imp:.4f}  {bar}")

    # ── 7. Correlação features com target ─────────────────────────────────────
    section("7. CORRELAÇÃO (Spearman) COM TARGET")
    for feat in avail_v2:
        col = pd.to_numeric(df_train[feat], errors="coerce")
        if col.notna().sum() < 10:
            continue
        corr = col.corr(y.astype(float), method="spearman")
        bar_len = int(abs(corr) * 30)
        direction = "+" if corr > 0 else "-"
        bar = direction * bar_len
        print(f"  {feat:<35s}  r = {corr:+.3f}  {bar}")

    # ── 8. Conclusão crítica ──────────────────────────────────────────────────
    section("8. CONCLUSÃO")

    best_model_auc = max(results_models.values()) if results_models else 0
    best_model_name = max(results_models, key=results_models.get) if results_models else "?"
    lr_v2_auc = results_ablation.get("Todas V2", 0)
    best_single = max(results_single.items(), key=lambda x: x[1]) if results_single else ("?", 0)
    best_group = max(results_ablation.items(), key=lambda x: x[1]) if results_ablation else ("?", 0)

    print(f"""
  Melhor feature única:    {best_single[0]} → AUC {best_single[1]:.4f}
  Melhor grupo:            {best_group[0]} → AUC {best_group[1]:.4f}
  LR todas V2 (sem WoE):  {lr_v2_auc:.4f}
  Melhor modelo:           {best_model_name} → AUC {best_model_auc:.4f}
""")

    gap_nonlinear = best_model_auc - lr_v2_auc
    print("  DIAGNÓSTICO:")
    if gap_nonlinear > 0.05:
        print(f"  → Modelos não-lineares ganham +{gap_nonlinear:.3f} sobre LR — problema NÃO É linear.")
        print("    Recomendação: usar GBM/XGBoost em vez de Logistic Regression.")
    else:
        print(f"  → Gap linear vs não-linear = {gap_nonlinear:+.3f} (pequeno).")
        print("    O problema é essencialmente linear — LR é escolha adequada.")

    if best_model_auc < 0.70:
        print()
        print("  → AUC < 0.70 mesmo com modelos não-lineares.")
        print("    Causa raiz provável: SINAL FRACO NAS FEATURES.")
        print("    As features atuais (win rates, deal age, deal size) não separam")
        print("    bem Won de Lost porque capturam características do vendedor/produto")
        print("    mas não da CONTA/OPORTUNIDADE específica.")
        print()
        print("  Recomendações para elevar AUC:")
        print("  1. Features de engajamento: nº de atividades, emails, calls recentes")
        print("  2. Features de progressão: mudanças de stage, velocidade de avanço")
        print("  3. Features da conta: setor, tamanho, histórico de deals anteriores")
        print("  4. Interações: seller_win_rate × product_win_rate, deal_size × seller_exp")
    elif best_model_auc < 0.80:
        print()
        print("  → AUC entre 0.70–0.80. Modelo com sinal moderado.")
        print("    Melhorias incrementais possíveis com feature engineering mais rico.")

    print()
    print(f"  Feature mais preditiva (RF):  {importances[0][0]}  ({importances[0][1]:.4f})")
    print(f"  Feature menos preditiva (RF): {importances[-1][0]}  ({importances[-1][1]:.4f})")

    low_importance = [f for f, imp in importances if imp < 0.02]
    if low_importance:
        print(f"\n  Features com importância < 0.02 (candidatas à remoção):")
        for f in low_importance:
            print(f"    - {f}")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()
