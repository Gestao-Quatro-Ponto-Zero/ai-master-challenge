# Validação do JourneyGraph

## Avaliação geral: Share with caveats

O grafo está reconciliado e metodologicamente utilizável, com ressalvas herdadas de warnings, cobertura e ordem intradiária.

## Metodologia

Foram validados schema, duplicação, privacidade, temporalidade, promoção, propriedades GraphML e semântica não causal nos dois grafos.

## Evidência

- diferença inexplicada: 0;
- IDs operacionais expostos: 0;
- violações temporais: 0;
- padrões UNSTABLE promovidos: 0;
- relações causais: 0.

## Ressalvas obrigatórias

- centralidade é estrutural;
- MRR é associado;
- EventInstance CSV é amostra, enquanto GraphML mantém o grafo completo;
- a execução externa do Neo4j não integra o gate.
