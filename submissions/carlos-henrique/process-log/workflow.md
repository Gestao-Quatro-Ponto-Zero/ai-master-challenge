# Workflow — Fase 0

## Registro da execução

- **Data e hora local de início:** 2026-07-20 15:00:15 -03:00
- **Fuso horário:** America/Sao_Paulo
- **Fase:** Fase 0 — Fundação, contexto e segurança do repositório
- **Objetivo:** estabelecer uma estrutura documental limpa, rastreável, segura e reproduzível para o JourneyGraph sem executar análise ou produzir resultados.

## Contexto inicial

- workspace: `C:\Users\ataqu\Documents\GitHub\ai-master-challenge`;
- branch esperada: `submission/carlos-henrique`;
- HEAD esperado: `4aed364d572fabe0f1fff1f0c6f32960b30fe575`;
- remotes esperados: fork em `origin` e repositório oficial em `upstream`;
- `submissions/` ignorada pelo `.gitignore` da raiz;
- cinco datasets oficiais ausentes e não autorizados para download nesta fase.

## Verificações iniciais executadas

1. resolução do diretório de trabalho;
2. inspeção de branch, remotes e HEAD;
3. confirmação de igualdade entre HEAD, `main`, `origin/main` e `upstream/main`;
4. confirmação de working tree limpo;
5. confirmação de staging vazio;
6. busca por conteúdo versionado prévio do Challenge 002;
7. leitura das instruções oficiais do repositório, do Challenge 001, do guia, do template e das regras de contribuição.

O gate inicial foi aprovado sem correções silenciosas.

## Arquivos criados

- `README.md`;
- `solution/README.md`;
- `solution/requirements.txt`;
- `solution/src/__init__.py`;
- `solution/scripts/README.md`;
- `solution/tests/README.md`;
- `solution/data/raw/README.md`;
- `solution/data/processed/README.md`;
- `solution/artifacts/README.md`;
- `solution/reports/README.md`;
- `docs/architecture.md`;
- `docs/data-contract.md`;
- `docs/repository-policy.md`;
- `process-log/workflow.md`;
- `process-log/prompts.md`;
- `process-log/decisions.md`.

## Validações

O checklist final deverá confirmar legibilidade, estrutura exata, escopo dos caminhos, ausência de pacotes proibidos, datasets, CSVs, segredos, resultados analíticos e conteúdo indevido; origem da regra de ignore; staging seletivo; diff completo; compilação do pacote vazio; e estado Git após o commit.

### Resultado das validacoes finais

- 16 arquivos e nenhuma divergencia da estrutura autorizada;
- leitura UTF-8 de todos os textos;
- 12 dependencias permitidas e nenhuma dependencia proibida;
- ausencia de datasets, CSVs, segredos, arquivos grandes e resultados analiticos;
- nenhuma criacao ou alteracao fora de `submissions/carlos-henrique/`;
- regra de ignore originada em `.gitignore:16:submissions/`;
- compilacao bem-sucedida de `solution/src/__init__.py`, seguida da remocao do cache gerado;
- staging seletivo de 16 arquivos e nenhum caminho externo;
- revisao dos caminhos e do diff staged completo antes do commit.

A primeira tentativa de staging nao conseguiu criar `.git/index.lock` por restricao de permissao do sandbox e adicionou zero arquivos. Os mesmos comandos individuais foram reexecutados com a permissao Git necessaria; nao houve ampliacao de escopo nem staging amplo. Trata-se de uma ocorrencia operacional do ambiente, nao de erro de implementacao.

## Resultado da fase

**Status no momento deste registro:** aguardando validações finais, staging seletivo e commit local.

**Atualizacao final:** PASS. A fundacao documental e estrutural foi validada e preparada para o unico commit local autorizado. Nenhuma analise foi executada, nenhum resultado foi produzido e nenhum dataset foi incluido.

## Próximo gate

A Fase 1 somente poderá começar depois que os cinco datasets oficiais estiverem presentes em `submissions/carlos-henrique/solution/data/raw/` e houver um novo prompt autorizando a auditoria das cinco fontes. Nenhuma auditoria foi iniciada.

---

# Workflow — Fase 1

## Registro da execução

- **Data e hora local da retomada:** 2026-07-20 16:18:37 -03:00
- **Fuso horário:** America/Sao_Paulo
- **Objetivo:** auditar tecnicamente as cinco fontes reais sem construir event log, diagnóstico, modelo, grafo ou dashboard.
- **Ambiente:** Python 3.12.10 no `.venv` local, com pandas, NumPy e pytest disponíveis; nenhum pacote foi instalado nesta execução.

## Gate de entrada repetido

Foram confirmados workspace, raiz Git, branch `submission/carlos-henrique`, HEAD `d5b12e2`, working tree limpo, staging vazio, cinco CSVs presentes e nenhum CSV versionado. O README de `data/raw` estava restaurado.

Antes da escrita de código foram registrados bytes, modificação UTC, linhas físicas e SHA-256:

| arquivo | bytes | linhas físicas | SHA-256 |
|---|---:|---:|---|
| `ravenstack_accounts.csv` | 36.649 | 501 | `348d8ba906b7776894b5236b2e7aa91a503d41670dbc9aad30c37b503c9abef5` |
| `ravenstack_subscriptions.csv` | 437.566 | 5.001 | `dcf1d93ca9a35e0dcba0ab686d255f0e9ec26512970bbf0944cf19cbef2d751a` |
| `ravenstack_feature_usage.csv` | 1.400.898 | 25.001 | `c081da2be8caf987d07f0f79ceb0619aba523d819529230ed6df77984fa21d4e` |
| `ravenstack_support_tickets.csv` | 145.598 | 2.001 | `ba0006951479771ee9f93c98789c96bc5fec892cf11f867afb28194f0b76d220` |
| `ravenstack_churn_events.csv` | 44.630 | 601 | `6391c41d8291b7b4845ec9a84d3837c2ed230a33a32a854ec33d4e66dc150940` |

## Hipóteses testadas

- IDs descritos publicamente poderiam ser chaves primárias ou estrangeiras válidas.
- As quatro relações mínimas poderiam ser referencialmente completas.
- Datas poderiam ordenar contas, assinaturas, uso, tickets e churn.
- Flags de churn poderiam concordar com eventos e datas de término.
- Joins diretos poderiam ou não preservar o grão de conta.
- Campos de texto poderiam conter padrões de email, telefone ou URL.

As hipóteses foram tratadas como candidatas até teste empírico.

## Implementação e comandos

Foram criados `data_loader.py`, `data_audit.py`, `inspect_data.py` e `test_data_audit.py`. O comando principal executado foi:

`submissions/carlos-henrique/solution/.venv/Scripts/python.exe submissions/carlos-henrique/solution/scripts/inspect_data.py`

Também foram executados `compileall` para `src` e `scripts`, pytest, leitura agregada de schemas, verificações de hashes, busca de padrões sensíveis, simulações key-only de joins e revisão dos relatórios.

## Resultados estruturais

- registros lidos: 500 contas, 5.000 assinaturas, 25.000 usos, 2.000 tickets e 600 churns;
- nenhuma linha completamente duplicada e nenhum valor negativo suspeito;
- `account_id`, `subscription_id`, `ticket_id` e `churn_event_id` são completos e únicos no snapshot;
- `usage_id` possui 21 duplicatas excedentes/42 linhas afetadas;
- o composto de uso testado possui 3 duplicatas excedentes/6 linhas afetadas;
- as quatro relações têm match de 100%, zero órfãos e cardinalidade um-para-muitos;
- mega-join simulado: 500 → 147.896 linhas, multiplicador 295,792×;
- 19.142 usos antecedem a assinatura e 1.077 tickets antecedem a conta;
- 53 churns antecedem a primeira assinatura e 55 não coincidem com assinatura ativa;
- 277 contas têm evento com flag falsa e 35 têm flag verdadeira sem evento;
- 175 contas possuem múltiplos churns e 61 eventos têm reativação explícita;
- nenhuma regex de email, telefone ou URL foi detectada nos campos textuais auditados.

## Verificação humana obrigatória

Foram revisados manualmente:

1. schemas e dtypes inferidos;
2. chaves simples e composta testada;
3. cardinalidades e distribuição de filhos por pai;
4. zero órfãos nas quatro relações;
5. multiplicadores de joins simples e encadeado;
6. sete colunas temporais reais, intervalos e parsing;
7. churn recorrente e máximo de eventos por conta;
8. reativação explícita e assinaturas posteriores a churn;
9. leakage explícito, temporal e proxy;
10. estatísticas agregadas de privacidade;
11. hashes e tamanhos dos cinco CSVs;
12. conteúdo integral dos três relatórios e quatro artefatos.

Nenhum dado foi considerado confiável apenas porque pandas o carregou.

## Erros reais e correções

1. A tentativa anterior da Fase 1 foi corretamente bloqueada por um README modificado; o usuário restaurou o arquivo e preparou o `.venv` antes desta retomada.
2. O primeiro pytest aprovou 13 testes, mas dois fixtures falharam porque o sandbox negou o diretório temporário padrão. Uma segunda tentativa com `basetemp` no `.venv` sofreu a mesma restrição. A execução autorizada fora do sandbox passou.
3. O detector inicial confundiu métricas de duração com timestamps. O padrão foi restringido a sufixos temporais reais e recebeu teste de regressão.
4. A inserção de dois checks temporais gerou um parêntese ausente; `compileall` detectou o SyntaxError e a estrutura foi corrigida.
5. Um novo teste foi inicialmente inserido antes do `from __future__`; a revisão do arquivo detectou o problema antes da suíte e moveu o teste para o final.

Resultado final de testes: 17 aprovados.

## Limitações e resultado

O snapshot não prova estabilidade histórica das chaves. A cronologia de uso e tickets apresenta conflito material com os ciclos de conta/assinatura. A flag de churn em contas não pode ser fonte soberana sem regra de precedência. Nenhum diagnóstico de churn foi produzido.

**Gate da Fase 2:** `PASS_WITH_WARNINGS`. O event log é tecnicamente possível somente com fontes separadas, identidade substituta para uso, regras de quarentena temporal, cutoffs as-of, precedência de target e preservação de churn recorrente/reativação.

## Próximo gate

Aguardar o prompt da Fase 2. Não iniciar automaticamente o event log.

## Validação final adicional

- duas execuções consecutivas do CLI produziram hashes idênticos nos sete outputs (`IDEMPOTENCE_FAILURES=0`);
- bytes, mtime, linhas físicas e SHA-256 dos cinco CSVs permaneceram idênticos ao baseline;
- os 15 arquivos autorizados existem, são pequenos e legíveis em UTF-8;
- zero nomes de conta ou feedbacks brutos foram encontrados nos outputs;
- zero emails e zero caminhos absolutos foram encontrados nos outputs;
- seis matches de uma regex ampla de telefone foram revisados e confirmados como falsos positivos de datas e notação numérica agregada;
- dois diretórios temporários deixados na raiz pela primeira tentativa do pytest foram removidos;
- caches `__pycache__` e o `pytest-temp` foram removidos após a validação;
- staging permaneceu vazio até a conclusão da revisão humana.
