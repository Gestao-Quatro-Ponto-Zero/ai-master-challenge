import sys
import pandas as pd
import importlib.util

sys.path.insert(0, '.')

spec_prep = importlib.util.spec_from_file_location("preprocessing", "01_data_preprocessing.py")
preprocessing = importlib.util.module_from_spec(spec_prep)
spec_prep.loader.exec_module(preprocessing)

spec_eng = importlib.util.spec_from_file_location("engineering", "02_feature_engineering.py")
engineering = importlib.util.module_from_spec(spec_eng)
spec_eng.loader.exec_module(engineering)

spec_train = importlib.util.spec_from_file_location("training", "04_model_training.py")
training = importlib.util.module_from_spec(spec_train)
spec_train.loader.exec_module(training)

try:
    print('='*60)
    print('COMPLETE PIPELINE TEST WITH TEMPORAL VALIDATION')
    print('='*60)
    print()
    
    print('STEP 1: Loading and preprocessing data...')
    preprocessor = preprocessing.DataPreprocessor('data')
    raw_data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()
    print(f'[OK] Raw data loaded: {raw_data.shape}')
    print()
    
    print('STEP 2: Engineering features with temporal validation...')
    engineer = engineering.FeatureEngineer(raw_data)
    processed_data = engineer.get_processed_data()
    print(f'[OK] Features engineered: {processed_data.shape}')
    
    if engineer.temporal_validation_errors:
        print(f'[FAIL] VALIDATION FAILED: {engineer.temporal_validation_errors}')
        sys.exit(1)
    else:
        print('[OK] Temporal integrity check PASSED')
    print()
    
    print('STEP 3: Preparing features for modeling...')
    trainer = training.ChurnModelTrainer(processed_data)
    trainer.prepare_features()
    print(f'[OK] Features prepared: {len(trainer.feature_columns)} features')
    print(f'[OK] Target distribution: {trainer.y.value_counts().to_dict()}')
    print()
    
    print('STEP 4: Time-based train/test split...')
    trainer.train_test_split_time_based()
    print(f'[OK] Train set: {len(trainer.X_train)} samples (churn: {trainer.y_train.mean()*100:.1f}%)')
    print(f'[OK] Test set: {len(trainer.X_test)} samples (churn: {trainer.y_test.mean()*100:.1f}%)')
    print()
    
    print('STEP 5: Training XGBoost model...')
    trainer.train_xgboost()
    xgb_auc = __import__('sklearn.metrics', fromlist=['roc_auc_score']).roc_auc_score(
        trainer.y_test, trainer.xgb_model.predict_proba(trainer.X_test)[:, 1]
    )
    print(f'[OK] XGBoost AUC: {xgb_auc:.4f}')
    print()
    
    print('STEP 6: Training LightGBM model...')
    trainer.train_lightgbm()
    lgb_auc = __import__('sklearn.metrics', fromlist=['roc_auc_score']).roc_auc_score(
        trainer.y_test, trainer.lgb_model.predict_proba(trainer.X_test)[:, 1]
    )
    print(f'[OK] LightGBM AUC: {lgb_auc:.4f}')
    print()
    
    print('STEP 7: Creating ensemble...')
    trainer.create_ensemble()
    ensemble_auc = __import__('sklearn.metrics', fromlist=['roc_auc_score']).roc_auc_score(
        trainer.y_test, trainer.ensemble_predictions
    )
    print(f'[OK] Ensemble AUC: {ensemble_auc:.4f}')
    print()
    
    print('='*60)
    print('PIPELINE SUMMARY')
    print('='*60)
    print(f'XGBoost AUC:  {xgb_auc:.4f}')
    print(f'LightGBM AUC: {lgb_auc:.4f}')
    print(f'Ensemble AUC: {ensemble_auc:.4f}')
    print()
    print('Status: [OK] COMPLETE - All temporal validation passed')
    print('='*60)
        
except Exception as e:
    import traceback
    print(f'\n[ERROR]: {e}')
    traceback.print_exc()
    sys.exit(1)
