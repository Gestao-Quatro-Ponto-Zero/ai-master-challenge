# Prompts usados — resumo

Não incluí prompts verbatim longos para evitar um arquivo excessivo. Abaixo estão os tipos de prompts usados e o objetivo de cada rodada.

## Rodada 1 — Decomposição
“Leia o challenge 002 e me ajude a decompor em diagnóstico, automação, protótipo e process log. A solução precisa evitar red flags como automatizar tudo.”

## Rodada 2 — Auditoria de dados
“Antes de modelar, audite os CSVs: tamanho, colunas, nulos, distribuição de status, consistência dos timestamps, sinais de dado sintético e vazamento de dados.”

## Rodada 3 — Crítica de hipóteses
“Compare hipóteses geradas por outras IAs: 67,3% aguardando cliente, auto-close gerando churn, B2C vs B2E, domain shift. Diga quais são sustentadas pelos dados.”

## Rodada 4 — Modelagem
“Compare ComplementNB e Logistic Regression no Dataset 2. Use train/test split, F1 macro, acurácia, matriz de confusão e tabela de confidence gate.”

## Rodada 5 — Arquitetura
“Transforme os achados em um protótipo real. Prefiro FastAPI em vez de Streamlit porque quero algo integrável.”

## Rodada 6 — Process log
“Reescreva o process log conforme o Guia de Submissão: ferramentas usadas, decomposição, onde a IA errou, o que corrigi, o que adicionei e quantas iterações foram necessárias.”
