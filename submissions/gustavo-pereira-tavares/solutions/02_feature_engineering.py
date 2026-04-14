import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeatureEngineer:
    """Create features for churn prediction model."""
    
    def __init__(self, data):
        self.data = data.copy()
        self.processed_data = None
        
    def engineer_adoption_features(self):
        """Create features related to feature adoption."""
        logger.info("Engineering adoption features...")
        
        # Feature adoption rate
        self.data['adoption_rate'] = self.data['unique_features_used'] / 40  # Assuming 40 total features
        self.data['adoption_rate'] = self.data['adoption_rate'].clip(0, 1)
        
        # Feature usage intensity
        self.data['usage_intensity'] = np.log1p(self.data['total_usage_count'] / (self.data['usage_days'] + 1))
        
        # Days to first feature use
        self.data['days_to_first_use'] = (
            (self.data['first_usage_date'] - self.data['start_date']).dt.days
        ).fillna(999)
        self.data['days_to_first_use'] = self.data['days_to_first_use'].clip(0, 365)
        
        # Feature usage recency (days since last use)
        reference_date = pd.to_datetime('2024-10-31')  # Latest date in data
        self.data['days_since_last_use'] = (
            (reference_date - self.data['last_usage_date']).dt.days
        ).fillna(999)
        
        # Beta feature adoption
        self.data['uses_beta_features'] = (self.data['beta_features_used'] > 0).astype(int)
        
        return self
    
    def engineer_support_features(self):
        """Create features related to support quality."""
        logger.info("Engineering support features...")
        
        # Support engagement
        self.data['support_engagement_level'] = np.log1p(self.data['support_ticket_count'])
        
        # Support quality score (combination of resolution time and satisfaction)
        self.data['support_quality_score'] = (
            (1 - np.tanh(self.data['avg_resolution_time'] / 100)) * 
            (self.data['avg_satisfaction_score'] / 5)
        ).fillna(0.5)
        
        # First response time efficiency
        self.data['first_response_efficiency'] = 1 - np.tanh(self.data['avg_first_response_time'] / 100)
        self.data['first_response_efficiency'] = self.data['first_response_efficiency'].fillna(0.5)
        
        # Escalation rate
        self.data['escalation_rate'] = self.data['escalation_count'] / (self.data['support_ticket_count'] + 1)
        
        # Has unresolved issues
        self.data['has_urgent_tickets'] = (self.data['urgent_ticket_count'] > 0).astype(int)
        
        # Support dissatisfaction flag
        self.data['low_satisfaction'] = (self.data['avg_satisfaction_score'] < 3.0).astype(int)
        self.data['low_satisfaction'] = self.data['low_satisfaction'].fillna(0)
        
        return self
    
    def engineer_financial_features(self):
        """Create features related to financial metrics."""
        logger.info("Engineering financial features...")
        
        # Account tenure (days since signup to reference date)
        reference_date = pd.to_datetime('2024-10-31')
        self.data['days_since_signup'] = (reference_date - self.data['signup_date']).dt.days
        
        # Subscription tenure
        self.data['subscription_tenure_days'] = (reference_date - self.data['start_date']).dt.days
        
        # MRR as log for normalized scale
        self.data['log_mrr'] = np.log1p(self.data['mrr_amount'])
        
        # Trial conversion flag (if is_trial is true but churn_flag is false = converted)
        self.data['trial_converted'] = ((self.data['is_trial'] == True) & (self.data['churn_flag'] == False)).astype(int)
        
        # Upgrade/downgrade patterns
        self.data['has_upgrade'] = self.data['upgrade_flag'].astype(int)
        self.data['has_downgrade'] = self.data['downgrade_flag'].astype(int)
        self.data['upgrade_downgrade_pattern'] = self.data['has_upgrade'] - self.data['has_downgrade']
        
        # Plan tier (ordinal encoding)
        plan_tier_map = {'Basic': 1, 'Pro': 2, 'Enterprise': 3}
        self.data['plan_tier_encoded'] = self.data['plan_tier'].map(plan_tier_map).fillna(1)
        
        # Account size (seats)
        self.data['log_seats'] = np.log1p(self.data['seats'])
        
        return self
    
    def engineer_temporal_features(self):
        """Create temporal features."""
        logger.info("Engineering temporal features...")
        
        # Days since last activity (combined from usage and support)
        self.data['days_since_activity'] = (
            self.data[['days_since_last_use', 'support_ticket_count']].apply(
                lambda row: row['days_since_last_use'] if row['support_ticket_count'] == 0 
                else min(row['days_since_last_use'], 365),
                axis=1
            )
        )
        
        # Activity momentum (recent vs older usage)
        reference_date = pd.to_datetime('2024-10-31')
        self.data['recent_activity_days'] = (
            (reference_date - self.data['last_usage_date']).dt.days <= 30
        ).astype(int)
        
        # Signup recency (new accounts vs mature)
        self.data['is_new_account'] = (self.data['days_since_signup'] < 90).astype(int)
        self.data['is_mature_account'] = (self.data['days_since_signup'] >= 365).astype(int)
        
        return self
    
    def engineer_industry_features(self):
        """Create industry and country features."""
        logger.info("Engineering industry features...")
        
        # Industry risk categories
        high_churn_industries = ['FinTech', 'EdTech']
        self.data['high_risk_industry'] = self.data['industry'].isin(high_churn_industries).astype(int)
        
        # One-hot encode industry
        industry_dummies = pd.get_dummies(self.data['industry'], prefix='industry')
        self.data = pd.concat([self.data, industry_dummies], axis=1)
        
        # Country (group low-frequency countries)
        country_counts = self.data['country'].value_counts()
        common_countries = country_counts[country_counts > 5].index
        self.data['country_grouped'] = self.data['country'].apply(
            lambda x: x if x in common_countries else 'Other'
        )
        country_dummies = pd.get_dummies(self.data['country_grouped'], prefix='country')
        self.data = pd.concat([self.data, country_dummies], axis=1)
        
        return self
    
    def engineer_churn_related_features(self):
        """Create features from churn patterns."""
        logger.info("Engineering churn-related features...")
        
        # Churn reason code encoding
        reason_dummies = pd.get_dummies(self.data['reason_code'], prefix='reason')
        self.data = pd.concat([self.data, reason_dummies], axis=1)
        
        # Preceding events
        self.data['had_upgrade_before_churn'] = self.data['preceding_upgrade_flag'].astype(int)
        self.data['had_downgrade_before_churn'] = self.data['preceding_downgrade_flag'].astype(int)
        
        # Refund amount
        self.data['has_refund'] = (self.data['refund_amount_usd'] > 0).astype(int)
        self.data['log_refund'] = np.log1p(self.data['refund_amount_usd'])
        
        return self
    
    def create_composite_risk_factors(self):
        """Create composite risk indicators."""
        logger.info("Creating composite risk factors...")
        
        # Adoption Risk
        self.data['adoption_risk'] = (
            (self.data['unique_features_used'] < 3).astype(int) * 40 +
            (self.data['days_to_first_use'] > 30).astype(int) * 15
        )
        
        # Support Risk
        self.data['support_risk'] = (
            (self.data['avg_resolution_time'] > 96).astype(int) * 35 +
            (self.data['avg_satisfaction_score'] < 3.0).astype(int) * 20 +
            (self.data['escalation_rate'] > 0.2).astype(int) * 15
        )
        
        # Financial Risk
        self.data['financial_risk'] = (
            (self.data['has_downgrade']).astype(int) * 25 +
            (self.data['is_trial'] & (self.data['support_ticket_count'] < 5)).astype(int) * 20
        )
        
        # Engagement Risk
        self.data['engagement_risk'] = (
            (self.data['days_since_last_use'] > 60).astype(int) * 30 +
            (self.data['usage_days'] < 10).astype(int) * 25
        )
        
        # Combined Risk Score (basis for risk tiers)
        self.data['base_risk_score'] = (
            self.data['adoption_risk'] + 
            self.data['support_risk'] + 
            self.data['financial_risk'] + 
            self.data['engagement_risk'] +
            (self.data['high_risk_industry'] * 15)
        ).clip(0, 100)
        
        return self
    
    def get_processed_data(self):
        """Get final processed data with all features."""
        if self.processed_data is None:
            (self.engineer_adoption_features()
             .engineer_support_features()
             .engineer_financial_features()
             .engineer_temporal_features()
             .engineer_industry_features()
             .engineer_churn_related_features()
             .create_composite_risk_factors())
            self.processed_data = self.data
        return self.processed_data
    
    def save_features(self, output_path='outputs/features_engineered.csv'):
        """Save engineered features."""
        import os
        os.makedirs('outputs', exist_ok=True)
        self.get_processed_data().to_csv(output_path, index=False)
        logger.info(f"Engineered features saved to {output_path}")
        return self


if __name__ == '__main__':
    import importlib.util
    spec = importlib.util.spec_from_file_location("preprocessing", "01_data_preprocessing.py")
    preprocessing = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preprocessing)
    DataPreprocessor = preprocessing.DataPreprocessor
    
    preprocessor = DataPreprocessor()
    raw_data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()
    
    engineer = FeatureEngineer(raw_data)
    processed_data = engineer.get_processed_data()
    engineer.save_features()
    
    print(f"\nEngineered features shape: {processed_data.shape}")
    print(f"New features count: {len([col for col in processed_data.columns if col not in raw_data.columns])}")
    print(f"Key features:\n{processed_data[['adoption_rate', 'support_quality_score', 'base_risk_score']].describe()}")
