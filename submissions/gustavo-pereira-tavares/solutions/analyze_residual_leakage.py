import pandas as pd
import numpy as np
import importlib.util

spec_prep = importlib.util.spec_from_file_location("preprocessing", "01_data_preprocessing.py")
preprocessing = importlib.util.module_from_spec(spec_prep)
spec_prep.loader.exec_module(preprocessing)

spec_eng = importlib.util.spec_from_file_location("engineering", "02_feature_engineering.py")
engineering = importlib.util.module_from_spec(spec_eng)
spec_eng.loader.exec_module(engineering)

print("="*70)
print("INVESTIGAÇÃO DE DATA LEAKAGE EM FEATURES REMANESCENTES")
print("="*70)
print()

preprocessor = preprocessing.DataPreprocessor('data')
raw_data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()

engineer = engineering.FeatureEngineer(raw_data)
processed = engineer.get_processed_data()

print("1. ANÁLISE DE FEATURES TEMPORAIS")
print("-" * 70)
print()

# Verificar datas
date_cols = ['usage_date', 'last_usage_date', 'first_usage_date', 'churn_date', 'start_date']
print("Data ranges nos datasets originais:")
for col in date_cols:
    if col in raw_data.columns:
        print(f"  {col}: {raw_data[col].min()} a {raw_data[col].max()}")
print()

# Verificar correlação de features com churn
print("2. FEATURES COM MAIOR CORRELAÇÃO COM CHURN")
print("-" * 70)
print()

numeric_cols = processed.select_dtypes(include=[np.number]).columns
correlations = {}
for col in numeric_cols:
    if col != 'churn_flag':
        corr = processed[col].corr(processed['churn_flag'])
        if not np.isnan(corr):
            correlations[col] = corr

sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
print("Top 15 features mais correlacionadas com churn:")
for i, (feat, corr) in enumerate(sorted_corr[:15], 1):
    print(f"  {i:2d}. {feat:40s} -> {corr:+.4f}")
print()

print("3. ANÁLISE DE FEATURES DE USO")
print("-" * 70)
print()

# Analisar features de uso
usage_features = ['usage_intensity', 'days_since_last_use', 'adoption_rate', 'usage_days']
for feat in usage_features:
    if feat in processed.columns:
        print(f"{feat}:")
        print(f"  Churn=0:   mean={processed[processed['churn_flag']==0][feat].mean():.2f}, std={processed[processed['churn_flag']==0][feat].std():.2f}")
        print(f"  Churn=1:   mean={processed[processed['churn_flag']==1][feat].mean():.2f}, std={processed[processed['churn_flag']==1][feat].std():.2f}")
        print()

print("4. ANÁLISE DE FEATURES DE SUPORTE")
print("-" * 70)
print()

support_features = ['support_ticket_count', 'avg_resolution_time', 'avg_satisfaction_score']
for feat in support_features:
    if feat in processed.columns:
        print(f"{feat}:")
        print(f"  Churn=0:   mean={processed[processed['churn_flag']==0][feat].mean():.2f}")
        print(f"  Churn=1:   mean={processed[processed['churn_flag']==1][feat].mean():.2f}")
        print()

print("5. POSSÍVEL DATA LEAKAGE RESIDUAL - FEATURES SUSPEITAS")
print("-" * 70)
print()

suspicious_features = {
    'days_since_last_use': 'Se > 60, pode ser que cliente já est abandonando',
    'support_ticket_count': 'Pode incluir tickets pós-churn?',
    'avg_resolution_time': 'Tickets após churn podem afetar média?',
    'adoption_rate': 'Uso próximo à data de churn?'
}

for feat, reason in suspicious_features.items():
    if feat in processed.columns:
        print(f"[SUSPICIOUS] {feat}")
        print(f"  Motivo: {reason}")
        churn_1 = processed[processed['churn_flag']==1][feat]
        churn_0 = processed[processed['churn_flag']==0][feat]
        print(f"  Churn=1: median={churn_1.median():.2f}, Q1={churn_1.quantile(0.25):.2f}, Q3={churn_1.quantile(0.75):.2f}")
        print(f"  Churn=0: median={churn_0.median():.2f}, Q1={churn_0.quantile(0.25):.2f}, Q3={churn_0.quantile(0.75):.2f}")
        print()

print("="*70)
print("RECOMENDAÇÕES")
print("="*70)
print()
print("1. Verificar se support_ticket_count inclui tickets posteriores a churn_date")
print("2. Validar se usage_date em feature_usage é anterior a churn_date")
print("3. Implementar cut-off date explícito (ex: predizer churn 30 dias no futuro)")
print("4. Considerar features como 'churn_score_immediately_before_churn'")
print("   como proxies de situação de risco genuína")
print()
