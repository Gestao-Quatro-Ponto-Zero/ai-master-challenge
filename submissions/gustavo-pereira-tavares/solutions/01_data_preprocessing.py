import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataPreprocessor:
    """Load, merge, and preprocess all churn analysis datasets."""
    
    def __init__(self, data_path='.'):
        self.data_path = data_path
        self.accounts = None
        self.subscriptions = None
        self.churn_events = None
        self.feature_usage = None
        self.support_tickets = None
        self.merged_data = None
        
    def load_raw_data(self):
        """Load all CSV files."""
        logger.info("Loading raw datasets...")
        
        self.accounts = pd.read_csv(f'{self.data_path}/ravenstack_accounts.csv')
        self.subscriptions = pd.read_csv(f'{self.data_path}/ravenstack_subscriptions.csv')
        self.churn_events = pd.read_csv(f'{self.data_path}/ravenstack_churn_events.csv')
        self.feature_usage = pd.read_csv(f'{self.data_path}/ravenstack_feature_usage.csv')
        self.support_tickets = pd.read_csv(f'{self.data_path}/ravenstack_support_tickets.csv')
        
        logger.info(f"Accounts: {self.accounts.shape}")
        logger.info(f"Subscriptions: {self.subscriptions.shape}")
        logger.info(f"Churn Events: {self.churn_events.shape}")
        logger.info(f"Feature Usage: {self.feature_usage.shape}")
        logger.info(f"Support Tickets: {self.support_tickets.shape}")
        
        return self
    
    def merge_datasets(self):
        """Merge all datasets on account_id and subscription_id."""
        logger.info("Merging datasets...")
        
        # Convert date columns to datetime
        self.accounts['signup_date'] = pd.to_datetime(self.accounts['signup_date'])
        self.subscriptions['start_date'] = pd.to_datetime(self.subscriptions['start_date'])
        self.subscriptions['end_date'] = pd.to_datetime(self.subscriptions['end_date'])
        self.churn_events['churn_date'] = pd.to_datetime(self.churn_events['churn_date'])
        self.feature_usage['usage_date'] = pd.to_datetime(self.feature_usage['usage_date'])
        self.support_tickets['submitted_at'] = pd.to_datetime(self.support_tickets['submitted_at'])
        self.support_tickets['closed_at'] = pd.to_datetime(self.support_tickets['closed_at'])
        
        # Merge subscriptions with accounts
        merged = self.subscriptions.merge(
            self.accounts[['account_id', 'account_name', 'industry', 'country', 'referral_source', 'seats', 'signup_date', 'churn_flag']],
            on='account_id',
            how='left'
        )
        
        # Merge with churn events
        merged = merged.merge(
            self.churn_events[['account_id', 'churn_date', 'reason_code', 'refund_amount_usd', 
                               'preceding_upgrade_flag', 'preceding_downgrade_flag', 'feedback_text']],
            on='account_id',
            how='left'
        )
        
        # Aggregate support tickets by account_id
        support_agg = self.support_tickets.groupby('account_id').agg({
            'ticket_id': 'count',
            'resolution_time_hours': 'mean',
            'first_response_time_minutes': 'mean',
            'satisfaction_score': 'mean',
            'escalation_flag': 'sum',
            'priority': lambda x: (x == 'urgent').sum()
        }).reset_index()
        support_agg.columns = ['account_id', 'support_ticket_count', 'avg_resolution_time', 
                               'avg_first_response_time', 'avg_satisfaction_score', 'escalation_count', 'urgent_ticket_count']
        
        merged = merged.merge(support_agg, on='account_id', how='left')
        
        # Merge feature usage aggregated by subscription_id
        feature_agg = self.feature_usage.groupby('subscription_id').agg({
            'feature_name': 'nunique',
            'usage_count': ['sum', 'mean'],
            'usage_duration_secs': ['sum', 'mean'],
            'error_count': 'sum',
            'is_beta_feature': 'sum',
            'usage_date': ['min', 'max', 'count']
        }).reset_index()
        feature_agg.columns = ['subscription_id', 'unique_features_used', 'total_usage_count', 'avg_usage_count',
                               'total_usage_duration', 'avg_usage_duration', 'total_errors', 'beta_features_used',
                               'first_usage_date', 'last_usage_date', 'usage_days']
        
        merged = merged.merge(feature_agg, on='subscription_id', how='left')
        
        self.merged_data = merged
        logger.info(f"Merged dataset shape: {self.merged_data.shape}")
        
        return self
    
    def handle_missing_values(self):
        """Handle missing values appropriately."""
        logger.info("Handling missing values...")
        
        # Consolidate churn_flag columns (prefer churn_flag_y from churn_events, then x from accounts)
        if 'churn_flag_x' in self.merged_data.columns and 'churn_flag_y' in self.merged_data.columns:
            self.merged_data['churn_flag'] = self.merged_data['churn_flag_y'].fillna(self.merged_data['churn_flag_x'])
            self.merged_data = self.merged_data.drop(['churn_flag_x', 'churn_flag_y'], axis=1)
        elif 'churn_flag_x' in self.merged_data.columns:
            self.merged_data = self.merged_data.rename(columns={'churn_flag_x': 'churn_flag'})
        elif 'churn_flag_y' in self.merged_data.columns:
            self.merged_data = self.merged_data.rename(columns={'churn_flag_y': 'churn_flag'})
        
        # Consolidate seats columns
        if 'seats_x' in self.merged_data.columns and 'seats_y' in self.merged_data.columns:
            self.merged_data['seats'] = self.merged_data['seats_x'].fillna(self.merged_data['seats_y'])
            self.merged_data = self.merged_data.drop(['seats_x', 'seats_y'], axis=1)
        elif 'seats_x' in self.merged_data.columns:
            self.merged_data = self.merged_data.rename(columns={'seats_x': 'seats'})
        elif 'seats_y' in self.merged_data.columns:
            self.merged_data = self.merged_data.rename(columns={'seats_y': 'seats'})
        
        # Fill support metrics with 0 for accounts with no tickets
        support_cols = ['support_ticket_count', 'avg_resolution_time', 'avg_first_response_time',
                       'avg_satisfaction_score', 'escalation_count', 'urgent_ticket_count']
        for col in support_cols:
            self.merged_data[col] = self.merged_data[col].fillna(0)
        
        # Fill feature metrics with 0 for subscriptions with no usage
        feature_cols = ['unique_features_used', 'total_usage_count', 'avg_usage_count',
                       'total_usage_duration', 'avg_usage_duration', 'total_errors', 'beta_features_used', 'usage_days']
        for col in feature_cols:
            self.merged_data[col] = self.merged_data[col].fillna(0)
        
        # Fill churn-related columns
        self.merged_data['reason_code'] = self.merged_data['reason_code'].fillna('unknown')
        self.merged_data['feedback_text'] = self.merged_data['feedback_text'].fillna('')
        self.merged_data['refund_amount_usd'] = self.merged_data['refund_amount_usd'].fillna(0)
        self.merged_data['preceding_upgrade_flag'] = self.merged_data['preceding_upgrade_flag'].fillna(False)
        self.merged_data['preceding_downgrade_flag'] = self.merged_data['preceding_downgrade_flag'].fillna(False)
        self.merged_data['churn_date'] = self.merged_data['churn_date'].fillna(pd.NaT)
        
        logger.info(f"Missing values after handling:\n{self.merged_data.isnull().sum().sum()} total nulls")
        
        return self
    
    def get_merged_data(self):
        """Return the merged and cleaned dataset."""
        if self.merged_data is None:
            self.load_raw_data().merge_datasets().handle_missing_values()
        return self.merged_data
    
    def save_preprocessed_data(self, output_path='outputs/preprocessed_data.csv'):
        """Save preprocessed data."""
        import os
        os.makedirs('outputs', exist_ok=True)
        self.merged_data.to_csv(output_path, index=False)
        logger.info(f"Preprocessed data saved to {output_path}")
        return self


if __name__ == '__main__':
    preprocessor = DataPreprocessor()
    data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()
    preprocessor.save_preprocessed_data()
    print(f"\nFinal dataset shape: {data.shape}")
    print(f"Columns: {list(data.columns)}")
    print(f"\nFirst few rows:")
    print(data.head(2))
