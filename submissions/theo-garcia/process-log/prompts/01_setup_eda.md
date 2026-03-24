# Fase 1 — Setup e Exploração Inicial

## Contexto
Antes de qualquer código, li o briefing completo. O CEO diz que churn subiu mas uso cresceu e satisfação está ok. Isso é uma contradição — e contradições são onde os insights moram.

## O que pedi para a IA
- Carregar os 5 CSVs e mostrar shapes, dtypes, nulls, distribuições
- Validar integridade referencial entre todas as tabelas (FKs batem? Orphans?)

## O que EU decidi antes de começar
- Formato: dashboard interativo (não PDF) — o challenge valoriza "algo que o CS usaria amanhã"
- 5 leis de qualidade definidas antes de tocar nos dados
- Plano de 6 partes sequenciais

## O que encontrei
- 5 tabelas íntegras, zero orphans
- GAP entre churn_flag (110 contas = 22%) e churn_events (352 contas = 70%)
- 277 contas reativaram — o CEO está vendo só a ponta do iceberg
- 175 contas churnearam mais de uma vez

## Correção aplicada
A IA mostrou os números. EU percebi que o gap entre 22% e 70% era o insight mais importante do dataset — ela não flagou isso espontaneamente.
