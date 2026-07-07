import sys
import pandas as pd
import importlib.util

sys.path.insert(0, '.')

# Load modules by file
spec_prep = importlib.util.spec_from_file_location("preprocessing", "01_data_preprocessing.py")
preprocessing = importlib.util.module_from_spec(spec_prep)
spec_prep.loader.exec_module(preprocessing)

spec_eng = importlib.util.spec_from_file_location("engineering", "02_feature_engineering.py")
engineering = importlib.util.module_from_spec(spec_eng)
spec_eng.loader.exec_module(engineering)

try:
    print('Loading and preprocessing data...')
    preprocessor = preprocessing.DataPreprocessor('data')
    raw_data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()
    print(f'Raw data shape: {raw_data.shape}')
    print()

    print('Engineering features with temporal validation...')
    engineer = engineering.FeatureEngineer(raw_data)
    processed = engineer.get_processed_data()
    print(f'Processed data shape: {processed.shape}')
    print()

    print('Feature columns created:')
    new_features = [col for col in processed.columns if col not in raw_data.columns]
    print(f'Total new features: {len(new_features)}')
    for feat in sorted(new_features):
        print(f'  - {feat}')
    print()

    print('Validation status:', 'PASSED' if not engineer.temporal_validation_errors else 'FAILED')
    if engineer.temporal_validation_errors:
        print('Errors:', engineer.temporal_validation_errors)
        
except Exception as e:
    import traceback
    print(f'ERROR: {e}')
    traceback.print_exc()
