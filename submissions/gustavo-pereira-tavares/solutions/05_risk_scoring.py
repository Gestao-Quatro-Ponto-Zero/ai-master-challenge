import pandas as pd
import numpy as np
import joblib
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskScoringEngine:
    """Generate risk scores and register for all accounts."""
    
    def __init__(self, data, models=None, model_dir='models'):
        self.data = data.copy()
        self.models = models
        self.model_dir = model_dir
        self.risk_register = None
        self.feature_columns = None
        
        if models is None:
            self.load_models()
    
    def load_models(self):
        """Load pre-trained models."""
        logger.info(f"Loading models from {self.model_dir}...")
        
        try:
            self.models = {
                'xgb': joblib.load(f'{self.model_dir}/xgb_model.pkl'),
                'lgb': joblib.load(f'{self.model_dir}/lgb_model.pkl'),
            }
            self.feature_columns = joblib.load(f'{self.model_dir}/feature_columns.pkl')
        except FileNotFoundError as e:
            logger.warning(f"Models not found: {e}. Will train new models.")
    
    def assign_risk_tiers(self, churn_probabilities):
        """Assign risk tiers based on churn probability."""
        tiers = []
        for prob in churn_probabilities:
            if prob >= 0.7:
                tiers.append('Critical')
            elif prob >= 0.5:
                tiers.append('High')
            elif prob >= 0.3:
                tiers.append('Medium')
            else:
                tiers.append('Low')
        return tiers
    
    def calculate_composite_risk_score(self, row):
        """Calculate comprehensive risk score using multiple factors."""
        score = 0
        drivers = {}
        
        # Adoption gap (40 points)
        if row['unique_features_used'] < 3:
            adoption_score = 40
            drivers['Low Feature Adoption'] = 40
        else:
            adoption_score = max(0, 40 - (row['unique_features_used'] * 5))
            if adoption_score > 0:
                drivers['Low Feature Adoption'] = adoption_score
        score += adoption_score
        
        # Support quality (35 points)
        support_score = 0
        if row['avg_resolution_time'] > 96:
            support_score += 20
            drivers['Slow Support Resolution'] = 20
        if row['avg_satisfaction_score'] < 3.0 and row['avg_satisfaction_score'] > 0:
            support_score += 15
            drivers['Low Support Satisfaction'] = 15
        score += support_score
        
        # Financial changes (30 points)
        financial_score = 0
        if row['has_downgrade'] > 0:
            financial_score += 25
            drivers['Recent Plan Downgrade'] = 25
        if row['is_trial'] and row['support_ticket_count'] < 5:
            financial_score += 20
            drivers['Trial with Low Engagement'] = 20
        score += financial_score
        
        # Industry risk (15 points)
        if row['high_risk_industry'] > 0:
            score += 15
            drivers['High-Risk Industry'] = 15
        
        # Engagement and recency (20 points)
        if row['days_since_last_use'] > 60:
            score += 20
            drivers['Low Recent Activity'] = 20
        
        return min(score, 100), drivers
    
    def predict_churn_probability(self):
        """Predict churn probability using ensemble models."""
        logger.info("Predicting churn probabilities...")
        
        if self.models is None or 'xgb' not in self.models:
            logger.warning("Models not loaded. Using rule-based risk scoring.")
            return self.data['base_risk_score'] / 100
        
        # Prepare features
        X = self.data[self.feature_columns].fillna(0).copy()
        
        # Convert object columns to numeric
        for col in X.columns:
            if X[col].dtype == 'object':
                try:
                    X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
                except:
                    # Use label encoding for categorical
                    from sklearn.preprocessing import LabelEncoder
                    le = LabelEncoder()
                    X[col] = le.fit_transform(X[col].astype(str))
        
        # Get predictions from both models
        xgb_proba = self.models['xgb'].predict_proba(X)[:, 1]
        lgb_proba = self.models['lgb'].predict_proba(X)[:, 1]
        
        # Ensemble prediction (weighted average)
        ensemble_proba = 0.6 * xgb_proba + 0.4 * lgb_proba
        
        logger.info(f"Average predicted churn probability: {ensemble_proba.mean():.4f}")
        
        return ensemble_proba
    
    def generate_risk_register(self):
        """Generate complete risk register with account-level insights."""
        logger.info("Generating risk register...")
        
        risk_register = pd.DataFrame({
            'account_id': self.data['account_id'],
            'account_name': self.data['account_name'],
            'industry': self.data['industry'],
            'country': self.data['country'],
            'plan_tier': self.data['plan_tier'],
            'mrr_amount': self.data['mrr_amount'],
            'arr_amount': self.data['mrr_amount'] * 12,
            'seats': self.data['seats'],
            'days_since_signup': self.data['days_since_signup'],
            'is_trial': self.data['is_trial'],
        })
        
        # Add churn probability
        risk_register['churn_probability'] = self.predict_churn_probability()
        
        # Add risk tier
        risk_register['risk_tier'] = self.assign_risk_tiers(risk_register['churn_probability'])
        
        # Add composite risk score and primary driver
        risk_scores = []
        primary_drivers = []
        for _, row in self.data.iterrows():
            score, drivers = self.calculate_composite_risk_score(row)
            risk_scores.append(score)
            primary_driver = max(drivers.items(), key=lambda x: x[1])[0] if drivers else 'N/A'
            primary_drivers.append(primary_driver)
        
        risk_register['risk_score'] = risk_scores
        risk_register['primary_risk_driver'] = primary_drivers
        
        # Add engagement metrics
        risk_register['feature_adoption_rate'] = (self.data['unique_features_used'] / 40 * 100).clip(0, 100)
        risk_register['support_quality_score'] = self.data['support_quality_score'] * 100
        risk_register['avg_resolution_time_hours'] = self.data['avg_resolution_time']
        risk_register['avg_satisfaction_score'] = self.data['avg_satisfaction_score']
        
        # Calculate confidence in prediction
        risk_register['prediction_confidence'] = np.where(
            (risk_register['churn_probability'] > 0.3) & (risk_register['churn_probability'] < 0.7),
            1 - (abs(risk_register['churn_probability'] - 0.5) / 0.2).clip(0, 1),
            0.9
        ) * 100
        
        # Add recommended actions
        recommended_actions = []
        for _, row in risk_register.iterrows():
            actions = []
            if row['churn_probability'] > 0.7:
                actions.append('🔴 IMEDIATO: Contato + Chamada do Gerente de Sucesso')
                actions.append('🔴 Oferecer desconto de retenção/upgrade')
            elif row['churn_probability'] > 0.5:
                actions.append('🟠 ALTO: Agendar workshop de adoção de recursos')
                actions.append('🟠 Melhorar conformidade de SLA de suporte')
            elif row['churn_probability'] > 0.3:
                actions.append('🟡 MÉDIO: Educação proativa de recursos')
            
            if row['feature_adoption_rate'] < 30:
                actions.append('→ Aumentar onboarding de recursos')
            if row['avg_satisfaction_score'] < 3.0 and row['avg_satisfaction_score'] > 0:
                actions.append('→ Escalar problema de qualidade de suporte')
            
            recommended_actions.append(' | '.join(actions) if actions else 'Monitorar')
        
        risk_register['recommended_action'] = recommended_actions
        
        # Sort by risk
        self.risk_register = risk_register.sort_values('risk_score', ascending=False)
        
        logger.info(f"Risk register generated. Shape: {self.risk_register.shape}")
        logger.info(f"Risk distribution:\n{self.risk_register['risk_tier'].value_counts()}")
        
        return self
    
    def get_risk_summary_stats(self):
        """Get summary statistics for dashboard."""
        if self.risk_register is None:
            self.generate_risk_register()
        
        stats = {
            'total_accounts': len(self.risk_register),
            'critical_risk_count': len(self.risk_register[self.risk_register['risk_tier'] == 'Critical']),
            'high_risk_count': len(self.risk_register[self.risk_register['risk_tier'] == 'High']),
            'medium_risk_count': len(self.risk_register[self.risk_register['risk_tier'] == 'Medium']),
            'low_risk_count': len(self.risk_register[self.risk_register['risk_tier'] == 'Low']),
            'avg_churn_probability': self.risk_register['churn_probability'].mean(),
            'revenue_at_critical_risk': self.risk_register[
                self.risk_register['risk_tier'] == 'Critical'
            ]['arr_amount'].sum(),
            'revenue_at_high_risk': self.risk_register[
                self.risk_register['risk_tier'] == 'High'
            ]['arr_amount'].sum(),
        }
        
        return stats
    
    def save_risk_register(self, output_path='outputs/risk_register.csv'):
        """Save risk register to CSV."""
        import os
        os.makedirs('outputs', exist_ok=True)
        
        if self.risk_register is None:
            self.generate_risk_register()
        
        self.risk_register.to_csv(output_path, index=False)
        logger.info(f"Risk register saved to {output_path}")
        
        return self
    
    def get_critical_action_list(self):
        """Get top accounts requiring immediate action."""
        if self.risk_register is None:
            self.generate_risk_register()
        
        critical = self.risk_register[self.risk_register['risk_tier'].isin(['Critical', 'High'])].head(50)
        return critical[['account_id', 'account_name', 'industry', 'mrr_amount', 'risk_score', 
                        'risk_tier', 'primary_risk_driver', 'recommended_action']]


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
    
    # Generate risk scores
    risk_engine = RiskScoringEngine(processed_data)
    risk_engine.generate_risk_register().save_risk_register()
    
    # Print summary
    stats = risk_engine.get_risk_summary_stats()
    print("\n=== RISK SCORING SUMMARY ===")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n=== TOP 10 CRITICAL ACCOUNTS ===")
    print(risk_engine.get_critical_action_list().head(10).to_string())
