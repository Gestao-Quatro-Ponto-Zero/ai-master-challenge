#!/usr/bin/env python3
"""
Master execution script for Ravenstack Churn Analysis Pipeline.
Runs all analysis, feature engineering, model training, and report generation.
"""

import os
import sys
import logging
import importlib.util
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_module(file_path, module_name):
    """Load a Python module from file path using importlib."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    """Execute full churn analysis pipeline."""
    
    logger.info("="*60)
    logger.info("RAVENSTACK CHURN ANALYSIS PIPELINE")
    logger.info("="*60)
    
    # Create outputs directory
    os.makedirs('outputs', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    
    try:
        # STEP 1: Data Preprocessing
        logger.info("\n[1/6] Loading and preprocessing data...")
        preprocessing_module = load_module('01_data_preprocessing.py', 'preprocessing')
        DataPreprocessor = preprocessing_module.DataPreprocessor
        
        preprocessor = DataPreprocessor(data_path='data')
        raw_data = (preprocessor
                   .load_raw_data()
                   .merge_datasets()
                   .handle_missing_values()
                   .get_merged_data())
        preprocessor.save_preprocessed_data()
        
        print(f"[OK] Preprocessing complete. Data shape: {raw_data.shape}")
        
        # STEP 2: Feature Engineering
        logger.info("\n[2/6] Engineering features...")
        feature_engineering_module = load_module('02_feature_engineering.py', 'feature_engineering')
        FeatureEngineer = feature_engineering_module.FeatureEngineer
        
        engineer = FeatureEngineer(raw_data)
        processed_data = engineer.get_processed_data()
        engineer.save_features()
        
        print(f"[OK] Feature engineering complete. Features: {processed_data.shape[1]} total")
        
        # STEP 3: Root Cause Analysis
        logger.info("\n[3/6] Analyzing root causes...")
        root_cause_module = load_module('03_root_cause_analysis.py', 'root_cause_analysis')
        RootCauseAnalysis = root_cause_module.RootCauseAnalysis
        
        analyzer = RootCauseAnalysis(raw_data)
        (analyzer
         .analyze_feature_adoption_gap()
         .analyze_support_quality()
         .analyze_pricing_patterns()
         .analyze_time_to_value()
         .analyze_industry_geography()
         .analyze_churn_reasons()
         .generate_summary_report()
         .save_analysis())
        
        summary = analyzer.results.get('summary', {})
        print(f"[OK] Root cause analysis complete.")
        if 'primary_causes' in summary:
            print(f"   Primary causes found: {len(summary['primary_causes'])}")
        
        # STEP 4: Model Training
        logger.info("\n[4/6] Training churn prediction models...")
        model_training_module = load_module('04_model_training.py', 'model_training')
        ChurnModelTrainer = model_training_module.ChurnModelTrainer
        from sklearn.metrics import roc_auc_score
        
        trainer = ChurnModelTrainer(processed_data)
        (trainer
         .prepare_features()
         .train_test_split_time_based()
         .train_xgboost()
         .train_lightgbm()
         .create_ensemble())
        
        # Get SHAP explanations
        trainer, shap_vals, feat_imp = trainer.explain_model_with_shap()
        
        # Save models
        trainer.save_models()
        
        # Print metrics
        xgb_auc = roc_auc_score(trainer.y_test, trainer.xgb_model.predict_proba(trainer.X_test)[:, 1])
        lgb_auc = roc_auc_score(trainer.y_test, trainer.lgb_model.predict_proba(trainer.X_test)[:, 1])
        ensemble_auc = roc_auc_score(trainer.y_test, trainer.ensemble_predictions)
        
        print(f"[OK] Model training complete.")
        print(f"   XGBoost AUC: {xgb_auc:.4f}")
        print(f"   LightGBM AUC: {lgb_auc:.4f}")
        print(f"   Ensemble AUC: {ensemble_auc:.4f}")
        
        # STEP 5: Risk Scoring
        logger.info("\n[5/6] Generating risk register...")
        risk_scoring_module = load_module('05_risk_scoring.py', 'risk_scoring')
        RiskScoringEngine = risk_scoring_module.RiskScoringEngine
        
        risk_engine = RiskScoringEngine(processed_data)
        risk_engine.generate_risk_register().save_risk_register()
        
        stats = risk_engine.get_risk_summary_stats()
        print(f"[OK] Risk scoring complete.")
        print(f"   Critical Risk: {stats['critical_risk_count']} accounts (${stats['revenue_at_critical_risk']:,.0f} ARR)")
        print(f"   High Risk: {stats['high_risk_count']} accounts (${stats['revenue_at_high_risk']:,.0f} ARR)")
        print(f"   Average Churn Probability: {stats['avg_churn_probability']*100:.1f}%")
        
        # STEP 6: PDF Report Generation
        logger.info("\n[6/6] Generating PDF report...")
        pdf_module = load_module('generate_pdf_report.py', 'generate_pdf_report')
        PDFReportGenerator = pdf_module.PDFReportGenerator
        
        report_gen = PDFReportGenerator(risk_engine.risk_register, processed_data)
        report_path = report_gen.generate_report()
        
        print(f"[OK] PDF report generated: {report_path}")
        
        # COMPLETION
        logger.info("\n" + "="*60)
        logger.info("PIPELINE COMPLETE")
        logger.info("="*60)
        
        print(f"\n[SUMMARY OF OUTPUTS]:")
        print(f"  1. Preprocessed Data: outputs/preprocessed_data.csv")
        print(f"  2. Engineered Features: outputs/features_engineered.csv")
        print(f"  3. Root Cause Analysis: outputs/root_cause_analysis.json")
        print(f"  4. Trained Models: models/xgb_model.pkl, models/lgb_model.pkl")
        print(f"  5. Risk Register: outputs/risk_register.csv")
        print(f"  6. PDF Report: outputs/churn_analysis_report.pdf")
        print(f"\n[NEXT STEPS]:")
        print(f"  - Run: streamlit run app.py")
        print(f"  - Open: http://localhost:8501")
        print(f"  - Interactive dashboard with scenario simulator ready!")
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\n[ERROR] PIPELINE FAILED: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
