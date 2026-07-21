---
id: V9K3
project: LeadScorer
subject: Versionamento da fonte normalizada e das features derivadas como insumos do conteiner
author: dcvr@
status: accepted
created: 2026-07-20
updated: 2026-07-20
---


# Contexto (por que a decisão é necessária)

A Fase 1 da tarefa 6X9H exige que um avaliador leigo clone o repositório e suba as duas
aplicações web em um único comando. Dois insumos de dados são necessários a essa execução: o seed
do banco (ver 'src/seed.lisp') lê a fonte normalizada de 'data/normalized/*.csv', e o agendador
de pontuações da camada web (ver 'src/web/scheduler.lisp' e 'ls:load-model' em 'src/model.lisp')
lê as features derivadas de 'data/derived/' para produzir as pontuações, que são o valor central
do produto. Pela política vigente, registrada no ADR F3N8 e em 'docs/dataset.md', 'data/' não é
versionado: os dados brutos vêm do Kaggle mediante token de API e as camadas normalizada e
derivada são regeneradas localmente com DuckDB. Um clone limpo, portanto, não contém esses dados,
o que torna o "um passo" impossível sem que o avaliador configure credenciais do Kaggle e execute
os scripts de normalização e modelagem. É necessário decidir como disponibilizar esses insumos
sem violar o princípio de segurança desde a concepção.

O dataset de origem (CRM Sales Predictive Analytics) está licenciado sob CC0, ou seja, em domínio
público, o que autoriza a sua redistribuição. É um dado sintético, de demonstração, sem qualquer
informação sensível ou pessoal de clientes reais.


# Decisão (o que foi decidido)

São versionados no repositório dois conjuntos de insumos reprodutíveis: a fonte normalizada
'data/normalized/*.csv', insumo do seed, e as quatro features derivadas independentes dos
pesos do modelo que 'load-model' consome em tempo de execução (a saber, 'potentials_base.csv',
'initiated_base.csv', 'adherence.csv' e 'decay.csv'), insumo do agendador de pontuações. Permanecem
fora do controle de versão os dados brutos em 'data/', os artefatos de scoring dependentes dos
pesos ('data/derived/*_scored.csv'), que são saída do modelo e não entrada, e o export de
diagnóstico 'data/derived/cadence.csv', que não é relido em runtime (a cadência entra por uma
coluna de 'potentials_base.csv'). O '.gitignore' é ajustado para desbloquear apenas esses arquivos,
preservando a exclusão do restante de 'data/'.


# Alternativas consideradas (o que mais foi ponderado)

- Baixar os CSV de um release ou URL público no build ou no entrypoint do conteiner: preterida por
  adicionar uma dependência de rede em tempo de subida e a manutenção de um artefato hospedado à
  parte, sem ganho de segurança, dado que o dado é público e não sensível.
- Manter estritamente a aquisição via Kaggle pelo avaliador: preterida por contrariar o objetivo
  declarado da Fase 1, pois exige conta e token do Kaggle e a execução manual da normalização e
  da modelagem, deixando de ser "um passo" para um leigo.
- Gerar as features derivadas no build com o DuckDB, mantendo-as fora do versionamento: preterida
  por adicionar uma dependência de build e mais superfície de falha, sem ganho material, dado que
  as features são pequenas e independentes dos pesos do modelo, mudando apenas com a fonte
  normalizada ou com 'scripts/modeling.sql'.
- Versionar também os dados brutos e os artefatos '*_scored': preterida por desnecessária; o seed
  e o agendador consomem apenas a fonte normalizada e as features, e os '*_scored' são saída
  dependente dos pesos, não entrada.


# Consequências (o que resulta da decisão)

- O clone do repositório passa a conter o insumo do seed e as features do modelo, tornando viável
  a execução em um passo em Docker e Podman, com as pontuações materializadas, sem credenciais nem
  acesso à rede.
- A política de "dados fora do versionamento" do ADR F3N8 é excepcionada de forma pontual e
  restrita a este dataset público CC0; os dados brutos e os artefatos de scoring dependentes dos
  pesos continuam não versionados, e a segregação entre dado exposto e dado sensível permanece
  intacta, pois nenhum dado sensível entra no controle de versão.
- 'scripts/normalize.sql' e 'scripts/modeling.sql' permanecem a fonte única de verdade das
  correções e das features; os arquivos versionados são a sua saída e devem ser regenerados e
  recomitados quando os brutos forem readquiridos ou esses scripts mudarem.
- 'docs/dataset.md' é atualizado para registrar que a fonte normalizada e as features derivadas
  são versionadas como insumos, mantendo o procedimento de aquisição dos brutos.


# Relações

- supersedes:
- superseded-by:
- related-tasks: 6X9H, 4G7C
