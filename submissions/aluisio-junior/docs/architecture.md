# Architecture Overview — Churn Intelligence System

## 1. Solution Summary

The solution is a modular **Churn Intelligence System** designed to transform churn analytics into executive decision support.

It combines:

- **FastAPI** for backend services
- **XGBoost** for churn prediction
- **Gemini** for generative executive insights
- **Lovable** for product-oriented frontend delivery
- **ngrok** for temporary external access during development

---

## 2. Architecture Layers

### Data Layer
Sources:
- `ravenstack_accounts.csv`
- `ravenstack_subscriptions.csv`
- `ravenstack_feature_usage.csv`
- `ravenstack_support_tickets.csv`
- `ravenstack_churn_events.csv`

Processing:
- joins across accounts, subscriptions, usage, tickets, and churn events
- feature engineering for revenue, support, and usage metrics
- derived analytical snapshot for account-level modeling

---

### Analytics Layer
Main KPI families:
- customer KPIs
- revenue KPIs
- churn KPIs
- risk KPIs
- segmentation KPIs

Examples:
- total MRR
- active MRR
- inactive MRR
- revenue at risk
- ARPU
- LTV proxy
- churn rate
- predictive churn by segment

---

### ML Layer
Model:
- **XGBoost Classifier**

Inputs:
- revenue
- seat count
- usage metrics
- error metrics
- support metrics
- satisfaction
- escalations

Outputs:
- `churn_score`
- `risk_level`

Risk classes:
- Alto
- Médio
- Baixo

---

### Explainability Layer
Explainability uses:
- feature importance
- SHAP-based global contribution analysis

Purpose:
- show which variables most influence churn risk
- help executives understand model behavior

---

### AI Layer
Model:
- **Gemini**

Purpose:
- answer executive questions
- summarize churn insights
- translate analytics into actions
- support recommendation generation

---

### Product Layer
Frontend modules:
- Dashboard
- Churn Risk
- Recommendations
- Kanban
- AI Chat
- WhatsApp approval simulation

Goal:
- move from prediction to execution

---

## 3. Backend Modules

### `data_service.py`
- dataset loading
- validation
- summary building

### `data_processing.py`
- analytical dataset construction
- revenue and support transformations
- account-level features

### `analysis.py`
- executive KPIs
- Pareto ABC
- revenue segmentation
- churn and risk aggregation

### `ml_model.py`
- model training
- feature importance
- probability scoring

### `shap_analysis.py`
- explainability outputs

### `ai_engine.py`
- Gemini integration
- executive response generation

### `main.py`
- endpoint orchestration
- payload assembly
- product-facing API layer

---

## 4. Core Endpoints

- `GET /kpis`
- `GET /dashboard-validation`
- `GET /churn-risk`
- `GET /insights`
- `GET /recommendations`
- `GET /kanban/projects`
- `POST /ask-ai`

---

## 5. Key Business Logic Decisions

### Active vs inactive accounts
The dataset does not provide a fully reliable current status flag. The solution uses analytical snapshot rules to define account activity for executive metrics.

### Historical churn vs predictive churn
These are treated separately:
- historical churn = what already happened
- predictive churn = expected future risk for active accounts

### LTV
LTV is modeled as a **proxy**, not realized lifetime billing, and is documented transparently.

### Revenue at risk
Revenue at risk is calculated only on active accounts classified as high risk.

---

## 6. Product Positioning

This is not only a churn dashboard.

It is a **Revenue Protection and Executive Decision Platform** that:

- identifies churn risk
- quantifies financial exposure
- prioritizes accounts
- generates recommendations
- supports operational execution

---

## 7. Future Evolution

- persistent model versioning
- production database
- automated retraining
- live WhatsApp approval flow
- multi-tenant SaaS packaging
- role-based access for C-Level, CS, Product, and Ops