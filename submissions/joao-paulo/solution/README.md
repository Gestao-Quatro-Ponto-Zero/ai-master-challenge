# Churn Diagnosis for RavenStack

Projeto final de submissão para o challenge de diagnóstico de churn da RavenStack.

O objetivo da solução é transformar dados cadastrais, contratuais, de uso, suporte e churn em uma leitura executiva e técnica da carteira, combinando:

- diagnóstico operacional por conta (`account_360`)
- priorização explicável de risco por regras de negócio
- score supervisionado de churn com avaliação temporal
- dashboard executivo em HTML pronto para apresentação

## Visão do problema

O problema de negócio não é apenas medir quem já churnou, e sim identificar quais contas apresentam sinais de enfraquecimento antes da perda de receita.

Para isso, a solução separa três camadas:

- visão cadastral: `churn_flag` da tabela de contas
- visão histórica observada: trilha de `churn_events` e reativações
- visão operacional atual: snapshot atual da carteira, score de churn e fila de retenção

Essa separação evita misturar definições diferentes de churn e transforma divergências em governança de KPI.

## Arquitetura da solução

O projeto foi organizado com DDD + Clean Architecture:

```text
src/churn_diagnosis/
  application/      # casos de uso e orquestração do pipeline
  domain/           # entidades, specifications e serviço de health score
  infrastructure/   # loaders e persistência dos outputs
  ml/               # dataset supervisionado, treino, avaliação e explicabilidade
  presentation/     # dashboard executivo em HTML
main.py             # entrypoint do pipeline
tests/              # suíte automatizada
```

## Dataset

O repositório usa o dataset do challenge, armazenado em `data/`:

- `ravenstack_accounts.csv`
- `ravenstack_subscriptions.csv`
- `ravenstack_feature_usage.csv`
- `ravenstack_support_tickets.csv`
- `ravenstack_churn_events.csv`

Crédito do dataset: RavenStack: Synthetic SaaS Dataset (Multi-Table), autor River @ Rivalytics.

## Como instalar

Recomendado: Python 3.12.

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e .
pip install -e .[dev]
```

## Como rodar do zero

Fluxo principal completo:

```bash
python main.py
```

Esse comando:

1. carrega os CSVs de `data/`
2. constrói o `account_360`
3. calcula health score e drivers por regra
4. monta o dataset supervisionado point-in-time
5. treina e avalia o classificador
6. gera o scoring atual da carteira
7. cria os artefatos de explicabilidade
8. salva os outputs em `output/`
9. gera o dashboard final em HTML

## Como gerar o dashboard final

Depois de rodar o pipeline principal:

```bash
python src/churn_diagnosis/presentation/generate_executive_dashboard.py
```

O arquivo final fica em:

- `output/dashboard_ceo_premium_ravenstack.html`

## Outputs gerados

Outputs operacionais e analíticos:

- `output/account_360.csv`
- `output/customer_health_score.csv`
- `output/churn_risk_drivers.csv`
- `output/churn_reconciliation.csv`
- `output/current_churn_scoring.csv`
- `output/account_model_explanations.csv`
- `output/model_global_explainability.csv`

Outputs de modelagem:

- `output/point_in_time_training_dataset.csv`
- `output/model_comparison.csv`
- `output/feature_importance_top25.csv`
- `output/model_metrics.json`
- `output/churn_classifier.joblib`

Output executivo:

- `output/dashboard_ceo_premium_ravenstack.html`

## Decisões de modelagem

### Definição do target

O target supervisionado foi formulado como previsão real de churn futuro:

- `target_churn_30d = 1` se ocorrer churn não ligado a reativação nos 30 dias após `snapshot_date`
- `target_churn_30d = 0` caso contrário

Essa definição evita que o modelo aprenda apenas “quem já churnou historicamente”.

### Recorte temporal

O dataset supervisionado usa múltiplos snapshots por conta.

- contas positivas: snapshots elegíveis antes do churn
- contas negativas: snapshots distribuídos ao longo do tempo
- features calculadas apenas com informação `<= snapshot_date`

O scoring exibido no `account_360` e no dashboard é sempre calculado no snapshot atual da carteira, separado do dataset histórico de treino.

### Avaliação do modelo

O projeto mantém duas avaliações:

- validação aleatória estratificada agrupada por conta
- validação temporal out-of-time com treino em snapshots antigos e validação em snapshots mais recentes

A leitura mais representativa para churn é a validação temporal, porque ela respeita a ordem cronológica do problema.

### Interpretação dos scores

O score supervisionado é interpretado em duas camadas:

- score atual: `current_churn_probability`
- faixa operacional: `current_risk_band`

Além disso, a explicabilidade foi separada em:

- explicabilidade global: variáveis que mais movem o risco no portfólio
- explicabilidade local: principais sinais que elevam ou reduzem o score de uma conta específica

## Explicabilidade

Para manter robustez e simplicidade, a solução não depende de SHAP.

Estratégia adotada:

- global: agregação da importância das features originais do modelo final, combinada com o impacto médio dessas features no portfólio atual
- local: explicação model-agnostic por perturbação simples, medindo quanto a probabilidade mudaria se cada feature da conta voltasse ao perfil típico observado no treino

Isso produz:

- drivers globais do modelo para a banca técnica
- drivers locais por conta para retenção e narrativa executiva

## Governança de KPI de churn

O projeto trata diferentes definições de churn explicitamente:

- histórico executivo oficial: `churn_flag`
- histórico observado por eventos: presença de `churn_events`
- operação atual: contas ativas, reativadas e score atual da carteira

A reconciliação entre essas leituras é salva em:

- `output/churn_reconciliation.csv`

## Limitações

- o modelo depende da qualidade e granularidade dos eventos disponíveis no dataset
- algumas features categóricas ainda carregam sinais fortes do contexto do dataset e pedem validação adicional em produção
- os warnings de folds sem predição positiva em alguns cenários de teste refletem a dificuldade do problema, não falha da pipeline
- a explicabilidade local é robusta e leve, mas não substitui ferramentas mais sofisticadas em um ambiente de produção com governança formal de modelos

## Próximos passos

- calibrar melhor as probabilidades do modelo final
- revisar features categóricas de alta influência para reduzir sinais espúrios
- expandir monitoramento de drift temporal
- incluir métricas operacionais como `precision@top_k` e `lift`
- evoluir a fila de retenção para playbooks segmentados por motivo de risco

## Qualidade e reprodutibilidade

Para validar a entrega:

```bash
python -m pytest
```

No estado final desta submissão, a suíte está passando integralmente.
