import pandas as pd
import numpy as np
from scipy.stats import chi2_contingency, pearsonr
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RootCauseAnalysis:
    """Analyze root causes of churn using cross-dataset analysis."""
    
    def __init__(self, merged_data):
        self.data = merged_data
        self.results = {}
        
    def analyze_feature_adoption_gap(self):
        """Analyze gap in feature adoption between churned and retained."""
        logger.info("Analyzing feature adoption gaps...")
        
        churned = self.data[self.data['churn_flag'] == True]
        retained = self.data[self.data['churn_flag'] == False]
        
        adoption_gap = {
            'churned_avg_features': churned['unique_features_used'].mean(),
            'retained_avg_features': retained['unique_features_used'].mean(),
            'gap_percentage': ((retained['unique_features_used'].mean() - churned['unique_features_used'].mean()) / 
                               (retained['unique_features_used'].mean() + 1) * 100),
            'churned_avg_usage_count': churned['total_usage_count'].mean(),
            'retained_avg_usage_count': retained['total_usage_count'].mean(),
        }
        
        # Low adoption rate in churned
        low_adoption_churned = (churned['unique_features_used'] < 3).sum() / len(churned) * 100
        adoption_gap['low_adoption_rate_churned'] = low_adoption_churned
        
        self.results['feature_adoption'] = adoption_gap
        logger.info(f"Feature adoption gap: {adoption_gap}")
        
        return self
    
    def analyze_support_quality(self):
        """Analyze support quality metrics correlation with churn."""
        logger.info("Analyzing support quality metrics...")
        
        churned = self.data[self.data['churn_flag'] == True]
        retained = self.data[self.data['churn_flag'] == False]
        
        support_analysis = {
            'churned_avg_resolution_time': churned['avg_resolution_time'].mean(),
            'retained_avg_resolution_time': retained['avg_resolution_time'].mean(),
            'churned_avg_satisfaction': churned['avg_satisfaction_score'].mean(),
            'retained_avg_satisfaction': retained['avg_satisfaction_score'].mean(),
            'churned_escalation_rate': (churned['escalation_count'] / (churned['support_ticket_count'] + 1)).mean(),
            'retained_escalation_rate': (retained['escalation_count'] / (retained['support_ticket_count'] + 1)).mean(),
        }
        
        # Tickets analysis
        support_analysis['churned_avg_tickets'] = churned['support_ticket_count'].mean()
        support_analysis['retained_avg_tickets'] = retained['support_ticket_count'].mean()
        
        # Unresolved/slow resolution in churned
        slow_resolution_rate = (churned['avg_resolution_time'] > 96).sum() / len(churned) * 100
        support_analysis['slow_resolution_rate_churned'] = slow_resolution_rate
        
        self.results['support_quality'] = support_analysis
        logger.info(f"Support quality analysis: {support_analysis}")
        
        return self
    
    def analyze_pricing_patterns(self):
        """Analyze pricing misalignment patterns preceding churn."""
        logger.info("Analyzing pricing patterns...")
        
        churned = self.data[self.data['churn_flag'] == True]
        retained = self.data[self.data['churn_flag'] == False]
        
        pricing_analysis = {
            'churned_had_downgrade': churned['downgrade_flag'].sum() / len(churned) * 100,
            'retained_had_downgrade': retained['downgrade_flag'].sum() / len(retained) * 100,
            'churned_had_upgrade': churned['upgrade_flag'].sum() / len(churned) * 100,
            'retained_had_upgrade': retained['upgrade_flag'].sum() / len(retained) * 100,
            'churned_avg_mrr': churned['mrr_amount'].mean(),
            'retained_avg_mrr': retained['mrr_amount'].mean(),
        }
        
        # Trial conversion pattern
        trial_churned = churned[churned['is_trial'] == True]
        if len(trial_churned) > 0:
            pricing_analysis['trial_churn_rate'] = len(trial_churned) / len(churned) * 100
        else:
            pricing_analysis['trial_churn_rate'] = 0
        
        # Downgrade before churn
        pricing_analysis['downgrade_before_churn_rate'] = churned['preceding_downgrade_flag'].sum() / len(churned) * 100
        
        self.results['pricing_patterns'] = pricing_analysis
        logger.info(f"Pricing patterns: {pricing_analysis}")
        
        return self
    
    def analyze_time_to_value(self):
        """Analyze time to adoption and time to first interaction."""
        logger.info("Analyzing time to value...")
        
        churned = self.data[self.data['churn_flag'] == True]
        retained = self.data[self.data['churn_flag'] == False]
        
        # Calculate days to first use (signup_date to first_usage_date)
        churned['days_to_first_use'] = (
            pd.to_datetime(churned['first_usage_date']) - pd.to_datetime(churned['signup_date'])
        ).dt.days
        retained['days_to_first_use'] = (
            pd.to_datetime(retained['first_usage_date']) - pd.to_datetime(retained['signup_date'])
        ).dt.days
        
        # Calculate subscription tenure
        reference_date = pd.to_datetime('2024-10-31')
        churned['tenure_days'] = (reference_date - pd.to_datetime(churned['start_date'])).dt.days
        retained['tenure_days'] = (reference_date - pd.to_datetime(retained['start_date'])).dt.days
        
        ttv_analysis = {
            'churned_days_to_first_use': churned['days_to_first_use'].mean(),
            'retained_days_to_first_use': retained['days_to_first_use'].mean(),
            'churned_never_used': (churned['first_usage_date'].isna()).sum() / len(churned) * 100,
            'retained_never_used': (retained['first_usage_date'].isna()).sum() / len(retained) * 100,
            'churned_quick_start': ((churned['days_to_first_use'] >= 0) & (churned['days_to_first_use'] <= 7)).sum() / len(churned) * 100,
            'retained_quick_start': ((retained['days_to_first_use'] >= 0) & (retained['days_to_first_use'] <= 7)).sum() / len(retained) * 100,
            'churned_tenure_days': churned['tenure_days'].mean(),
            'retained_tenure_days': retained['tenure_days'].mean(),
        }
        
        self.results['time_to_value'] = ttv_analysis
        logger.info(f"Time to value: {ttv_analysis}")
        
        return self
    
    def analyze_industry_geography(self):
        """Analyze churn patterns by industry and country."""
        logger.info("Analyzing industry and geography patterns...")
        
        industry_churn = self.data.groupby('industry').agg({
            'churn_flag': ['sum', 'count', 'mean']
        }).reset_index()
        industry_churn.columns = ['industry', 'churn_count', 'total_accounts', 'churn_rate']
        industry_churn = industry_churn.sort_values('churn_rate', ascending=False)
        
        country_churn = self.data.groupby('country').agg({
            'churn_flag': ['sum', 'count', 'mean']
        }).reset_index()
        country_churn.columns = ['country', 'churn_count', 'total_accounts', 'churn_rate']
        country_churn = country_churn.sort_values('churn_rate', ascending=False)
        
        plan_churn = self.data.groupby('plan_tier').agg({
            'churn_flag': ['sum', 'count', 'mean']
        }).reset_index()
        plan_churn.columns = ['plan_tier', 'churn_count', 'total_accounts', 'churn_rate']
        plan_churn = plan_churn.sort_values('churn_rate', ascending=False)
        
        self.results['industry_churn'] = industry_churn.to_dict('records')
        self.results['country_churn'] = country_churn.to_dict('records')
        self.results['plan_churn'] = plan_churn.to_dict('records')
        
        logger.info(f"Industry churn rates:\n{industry_churn}")
        logger.info(f"Plan churn rates:\n{plan_churn}")
        
        return self
    
    def analyze_churn_reasons(self):
        """Analyze stated reasons for churn."""
        logger.info("Analyzing churn reasons...")
        
        churned_with_reason = self.data[self.data['churn_flag'] == True]['reason_code'].value_counts()
        churn_reasons = {
            'top_reasons': churned_with_reason.head(5).to_dict(),
            'reason_distribution': (churned_with_reason / churned_with_reason.sum() * 100).to_dict()
        }
        
        self.results['churn_reasons'] = churn_reasons
        logger.info(f"Top churn reasons:\n{churned_with_reason}")
        
        return self
    
    def generate_summary_report(self):
        """Generate executive summary of root causes."""
        logger.info("Generating root cause summary...")
        
        summary = {
            'primary_causes': [],
            'secondary_causes': [],
            'metrics': {}
        }
        
        # Feature adoption is primary cause if gap > 40%
        if self.results['feature_adoption']['gap_percentage'] > 40:
            summary['primary_causes'].append({
                'cause': 'Lacuna de Adoção de Recursos',
                'severity': 'ALTA',
                'impact': f"{self.results['feature_adoption']['gap_percentage']:.1f}% lower adoption in churned accounts",
                'recommendation': 'Implementar programa proativo de onboarding de recursos'
            })
        
        # Support quality is primary cause if satisfaction < 3.0
        if self.results['support_quality']['churned_avg_satisfaction'] < 3.0:
            summary['primary_causes'].append({
                'cause': 'Problemas de Qualidade de Suporte',
                'severity': 'ALTA',
                'impact': f"Avg satisfaction {self.results['support_quality']['churned_avg_satisfaction']:.1f}/5 in churned",
                'recommendation': 'Melhorar conformidade de SLA e treinamento da equipe de suporte'
            })
        
        # Pricing misalignment
        if self.results['pricing_patterns']['trial_churn_rate'] > 30:
            summary['primary_causes'].append({
                'cause': 'Falha de Conversão de Trial',
                'severity': 'ALTA',
                'impact': f"{self.results['pricing_patterns']['trial_churn_rate']:.1f}% of churned were trials",
                'recommendation': 'Melhorar experiência de trial e campanhas de conversão'
            })
        
        summary['metrics'] = {
            'overall_churn_rate': (self.data['churn_flag'].sum() / len(self.data) * 100),
            'churned_accounts': self.data['churn_flag'].sum(),
            'total_accounts': len(self.data)
        }
        
        self.results['summary'] = summary
        logger.info(f"Root cause summary: {summary}")
        
        return self
    
    def get_results(self):
        """Get all analysis results."""
        return self.results
    
    def save_analysis(self, output_path='outputs/root_cause_analysis.csv'):
        """Save analysis results to CSV."""
        import os
        import json
        os.makedirs('outputs', exist_ok=True)
        
        # Save as JSON for better structure
        with open(output_path.replace('.csv', '.json'), 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"Analysis saved to {output_path}")
        return self


if __name__ == '__main__':
    import importlib.util
    import json
    
    spec = importlib.util.spec_from_file_location("preprocessing", "01_data_preprocessing.py")
    preprocessing = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preprocessing)
    DataPreprocessor = preprocessing.DataPreprocessor
    
    preprocessor = DataPreprocessor()
    merged_data = preprocessor.load_raw_data().merge_datasets().handle_missing_values().get_merged_data()
    
    analyzer = RootCauseAnalysis(merged_data)
    (analyzer.analyze_feature_adoption_gap()
     .analyze_support_quality()
     .analyze_pricing_patterns()
     .analyze_time_to_value()
     .analyze_industry_geography()
     .analyze_churn_reasons()
     .generate_summary_report()
     .save_analysis())
    
    print("\n=== ROOT CAUSE ANALYSIS COMPLETE ===")
    print(json.dumps(analyzer.get_results()['summary'], indent=2, default=str))
