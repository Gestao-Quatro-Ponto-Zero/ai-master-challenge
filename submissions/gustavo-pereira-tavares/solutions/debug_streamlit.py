"""Debug script to understand what Streamlit is passing to PDFReportGenerator"""

import sys
import os
sys.path.insert(0, os.getcwd())

import importlib.util

def load_module(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

print("=" * 70)
print("DEBUGGING STREAMLIT PDF GENERATION")
print("=" * 70)

# Load modules exactly like Streamlit does
preprocessing_module = load_module('01_data_preprocessing.py', 'preprocessing')
DataPreprocessor = preprocessing_module.DataPreprocessor

feature_engineering_module = load_module('02_feature_engineering.py', 'feature_engineering')
FeatureEngineer = feature_engineering_module.FeatureEngineer

risk_scoring_module = load_module('05_risk_scoring.py', 'risk_scoring')
RiskScoringEngine = risk_scoring_module.RiskScoringEngine

pdf_report_module = load_module('generate_pdf_report.py', 'pdf_report')
PDFReportGenerator = pdf_report_module.PDFReportGenerator

print("\nLoading data...")
preprocessor = DataPreprocessor(data_path='data')
raw_data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()
print(f"[OK] raw_data shape: {raw_data.shape}")

engineer = FeatureEngineer(raw_data)
processed_data = engineer.get_processed_data()
print(f"[OK] processed_data shape: {processed_data.shape}")

risk_engine = RiskScoringEngine(processed_data)
risk_engine.generate_risk_register()
risk_register = risk_engine.risk_register
print(f"[OK] risk_register shape: {risk_register.shape}")
print(f"[OK] risk_register columns: {list(risk_register.columns)[:5]}...")

# Apply filters (like Streamlit does)
filtered_register = risk_register.copy()
print(f"[OK] filtered_register shape: {filtered_register.shape}")

print("\n" + "=" * 70)
print("TESTING SCENARIO 1: WITHOUT risk_register (like Streamlit might be doing)")
print("=" * 70)

report_gen1 = PDFReportGenerator(
    filtered_register, 
    processed_data, 
    [],
    None  # NOT passing raw_data
)

print(f"[FAIL] diagnostic_analysis: {report_gen1.diagnostic_analysis}")
print(f"[FAIL] diagnostic_results: {report_gen1.diagnostic_results}")
print(f"[RESULT] NO new format sections will be added\n")

print("=" * 70)
print("TESTING SCENARIO 2: WITH raw_data (correct implementation)")
print("=" * 70)

report_gen2 = PDFReportGenerator(
    filtered_register, 
    processed_data, 
    [],
    raw_data  # Passing raw_data
)

print(f"[PASS] diagnostic_analysis: {report_gen2.diagnostic_analysis is not None}")
print(f"[PASS] diagnostic_results: {report_gen2.diagnostic_results is not None}")
print(f"[RESULT] New format sections WILL be added\n")

print("=" * 70)
print("CHECKING: Is raw_data being passed by Streamlit?")
print("=" * 70)

# Look at app.py code
with open('app.py', 'r') as f:
    content = f.read()
    
if 'PDFReportGenerator(' in content:
    import re
    match = re.search(r'PDFReportGenerator\((.*?)\)', content, re.DOTALL)
    if match:
        args = match.group(1)
        print("\nPDFReportGenerator call in app.py:")
        print(args)
        
        if 'raw_data' in args:
            print("\n[PASS] raw_data IS in the arguments")
        else:
            print("\n[FAIL] raw_data IS NOT in the arguments")
