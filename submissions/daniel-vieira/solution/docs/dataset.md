# Aquisição do dataset CRM

Este documento descreve como obter e verificar o dataset utilizado na fase de modelagem. Os
arquivos brutos residem em 'data/' e não são versionados; apenas o procedimento é versionado. A
fonte normalizada em 'data/normalized/' e as features derivadas independentes dos pesos em
'data/derived/' que 'load-model' consome (a saber, 'potentials_base.csv', 'initiated_base.csv',
'adherence.csv' e 'decay.csv'), ao contrário, passaram a ser versionadas como insumos reprodutíveis
do seed e do agendador de pontuações, por serem derivadas de dado público sob licença CC0 e
precondição da execução em um passo (ADR V9K3); os brutos, os artefatos de scoring dependentes
dos pesos ('data/derived/*_scored.csv') e o export de diagnóstico 'data/derived/cadence.csv'
permanecem fora do controle de versão.


## Fonte

- Dataset: CRM Sales Predictive Analytics, no Kaggle, sob licença CC0;
- Identificador Kaggle: 'agungpambudi/crm-sales-predictive-analytics';
- Arquivos: accounts.csv, products.csv, sales_teams.csv, sales_pipeline.csv e metadata.csv,
  este último um dicionário de campos.


## Pré-requisitos

- Conta no Kaggle e token de API no formato padrão em '~/.kaggle/kaggle.json', contendo o nome
  de usuário e a chave, com permissão restrita ('chmod 600'). O token não é versionado e nunca
  entra no controle de versão;
- Interface de linha de comando do Kaggle, instalável de forma isolada com 'pipx install
  kaggle'. Trata-se de ferramenta de setup para a aquisição do dataset, e não de dependência de
  tempo de execução da aplicação; é a ferramenta oficial da fonte e substituível por download
  manual, de modo que a sua adoção não constitui decisão arquitetural que demande um ADR.


## Download

Executar a partir da raiz do projeto:

```bash
kaggle datasets download -d agungpambudi/crm-sales-predictive-analytics -p data/ --unzip
```

Os cinco arquivos CSV são extraídos em 'data/', que é ignorado pelo controle de versão.


## Verificação

O script 'scripts/verify-dataset.lisp' é a fonte canônica dos valores esperados de cada arquivo,
a saber, a coluna chave e a contagem de registros. Executar a partir da raiz do projeto:

```bash
qlot exec sbcl --non-interactive --load scripts/verify-dataset.lisp
```

O script encerra com estado nulo quando todos os arquivos estão conformes e com estado não nulo
quando algum arquivo está ausente ou diverge do esperado.


## Normalização

Os dados brutos contêm inconsistências de descrição (por exemplo, o produto 'GTXPro' onde o
catálogo usa 'GTX Pro'). O script 'scripts/normalize.sql' é a fonte única de verdade das
correções e gera a fonte normalizada em 'data/normalized/', consumida pela análise exploratória
e pela modelagem. Executar a partir da raiz do projeto, após a verificação:

```bash
mkdir -p data/normalized && duckdb < scripts/normalize.sql
```

O diretório 'data/normalized/' é derivado e passou a ser versionado como insumo do seed
(ADR V9K3); deve ser regenerado e recomitado sempre que os dados brutos forem readquiridos ou as
correções de 'scripts/normalize.sql' mudarem. Os dados brutos em 'data/' permanecem imutáveis e
não versionados.
