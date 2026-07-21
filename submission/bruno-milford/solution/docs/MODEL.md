# Modelo e Score de Churn

## Situação Atual

O projeto não possui um modelo preditivo de churn operacional baseado em machine learning. Não há script de treinamento, artefato de modelo, divisão treino/teste, inferência separada, métricas de validação ou pipeline de retreinamento.

O que existe é um score heurístico de risco implementado em `services/risk_service.py`. Ele combina regras fixas e pesos manuais para priorizar contas que merecem atenção de Customer Success.

## Problema Atendido pelo Score

O score busca responder:

> Quais contas ativas devem ser priorizadas por sinais operacionais de risco e valor financeiro?

Ele não deve ser interpretado como probabilidade calibrada de churn nem como explicação causal.

## Unidade de Análise

A unidade de análise é a conta (`account_id`).

Para cada conta, o serviço agrega:

- assinatura considerada na base consolidada;
- volume e recência de uso;
- erros;
- tickets de suporte;
- satisfação;
- sinais comerciais como downgrade, trial, cobrança mensal e renovação automática desligada.

## Variável-Alvo

Não há variável-alvo treinada. A regra de churn consolidada existe para status analítico da conta, mas não é usada para treinar um modelo.

Regra consolidada de churn:

```text
se o último evento de churn da conta for reativação:
    churned_account = 0
senão, se houver evento de churn:
    churned_account = 1
senão, se accounts.churn_flag = 1:
    churned_account = 1
senão:
    churned_account = 0
```

## Features Utilizadas pelo Score

| Sinal | Peso | Lógica |
| --- | ---: | --- |
| `no_recent_usage` | 18 | Sem uso conhecido ou mais de 45 dias desde o último uso. |
| `low_usage_volume` | 12 | `usage_volume < 50`. |
| `usage_drop` | 12 | Uso recente menor que 65% do período anterior. |
| `high_error_rate` | 14 | `errors / usage_volume > 0.18`, ou erro sem uso. |
| `many_errors` | 8 | `errors >= 20`. |
| `many_tickets` | 10 | `ticket_count >= 5`. |
| `urgent_tickets` | 8 | Pelo menos um ticket `urgent`, `high` ou `critical`. |
| `slow_response` | 6 | Média de primeira resposta maior que 180 minutos. |
| `slow_resolution` | 5 | Média de resolução maior que 72 horas. |
| `escalation` | 7 | Pelo menos um ticket escalado. |
| `low_satisfaction` | 10 | Satisfação média maior que 0 e menor que 3,5. |
| `downgrade` | 8 | `downgrade_flag` verdadeiro. |
| `auto_renew_off` | 7 | Renovação automática desligada. |
| `trial` | 5 | Conta/assinatura em trial. |
| `monthly_billing` | 4 | Cobrança mensal. |

## Pré-Processamento

O score calcula agregações diretamente por SQL:

- `usage_volume`: soma de `usage_count`;
- `errors`: soma de `error_count`;
- `last_usage_date`: maior `usage_date`;
- `usage_recent`: soma de uso nos últimos 30 dias em relação à maior data da tabela `feature_usage`;
- `usage_previous`: soma de uso entre 31 e 60 dias antes da maior data da tabela;
- `ticket_count`: total de tickets por conta;
- `urgent_tickets`: tickets com prioridade `urgent`, `high` ou `critical`;
- médias de resposta, resolução e satisfação;
- total de escalonamentos.

Datas inválidas ou ausentes são tratadas com fallback. Quando não existe uso recente conhecido, o sinal de ausência de uso é aplicado.

## Fórmulas

```text
risk_score = min(soma_dos_pesos_dos_sinais, 100)
value_score = min((mrr / 12000) * 100, 100)
priority_score = round((risk_score * 0.7) + (value_score * 0.3), 2)
```

## Faixas de Risco

| Score | Classificação |
| ---: | --- |
| 0 a 29 | baixo |
| 30 a 59 | medio |
| 60 a 79 | alto |
| 80 a 100 | critico |

## Interpretação

- `risk_score`: intensidade dos sinais operacionais de risco.
- `value_score`: aproximação de valor financeiro relativo com base no MRR.
- `priority_score`: ordenação prática para atuação, dando 70% de peso ao risco e 30% ao valor.
- `risk_signals`: lista textual dos sinais acionados.

Uma conta com score alto deve ser analisada por CS, Produto ou Receita, mas a decisão de intervenção deve considerar contexto qualitativo e histórico.

## Validação e Métricas

Não há validação estatística implementada. O projeto não calcula:

- acurácia;
- precisão;
- recall;
- AUC;
- matriz de confusão;
- calibração;
- validação temporal.

Para transformar o score em modelo preditivo, seria necessário criar um dataset supervisionado com janelas temporais, definir horizonte de previsão e medir desempenho fora da amostra.

## Riscos e Limitações

- Pesos são manuais.
- O score pode refletir viés dos dados sintéticos ou históricos.
- Pode haver vazamento temporal se sinais posteriores ao churn forem usados para prever churn passado.
- O uso da maior data global de `feature_usage` simplifica a análise temporal.
- Não há explicabilidade estatística além dos sinais acionados.
- `priority_score` favorece contas de maior MRR, o que pode reduzir atenção a contas menores em risco.
- A inconsistência entre `churn_flag` e eventos de churn exige decisão de negócio antes de treinar um modelo real.

## Componentes Necessários para um Modelo Futuro

Para implementar um modelo preditivo real, seriam necessários:

- definição oficial de churn;
- horizonte de previsão, por exemplo churn nos próximos 30/60/90 dias;
- geração de features com ponto de corte temporal;
- separação treino/teste temporal;
- tratamento de desbalanceamento;
- algoritmo e hiperparâmetros documentados;
- métricas de validação;
- artefato versionado do modelo;
- rotina de inferência;
- monitoramento de drift;
- explicabilidade por conta;
- histórico de previsões.
