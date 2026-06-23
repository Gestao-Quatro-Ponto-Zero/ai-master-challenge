"""Simulating EXACT Streamlit flow to identify the problem"""

import sys
import os
sys.path.insert(0, os.getcwd())

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import importlib.util

def load_module(file_path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

print("=" * 70)
print("SIMULATING EXACT STREAMLIT FLOW")
print("=" * 70)

# Load modules exactly like Streamlit
preprocessing_module = load_module('01_data_preprocessing.py', 'preprocessing')
DataPreprocessor = preprocessing_module.DataPreprocessor

feature_engineering_module = load_module('02_feature_engineering.py', 'feature_engineering')
FeatureEngineer = feature_engineering_module.FeatureEngineer

risk_scoring_module = load_module('05_risk_scoring.py', 'risk_scoring')
RiskScoringEngine = risk_scoring_module.RiskScoringEngine

pdf_report_module = load_module('generate_pdf_report.py', 'pdf_report')
PDFReportGenerator = pdf_report_module.PDFReportGenerator

# Simulating @st.cache_resource load_data()
def load_data():
    """Load and preprocess data."""
    preprocessor = DataPreprocessor(data_path='data')
    raw_data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()
    
    engineer = FeatureEngineer(raw_data)
    processed_data = engineer.get_processed_data()
    
    risk_engine = RiskScoringEngine(processed_data)
    risk_engine.generate_risk_register()
    
    return processed_data, risk_engine.risk_register, risk_engine.get_risk_summary_stats(), raw_data

print("\n[STEP 1] Loading data...")
processed_data, risk_register, risk_stats, raw_data = load_data()
logger.info(f"[OK] Loaded: processed_data {processed_data.shape}, risk_register {risk_register.shape}, raw_data {raw_data.shape}")

# Simulating sidebar filters
print("\n[STEP 2] Applying sidebar filters...")
selected_industries = risk_register['industry'].unique()
selected_plan_tiers = risk_register['plan_tier'].unique()
selected_risk_tiers = ['Critical', 'High', 'Medium', 'Low']

# Apply filters
filtered_register = risk_register[
    (risk_register['industry'].isin(selected_industries)) &
    (risk_register['plan_tier'].isin(selected_plan_tiers)) &
    (risk_register['risk_tier'].isin(selected_risk_tiers))
]
logger.info(f"[OK] Filtered register shape: {filtered_register.shape}")

# Simulating PDF generation button click
print("\n[STEP 3] Clicking PDF generation button...")
print(f"[DEBUG] raw_data available: {raw_data is not None}")
print(f"[DEBUG] raw_data type: {type(raw_data)}")
print(f"[DEBUG] raw_data shape: {raw_data.shape}")
print(f"[DEBUG] filtered_register shape: {filtered_register.shape}")
print(f"[DEBUG] processed_data shape: {processed_data.shape}")

# Simulating st.session_state.simulator_results
simulator_results = []

report_gen = PDFReportGenerator(
    filtered_register, 
    processed_data, 
    simulator_results,
    raw_data  # PASSING raw_data
)

logger.info(f"[DEBUG] After PDFReportGenerator creation:")
logger.info(f"  merged_data: {report_gen.merged_data is not None}")
logger.info(f"  diagnostic_analysis: {report_gen.diagnostic_analysis is not None}")
logger.info(f"  diagnostic_results: {report_gen.diagnostic_results is not None}")

if report_gen.diagnostic_analysis:
    print("\nGenerating report...")
    pdf_path = report_gen.generate_report('outputs/streamlit_simulation.pdf')
    print(f"[OK] PDF generated: {pdf_path}")
    print(f"[OK] File size: {os.path.getsize(pdf_path)} bytes")
else:
    print("\n[ERROR] diagnostic_analysis is None, report will be in OLD FORMAT")
