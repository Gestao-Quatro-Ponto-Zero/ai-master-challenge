---
id: F3N8
project: LeadScorer
subject: Fonte de dados normalizada por dataset derivado
author: dcvr@
status: accepted
created: 2026-07-18
updated: 2026-07-18
---


# Contexto (por que a decisão é necessária)

A análise exploratória revelou inconsistências de descrição nos dados brutos: o produto 'GTXPro'
no pipeline onde o catálogo usa 'GTX Pro', o setor 'technolgy' e o país 'Philipines'. A primeira
é funcional, pois quebra o cruzamento com o catálogo de preços, do qual depende o retorno
econômico da modelagem; as demais são de grafia. Durante a EDA, a correção do produto foi
aplicada de forma dispersa, com um 'replace' repetido em consulta, sem fonte única de verdade.
A modelagem exige uma fonte limpa e canônica, enquanto os dados brutos devem permanecer
imutáveis.


# Decisão (o que foi decidido)

Gera-se um dataset derivado e normalizado em 'data/normalized/' a partir dos CSV brutos de
'data/', por meio de um script DuckDB versionado, 'scripts/normalize.sql', que é a fonte única
de verdade das correções de limpeza. Os dados brutos em 'data/' permanecem imutáveis. Os
derivados normalizados não são versionados, pois são regeneráveis a partir do script, e ficam
sob a regra de ignorar 'data/'. Tanto a análise exploratória quanto a modelagem consomem
'data/normalized/', de modo que nenhuma correção é aplicada em linha.


# Alternativas consideradas (o que mais foi ponderado)

- Correção em linha, dispersa pelas consultas e pelo código: descartada por não haver fonte
  única de verdade, com risco de divergência entre consumidores;
- Tabela de correções aplicada na ingestão em Common Lisp: viável, mas duplicaria as regras
  entre os motores (Common Lisp e SQL) e exigiria um escritor de CSV ainda inexistente na
  fundação; o COPY do DuckDB é declarativo e mais simples.


# Consequências (o que resulta da decisão)

- As correções residem em um único artefato versionado; os consumidores leem dados já limpos;
- Os dados brutos permanecem imutáveis, preservando a rastreabilidade da fonte;
- O DuckDB torna-se um passo de pré-processamento em tempo de modelagem, uso já sancionado pelo
  std-sql.md para pesquisa e modelagem; não é dependência de tempo de execução da aplicação;
- 'data/normalized/' deve ser regenerado sempre que os dados brutos forem readquiridos, o que
  consta da documentação de aquisição;
- A verificação persistida confirmou que a fonte normalizada reproduz a análise de forma
  idêntica à correção em consulta.


# Relações

- supersedes:
- superseded-by:
- related-tasks: 1J8R, 4G7C, 3RJ8, 5T6Q
