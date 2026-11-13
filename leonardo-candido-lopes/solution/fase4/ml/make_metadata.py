"""Gera model/model_metadata.json a partir dos resultados reais (evaluation/*.json)."""
import json, hashlib, datetime, sklearn, platform
R = json.load(open("evaluation/results.json")); D = json.load(open("evaluation/domain_detector_results.json")); A = json.load(open("splits/audit_results.json"))
sha = hashlib.sha256(open("../../data/all_tickets_processed_improved_v3.csv", "rb").read()).hexdigest()
T = R["thresholds"]
meta = dict(
    version="1.0.0", created_at=datetime.date.today().isoformat(), sklearn_version=sklearn.__version__, python=platform.python_version(),
    dataset=dict(path="data/all_tickets_processed_improved_v3.csv", sha256=sha, n_original=A["total_original"], n_clean=A["final_clean"], split_sizes=A["split_sizes"], seed=42),
    classifier=dict(file="classifier_pipeline.pkl", selected=R["best_by_val"], calibration=f"CalibratedClassifierCV(method='{R['calibration_choice']}', cv=5)",
                    tfidf=dict(max_features=50000, ngram_range=[1, 2], sublinear_tf=True, preprocessor="text_prep.preprocess"), classes=R["test"]["labels"]),
    test_metrics={k: R["test"][k] for k in ["n", "f1_macro", "f1_weighted", "accuracy", "ece", "dummy_f1_macro", "per_class"]},
    thresholds=dict(threshold_alto=T["threshold_alto"], threshold_baixo=T["threshold_baixo"], rule=T["rule"], test_at_alto=T["test_at_alto"], test_at_baixo=T["test_at_baixo"],
                    note="Metas de precisão (0,95 / 0,90) são proposta para validação de negócio; os limiares derivam delas empiricamente no conjunto de validação."),
    domain_detector=dict(file="domain_detector.pkl", t_uncertain=D["t_uncertain"], t_oos=D["t_oos"], abstain_quantile=D["abstain_quantile"], min_tokens=D["min_tokens"], val_f1_macro_at_0_5=D["val_f1_macro_at_0_5"],
                         warning="Validação perfeitamente separável (negativos sintéticos do D1). Métrica NÃO representa desempenho real; limiares = 1º percentil no val in-domain."),
    load_requirements="Os .pkl referenciam text_prep.py e domain_detector.py — mantenha-os no PYTHONPATH.")
json.dump(meta, open("model/model_metadata.json", "w"), indent=1, ensure_ascii=False)
print(meta["thresholds"]["threshold_baixo"], meta["thresholds"]["threshold_alto"])
