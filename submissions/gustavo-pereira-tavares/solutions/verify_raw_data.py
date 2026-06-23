"""Quick debug to verify raw_data is loaded in Streamlit context"""

import sys
import os
sys.path.insert(0, os.getcwd())

import importlib.util

def load_module(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

preprocessing_module = load_module('01_data_preprocessing.py', 'preprocessing')
DataPreprocessor = preprocessing_module.DataPreprocessor

feature_engineering_module = load_module('02_feature_engineering.py', 'feature_engineering')
FeatureEngineer = feature_engineering_module.FeatureEngineer

risk_scoring_module = load_module('05_risk_scoring.py', 'risk_scoring')
RiskScoringEngine = risk_scoring_module.RiskScoringEngine

# Simulating the exact code from app.py load_data()
def load_data():
    """Load and preprocess data."""
    preprocessor = DataPreprocessor(data_path='data')
    raw_data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()
    
    engineer = FeatureEngineer(raw_data)
    processed_data = engineer.get_processed_data()
    
    risk_engine = RiskScoringEngine(processed_data)
    risk_engine.generate_risk_register()
    
    return processed_data, risk_engine.risk_register, risk_engine.get_risk_summary_stats(), raw_data

# Call it like Streamlit does
processed_data, risk_register, risk_stats, raw_data = load_data()

print(f"raw_data type: {type(raw_data)}")
print(f"raw_data is None: {raw_data is None}")
print(f"raw_data shape: {raw_data.shape if raw_data is not None else 'None'}")

# Now let's check what happens in PDFReportGenerator
pdf_report_module = load_module('generate_pdf_report.py', 'pdf_report')
PDFReportGenerator = pdf_report_module.PDFReportGenerator

print(f"\nCreating PDFReportGenerator with raw_data...")
report_gen = PDFReportGenerator(
    risk_register,
    processed_data,
    [],
    raw_data  # This should NOT be None
)

print(f"report_gen.merged_data is None: {report_gen.merged_data is None}")
print(f"report_gen.diagnostic_analysis is None: {report_gen.diagnostic_analysis is None}")
print(f"report_gen.diagnostic_results is None: {report_gen.diagnostic_results is None}")
