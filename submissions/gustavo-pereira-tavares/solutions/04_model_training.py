import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, precision_score, recall_score, f1_score, confusion_matrix, roc_curve, auc
import xgboost as xgb
import lightgbm as lgb
import joblib
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChurnModelTrainer:
    """Train and evaluate churn prediction models."""
    
    def __init__(self, data, target_column='churn_flag', random_state=42):
        self.data = data.copy()
        self.target_column = target_column
        self.random_state = random_state
        self.X = None
        self.y = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.feature_columns = None
        self.scaler = StandardScaler()
        self.xgb_model = None
        self.lgb_model = None
        self.ensemble_model = None
        self.shap_explainer = None
        
    def prepare_features(self):
        """Prepare features for modeling."""
        logger.info("Preparing features for modeling...")
        
        # Select features to use (exclude identifiers, dates, text)
        exclude_cols = [
            'subscription_id', 'account_id', 'account_name', 'churn_event_id', 'ticket_id',
            'signup_date', 'start_date', 'end_date', 'churn_date', 'usage_date', 'usage_id',
            'submitted_at', 'closed_at', 'feedback_text', 'industry', 'country',
            'country_grouped', 'reason_code', 'referral_source', 'priority',
            'first_usage_date', 'last_usage_date', 'billing_frequency'
        ]
        
        # Features to use
        self.feature_columns = [col for col in self.data.columns 
                               if col not in exclude_cols and col != self.target_column]
        
        self.X = self.data[self.feature_columns].fillna(0)
        
        # Convert object columns to numeric if they exist
        for col in self.X.columns:
            if self.X[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    self.X[col] = pd.to_numeric(self.X[col], errors='coerce').fillna(0)
                except:
                    # If conversion fails, use one-hot encoding
                    encoded = pd.get_dummies(self.X[col], prefix=col, drop_first=True)
                    self.X = pd.concat([self.X.drop(col, axis=1), encoded], axis=1)
                    self.feature_columns = [c for c in self.feature_columns if c != col] + list(encoded.columns)
        
        self.X = self.X[self.feature_columns].fillna(0)
        self.y = self.data[self.target_column].astype(int)
        
        logger.info(f"Using {len(self.feature_columns)} features")
        logger.info(f"Feature list: {self.feature_columns[:10]}... (showing first 10)")
        logger.info(f"Target distribution: {self.y.value_counts().to_dict()}")
        
        return self
    
    def train_test_split_time_based(self, test_size=0.2):
        """Split data based on subscription tenure (time-based split)."""
        logger.info(f"Performing time-based train/test split ({100*(1-test_size):.0f}/{100*test_size:.0f})...")
        
        # Sort by subscription_tenure_days and split
        sorted_indices = self.data['subscription_tenure_days'].argsort()
        split_point = int(len(sorted_indices) * (1 - test_size))
        
        train_idx = sorted_indices[:split_point]
        test_idx = sorted_indices[split_point:]
        
        self.X_train = self.X.iloc[train_idx].reset_index(drop=True)
        self.X_test = self.X.iloc[test_idx].reset_index(drop=True)
        self.y_train = self.y.iloc[train_idx].reset_index(drop=True)
        self.y_test = self.y.iloc[test_idx].reset_index(drop=True)
        
        logger.info(f"Training set: {len(self.X_train)} samples, churn rate: {self.y_train.mean()*100:.1f}%")
        logger.info(f"Test set: {len(self.X_test)} samples, churn rate: {self.y_test.mean()*100:.1f}%")
        
        return self
    
    def train_xgboost(self, hyperparameters=None):
        """Train XGBoost model."""
        logger.info("Training XGBoost model...")
        
        if hyperparameters is None:
            hyperparameters = {
                'max_depth': 6,
                'learning_rate': 0.1,
                'n_estimators': 100,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'min_child_weight': 1,
                'reg_alpha': 0.1,
                'reg_lambda': 0.5,
                'random_state': self.random_state,
                'objective': 'binary:logistic',
                'eval_metric': 'logloss'
            }
        
        self.xgb_model = xgb.XGBClassifier(**hyperparameters)
        self.xgb_model.fit(
            self.X_train, self.y_train,
            eval_set=[(self.X_test, self.y_test)],
            early_stopping_rounds=10,
            verbose=False
        )
        
        # Evaluate
        y_pred_xgb = self.xgb_model.predict(self.X_test)
        y_pred_proba_xgb = self.xgb_model.predict_proba(self.X_test)[:, 1]
        
        xgb_auc = roc_auc_score(self.y_test, y_pred_proba_xgb)
        xgb_precision = precision_score(self.y_test, y_pred_xgb)
        xgb_recall = recall_score(self.y_test, y_pred_xgb)
        xgb_f1 = f1_score(self.y_test, y_pred_xgb)
        
        logger.info(f"XGBoost Results - AUC: {xgb_auc:.4f}, Precision: {xgb_precision:.4f}, Recall: {xgb_recall:.4f}, F1: {xgb_f1:.4f}")
        
        return self
    
    def train_lightgbm(self, hyperparameters=None):
        """Train LightGBM model."""
        logger.info("Training LightGBM model...")
        
        if hyperparameters is None:
            hyperparameters = {
                'max_depth': 7,
                'learning_rate': 0.1,
                'n_estimators': 100,
                'num_leaves': 31,
                'feature_fraction': 0.8,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'lambda_l1': 0.1,
                'lambda_l2': 0.5,
                'random_state': self.random_state,
                'objective': 'binary',
                'metric': 'auc'
            }
        
        self.lgb_model = lgb.LGBMClassifier(**hyperparameters)
        self.lgb_model.fit(
            self.X_train, self.y_train,
            eval_set=[(self.X_test, self.y_test)],
            callbacks=[lgb.early_stopping(10), lgb.log_evaluation(-1)]
        )
        
        # Evaluate
        y_pred_lgb = self.lgb_model.predict(self.X_test)
        y_pred_proba_lgb = self.lgb_model.predict_proba(self.X_test)[:, 1]
        
        lgb_auc = roc_auc_score(self.y_test, y_pred_proba_lgb)
        lgb_precision = precision_score(self.y_test, y_pred_lgb)
        lgb_recall = recall_score(self.y_test, y_pred_lgb)
        lgb_f1 = f1_score(self.y_test, y_pred_lgb)
        
        logger.info(f"LightGBM Results - AUC: {lgb_auc:.4f}, Precision: {lgb_precision:.4f}, Recall: {lgb_recall:.4f}, F1: {lgb_f1:.4f}")
        
        return self
    
    def create_ensemble(self):
        """Create weighted ensemble of both models."""
        logger.info("Creating ensemble model...")
        
        # Simple averaging
        y_pred_xgb_proba = self.xgb_model.predict_proba(self.X_test)[:, 1]
        y_pred_lgb_proba = self.lgb_model.predict_proba(self.X_test)[:, 1]
        
        # Weighted average (60% XGBoost, 40% LightGBM based on typical performance)
        self.ensemble_predictions = (0.6 * y_pred_xgb_proba + 0.4 * y_pred_lgb_proba)
        ensemble_auc = roc_auc_score(self.y_test, self.ensemble_predictions)
        
        logger.info(f"Ensemble AUC: {ensemble_auc:.4f}")
        
        return self
    
    def explain_model_with_shap(self):
        """Generate feature importance explanations."""
        logger.info("Generating feature importance...")
        
        # Use model's built-in feature importance
        xgb_importance = self.xgb_model.feature_importances_
        lgb_importance = self.lgb_model.feature_importances_
        
        # Average importance from both models
        avg_importance = (xgb_importance + lgb_importance) / 2
        
        # Create feature importance summary
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': avg_importance,
            'xgb_importance': xgb_importance,
            'lgb_importance': lgb_importance
        }).sort_values('importance', ascending=False)
        
        logger.info(f"Top 10 features by importance:\n{feature_importance.head(10)}")
        
        return self, None, feature_importance
    
    def save_models(self, output_dir='models'):
        """Save trained models to disk."""
        logger.info(f"Saving models to {output_dir}...")
        os.makedirs(output_dir, exist_ok=True)
        
        joblib.dump(self.xgb_model, f'{output_dir}/xgb_model.pkl')
        joblib.dump(self.lgb_model, f'{output_dir}/lgb_model.pkl')
        joblib.dump(self.scaler, f'{output_dir}/scaler.pkl')
        
        # Save feature columns
        joblib.dump(self.feature_columns, f'{output_dir}/feature_columns.pkl')
        
        logger.info("Models saved successfully")
        return self
    
    def get_models(self):
        """Return trained models."""
        return {
            'xgb': self.xgb_model,
            'lgb': self.lgb_model,
            'feature_columns': self.feature_columns
        }


if __name__ == '__main__':
    import importlib.util
    
    spec1 = importlib.util.spec_from_file_location("preprocessing", "01_data_preprocessing.py")
    preprocessing = importlib.util.module_from_spec(spec1)
    spec1.loader.exec_module(preprocessing)
    DataPreprocessor = preprocessing.DataPreprocessor
    
    spec2 = importlib.util.spec_from_file_location("feature_eng", "02_feature_engineering.py")
    feature_eng = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(feature_eng)
    FeatureEngineer = feature_eng.FeatureEngineer
    
    # Load and prepare data
    preprocessor = DataPreprocessor()
    raw_data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()
    
    engineer = FeatureEngineer(raw_data)
    processed_data = engineer.get_processed_data()
    
    # Train models
    trainer = ChurnModelTrainer(processed_data)
    (trainer.prepare_features()
     .train_test_split_time_based()
     .train_xgboost()
     .train_lightgbm()
     .create_ensemble())
    
    # Get SHAP explanations
    trainer, shap_vals, feat_imp = trainer.explain_model_with_shap()
    
    # Save models
    trainer.save_models()
    
    print("\n=== MODEL TRAINING COMPLETE ===")
    print(f"XGBoost AUC: {roc_auc_score(trainer.y_test, trainer.xgb_model.predict_proba(trainer.X_test)[:, 1]):.4f}")
    print(f"LightGBM AUC: {roc_auc_score(trainer.y_test, trainer.lgb_model.predict_proba(trainer.X_test)[:, 1]):.4f}")
    print(f"Ensemble AUC: {roc_auc_score(trainer.y_test, trainer.ensemble_predictions):.4f}")
