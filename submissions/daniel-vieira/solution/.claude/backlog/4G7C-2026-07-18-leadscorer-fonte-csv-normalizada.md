---
id: 4G7C
parent:
project: LeadScorer
subject: Fonte CSV normalizada como camada de limpeza canônica
author: dcvr@
priority: high
status: done
created: 2026-07-18
updated: 2026-07-18
---


# Descrição (o que será feito)

Gerar uma fonte CSV normalizada e derivada em 'data/normalized/', a partir dos CSV brutos
imutáveis de 'data/', por meio de um script DuckDB versionado que é a fonte única de verdade das
correções de limpeza. Repontar os consumidores (a análise exploratória e, adiante, a modelagem)
para a fonte normalizada, eliminando as correções em linha.


# Motivações (por que será feito)

A análise exploratória identificou inconsistências de descrição, em especial 'GTXPro' versus
'GTX Pro', que quebra o cruzamento com o catálogo de preços e afeta o retorno econômico da
modelagem. A correção estava dispersa em consultas, sem fonte única. A modelagem requer uma
fonte limpa e canônica, com os dados brutos preservados. A decisão está registrada no ADR F3N8.


# Recursos e dados necessários

- Os CSV brutos em 'data/' (2H5K) e as correções identificadas na EDA (1J8R);
- DuckDB, para o script de normalização e a leitura direta dos CSV.


# Plano de trabalho (como será feito)

- Escrever 'scripts/normalize.sql' com as correções (produto, setor, país);
- Gerar 'data/normalized/' e verificar as correções e a preservação das contagens;
- Repontar 'scripts/eda.sql' para a fonte normalizada e confirmar resultados idênticos;
- Documentar o passo de normalização e registrar o ADR.


# Riscos e ressalvas

- Os derivados normalizados devem ser regenerados quando os dados brutos forem readquiridos;
- Novas inconsistências futuras devem ser adicionadas ao script, mantendo a fonte única.


# Dependências

- blocks: 3RJ8, 5T6Q
- blocked-by: 1J8R


# Definição de pronto

O script 'scripts/normalize.sql' gera 'data/normalized/' com as três correções aplicadas
(produto, setor, país) e as contagens preservadas, o cruzamento pipeline-catálogo fica sem
órfãos, a análise exploratória consome a fonte normalizada sem correções em linha e reproduz os
resultados de forma idêntica, e a decisão está registrada no ADR F3N8.
