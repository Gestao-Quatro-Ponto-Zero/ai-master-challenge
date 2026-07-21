# Metodologia do JourneyGraph

## Escopo

NetworkX 3.x é a implementação de referência local. O instance graph privilegia explicabilidade; o analytical graph privilegia padrões agregados promovíveis.

## Identificadores

SHA-256 truncado em 16 caracteres com salt público de namespacing. O account_id bruto participa somente do cálculo local e nunca é persistido em propriedade pública ou mapeamento reversível.

## Promoção

Somente ROBUST/SENSITIVE, suporte mínimo, denominador positivo, `small_sample=false` e dependência diferente de HIGH. Rejeições são contabilizadas em `graph_quality.json`.

## Centralidade

PageRank, grau ponderado e betweenness foram calculados apenas em EventType, com sensibilidade a account_support, relative_support e transition_count. Pattern recebe ranking somente por suporte/MRR agregado. Account nunca recebe centralidade.

## Caminhos e MRR

Caminhos têm no máximo seis eventos e suporte mínimo de dez contas. MRR é soma/mediana/média associada às contas correspondentes, sem interpretação de perda ou economia.

## Reconciliação

Contas, jornadas, taxonomia, padrões, transições, findings, outcomes e MRR foram reconciliados. Diferença inexplicada: 0.
