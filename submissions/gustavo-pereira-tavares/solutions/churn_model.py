import pandas as pd
import numpy as np
import joblib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChurnPredictor:
    """Churn prediction model for custom scenarios and explanations."""
    
    def __init__(self, model_dir='models'):
        self.model_dir = model_dir
        self.xgb_model = None
        self.lgb_model = None
        self.feature_columns = None
        self.shap_explainer = None
        self.load_models()
    
    def load_models(self):
        """Load pre-trained models."""
        try:
            self.xgb_model = joblib.load(f'{self.model_dir}/xgb_model.pkl')
            self.lgb_model = joblib.load(f'{self.model_dir}/lgb_model.pkl')
            self.feature_columns = joblib.load(f'{self.model_dir}/feature_columns.pkl')
            logger.info("Models loaded successfully")
        except FileNotFoundError as e:
            logger.error(f"Failed to load models: {e}")
            raise
    
    def prepare_scenario(self, scenario_dict):
        """Convert scenario dictionary to feature vector."""
        
        # Create a feature dataframe with all required features
        feature_data = {}
        
        # Map scenario inputs to expected features
        feature_mapping = {
            'adoption_rate': 'adoption_rate',
            'support_quality_score': 'support_quality_score',
            'support_ticket_count': 'support_ticket_count',
            'avg_resolution_time': 'avg_resolution_time',
            'avg_satisfaction_score': 'avg_satisfaction_score',
            'mrr_amount': 'mrr_amount',
            'days_since_signup': 'days_since_signup',
        }
        
        # Initialize all features with default values
        for col in self.feature_columns:
            feature_data[col] = 0
        
        # Update with provided values
        for scenario_key, feature_key in feature_mapping.items():
            if scenario_key in scenario_dict and feature_key in self.feature_columns:
                feature_data[feature_key] = scenario_dict[scenario_key]
        
        # Handle plan tier encoding
        if 'plan_tier' in scenario_dict:
            plan_tier_map = {'Basic': 1, 'Pro': 2, 'Enterprise': 3}
            plan_tier_encoded = plan_tier_map.get(scenario_dict['plan_tier'], 1)
            if 'plan_tier_encoded' in self.feature_columns:
                feature_data['plan_tier_encoded'] = plan_tier_encoded
        
        # Handle industry encoding (one-hot)
        if 'industry' in scenario_dict:
            industry = scenario_dict['industry']
            for col in self.feature_columns:
                if col.startswith('industry_'):
                    feature_data[col] = 1 if col == f'industry_{industry}' else 0
        
        # Create dataframe
        df = pd.DataFrame([feature_data])[self.feature_columns]
        return df
    
    def predict(self, scenario_dict):
        """Predict churn probability for a scenario."""
        
        # Prepare features
        X = self.prepare_scenario(scenario_dict)
        
        # Get predictions from both models
        xgb_proba = self.xgb_model.predict_proba(X)[0, 1]
        lgb_proba = self.lgb_model.predict_proba(X)[0, 1]
        
        # Ensemble prediction
        churn_probability = 0.6 * xgb_proba + 0.4 * lgb_proba
        
        # Assign risk tier
        if churn_probability >= 0.7:
            risk_tier = 'Critical'
        elif churn_probability >= 0.5:
            risk_tier = 'High'
        elif churn_probability >= 0.3:
            risk_tier = 'Medium'
        else:
            risk_tier = 'Low'
        
        # Calculate risk score (0-100)
        risk_score = int(churn_probability * 100)
        
        # Get feature importance (top drivers)
        top_drivers = self.get_top_drivers(X)
        
        # Generate recommendations
        recommendations = self.generate_recommendations(scenario_dict, churn_probability)
        
        return {
            'churn_probability': churn_probability,
            'risk_tier': risk_tier,
            'risk_score': risk_score,
            'top_drivers': top_drivers,
            'recommendations': recommendations,
            'xgb_probability': xgb_proba,
            'lgb_probability': lgb_proba
        }
    
    def get_top_drivers(self, X):
        """Get top 3 drivers for prediction."""
        
        # Use feature importance from model
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.xgb_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        # Map feature names to readable names
        feature_name_map = {
            'adoption_rate': 'Adoção de Recursos',
            'support_quality_score': 'Qualidade de Suporte',
            'avg_resolution_time': 'Tempo de Resposta',
            'avg_satisfaction_score': 'Satisfação',
            'mrr_amount': 'MRR da Conta',
            'days_since_signup': 'Idade da Conta',
            'support_ticket_count': 'Engajamento de Suporte',
            'unique_features_used': 'Recursos Utilizados',
            'days_since_last_use': 'Recência de Atividade',
            'arr_amount': 'ARR Anual',
            'is_trial': 'Conta Trial',
            'trial_converted': 'Trial Convertido',
            'upgrade_flag': 'Upgrade Realizado',
            'downgrade_flag': 'Downgrade Realizado',
            'has_upgrade': 'Tem Upgrade',
            'has_downgrade': 'Tem Downgrade',
            'total_usage_count': 'Total de Usos',
            'avg_usage_count': 'Uso Médio',
            'usage_intensity': 'Intensidade de Uso',
            'days_since_activity': 'Dias sem Atividade',
            'escalation_rate': 'Taxa de Escalação',
            'support_engagement_level': 'Nível de Engajamento',
            'usage_days': 'Dias de Uso',
            'plan_tier': 'Nível do Plano',
            'days_since_first_use': 'Dias desde Primeiro Uso',
            'seats': 'Número de Assentos',
            'days_to_first_use': 'Dias até Primeiro Uso',
        }
        
        top_3 = {}
        for _, row in feature_importance.head(5).iterrows():
            feature = row['feature']
            importance = row['importance']
            
            readable_name = feature_name_map.get(feature, feature)
            if readable_name not in top_3 and len(top_3) < 3:
                top_3[readable_name] = float(importance)
        
        return top_3
    
    def generate_recommendations(self, scenario_dict, churn_probability):
        """Generate actionable recommendations."""
        recommendations = []
        
        # Based on probability
        if churn_probability >= 0.7:
            recommendations.append('🔴 CRÍTICO: Agendar chamada imediata com gerente de sucesso')
            recommendations.append('🔴 Oferecer desconto de retenção ou upgrade de plano')
            recommendations.append('🔴 Atribuir contato de suporte dedicado')
        elif churn_probability >= 0.5:
            recommendations.append('🟠 RISCO ALTO: Agendar workshop de adoção de produtos')
            recommendations.append('🟠 Revisar e melhorar SLAs de suporte')
            recommendations.append('🟠 Contato proativo com soluções de casos de uso')
        elif churn_probability >= 0.3:
            recommendations.append('🟡 MÉDIO: Enviar email de adoção de recursos')
            recommendations.append('🟡 Oferecer webinar sobre recursos avançados')
        else:
            recommendations.append('🟢 BAIXO: Continuar com engajamento padrão')
        
        # Based on scenario details
        if scenario_dict.get('adoption_rate', 0) < 0.3:
            recommendations.append('→ Realizar treinamento de onboarding de recursos')
        
        if scenario_dict.get('avg_satisfaction_score', 4) < 3.0:
            recommendations.append('→ Resolver problemas de qualidade de suporte com urgência')
        
        if scenario_dict.get('avg_resolution_time', 48) > 96:
            recommendations.append('→ Melhorar tempo de resolução de suporte (<24h)')
        
        if scenario_dict.get('days_since_signup', 180) < 90:
            recommendations.append('→ Fortalecer onboarding para conta nova')
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def explain_scenario(self, scenario_dict):
        """Provide detailed explanation of a prediction."""
        prediction = self.predict(scenario_dict)
        
        explanation = {
            'scenario': scenario_dict,
            'prediction': prediction,
            'explanation': []
        }
        
        # Add contextual explanations
        if prediction['churn_probability'] > 0.5:
            if scenario_dict.get('adoption_rate', 0) < 0.5:
                explanation['explanation'].append(
                    f"Feature adoption ({scenario_dict.get('adoption_rate', 0)*100:.0f}%) is significantly below healthy levels (>50%)"
                )
            
            if scenario_dict.get('avg_satisfaction_score', 4) < 3.5:
                explanation['explanation'].append(
                    f"Support satisfaction score ({scenario_dict.get('avg_satisfaction_score', 4):.1f}/5) is low"
                )
        
        return explanation


if __name__ == '__main__':
    # Test the predictor
    predictor = ChurnPredictor()
    
    # Test scenario 1: High risk
    scenario1 = {
        'adoption_rate': 0.2,
        'support_quality_score': 0.3,
        'support_ticket_count': 2,
        'avg_resolution_time': 120,
        'avg_satisfaction_score': 2.5,
        'mrr_amount': 1000,
        'days_since_signup': 60,
        'plan_tier': 'Basic',
        'industry': 'EdTech'
    }
    
    result = predictor.predict(scenario1)
    print("\n=== SCENARIO 1: High Risk ===")
    print(f"Churn Probability: {result['churn_probability']*100:.1f}%")
    print(f"Risk Tier: {result['risk_tier']}")
    print(f"Top Drivers: {result['top_drivers']}")
    print("Recommendations:")
    for rec in result['recommendations']:
        print(f"  {rec}")
    
    # Test scenario 2: Low risk
    scenario2 = {
        'adoption_rate': 0.8,
        'support_quality_score': 0.85,
        'support_ticket_count': 8,
        'avg_resolution_time': 24,
        'avg_satisfaction_score': 4.5,
        'mrr_amount': 5000,
        'days_since_signup': 300,
        'plan_tier': 'Enterprise',
        'industry': 'DevTools'
    }
    
    result = predictor.predict(scenario2)
    print("\n=== SCENARIO 2: Low Risk ===")
    print(f"Churn Probability: {result['churn_probability']*100:.1f}%")
    print(f"Risk Tier: {result['risk_tier']}")
    print(f"Top Drivers: {result['top_drivers']}")
