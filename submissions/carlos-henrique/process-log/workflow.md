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

---

# Workflow — Fase 2

## Registro da execução

- **Data e hora local:** 2026-07-20 17:18:29 -03:00;
- **Fuso horário:** America/Sao_Paulo;
- **Objetivo:** construir e validar a camada temporal canônica sem produzir diagnóstico, receita em risco, survival, journey mining, grafo, watchlist, modelo ou dashboard;
- **Commit-base:** `b9f341b92af080e4abf30282171994905cf0a780`.

## Gate de entrada

Antes de qualquer alteração foram confirmados workspace e raiz Git corretos, branch `submission/carlos-henrique`, HEAD esperado, working tree limpo, staging vazio, nenhum CSV bruto versionado e nenhuma modificação externa ao escopo.

Os cinco SHA-256 foram recalculados pelo build e comparados ao `raw_file_manifest.json` da Fase 1. Todos permaneceram idênticos.

## Semântica implementada

1. eventos permanecem separados por fonte e entidade, sem mega-join;
2. `event_id` usa hash determinístico de fonte, ID original, linha física, tipo e tempo;
3. `source_table`, `source_record_id` e `source_row_number` preservam provenance;
4. datas usam `datetime64[ns]` e `NAIVE_SOURCE_TIME`;
5. desempate no mesmo dia é técnico, estável e não causal;
6. churn é evento recorrente de conta;
7. reativação explícita é evento distinto e não cria assinatura;
8. cada `subscription_id` forma um episódio independente;
9. atribuição churn–assinatura somente preenche candidato para uma assinatura ativa exata;
10. texto livre, nomes, flags snapshot, motivo e refund não entram no event log.

## Política de qualidade

Foram separados três statuses: `VALID`, `VALID_WITH_WARNING` e `QUARANTINED`. A política conservadora coloca em quarentena cronologia fatal confirmada, incluindo evento pré-conta, uso pré/pós-assinatura, churn pré-assinatura e reativação sem churn anterior utilizável.

Duplicatas distintas de `usage_id` ou chave candidata foram preservadas e sinalizadas. Somente duplicatas integrais secundárias podem ser removidas; zero foram encontradas no snapshot.

## Outputs finais

- eventos gerados: 35.586;
- ativos: 13.927;
- válidos: 10.703;
- com warning: 3.224;
- quarentena: 21.659;
- episódios: 5.000;
- diferença não explicada: zero;
- período: 2023-01-01 00:00:00 a 2024-12-31 19:00:00.

Tipos gerados: 500 ACCOUNT_CREATED, 5.000 SUBSCRIPTION_STARTED, 486 SUBSCRIPTION_ENDED, 25.000 FEATURE_USED, 2.000 SUPPORT_TICKET_OPENED, 2.000 SUPPORT_TICKET_CLOSED, 539 CHURN_RECORDED e 61 REACTIVATION_RECORDED.

## Qualidade observada

- 19.142 usos pré-assinatura;
- 290 usos pós-assinatura;
- 15.347 eventos pré-conta, considerando todas as fontes;
- 53 churns pré-primeira-assinatura;
- 55 eventos de churn/reativação sem assinatura ativa;
- 478 atribuições com múltiplas assinaturas ativas;
- 31 reativações sem churn anterior utilizável;
- 42 linhas afetadas por `usage_id` duplicado e 6 pela chave candidata duplicada;
- 5.011 eventos com desempate técnico no mesmo dia.

## Churn, reativação e episódios

Após separar as 61 reativações dos churns, existem 161 contas sem CHURN_RECORDED, 190 com um e 149 com múltiplos; o máximo permanece cinco. Há 501 churns sem reativação posterior observada.

Das 600 ocorrências de churn/reativação, 67 têm uma assinatura ativa exata, 478 têm múltiplas candidatas, 53 não têm assinatura iniciada e 2 possuem somente uma assinatura anterior. Nenhum vínculo ambíguo foi inventado.

Os 5.000 episódios incluem 4.514 abertos, 486 encerrados e 4.992 afetados por sobreposição. Sobreposição é warning; churn não altera `end_date`.

## Testes e idempotência

- `compileall` de `src`, `scripts` e testes: aprovado;
- pytest final: 38 testes aprovados;
- duas gerações consecutivas: 10 de 10 outputs com SHA-256 idêntico;
- `IDEMPOTENCE_FAILURES=0`;
- Parquet finais: aproximadamente 0,64 MB, 0,89 MB e 0,20 MB.

## Erros reais e correções

1. O `.venv` não continha engine Parquet. PyArrow 25.0.0 foi instalado somente em diretório temporário externo ao repositório; `.venv` e requirements não foram alterados, e o diretório temporário foi removido após a validação.
2. O sandbox negou leitura ao pacote temporário. O build foi repetido com permissão local restrita ao acesso do engine e aos outputs autorizados.
3. A primeira revisão agregada revelou que múltiplas assinaturas ativas recebiam incorretamente a flag de ausência de assinatura. A condição foi restringida aos estados realmente sem ativa.
4. Churn pré-primeira-assinatura estava como warning apesar da política textual de quarentena. A flag foi incluída no conjunto fatal e os outputs foram regenerados.
5. O primeiro pytest teve 37 aprovações e uma falha no teste de privacidade porque a concatenação tinha índice repetido para `to_json`. O teste passou a usar `orient=records`; resultado final 38/38.
6. A ferramenta de patch encontrou a limitação de writable roots do sandbox do Windows em atualizações pontuais. Os mesmos diffs foram aplicados como patches Git textuais, sem staging e sem ampliação de escopo.
7. Um patch documental amplo não encontrou o contexto completo e adicionou zero alterações. A atualização foi dividida em hunks menores e revisada em UTF-8.
8. A primeira adição extensa ao contrato terminou no cabeçalho `Uso proibido` por contagem incorreta do hunk. A revisão do diff detectou a truncagem e as regras proibidas e o gate foram completados em patch separado.

## Revisão humana

Foram revisados tipos e volumes de evento, provenance, flags fatais e warnings, duplicatas, churn recorrente, reativação, atribuição a assinatura, episódios abertos/sobrepostos, reconciliação por fonte, período temporal, schemas Parquet, hashes, ausência de texto livre e tamanho dos outputs.

## Limitações e gate

A cobertura ativa é reduzida pela quarentena material de uso e suporte. Datas diárias não permitem ordem intradiária causal. Atribuição de churn é majoritariamente ambígua devido a assinaturas sobrepostas. A estabilidade longitudinal dos IDs e a disponibilidade as-of de atributos mutáveis não são provadas pelo snapshot.

**Gate da Fase 3:** `PASS_WITH_WARNINGS`. O log é auditável e reconciliado, mas diagnósticos devem excluir quarentena, respeitar warnings e declarar cutoffs.

Não foram executados diagnóstico, análise de receita, survival, journey mining, grafo, watchlist, modelo, dashboard, push ou Pull Request.

---

## Fase 3 — diagnóstico executivo governado

### Gate e fontes

1. Reexecutados `pwd`, raiz Git, branch, status, diffs, staging e log.
2. Confirmados branch `submission/carlos-henrique`, HEAD `75be8ef0663f0f49b425092735ffe0a3c6ed65f6`, working tree limpo e staging vazio.
3. Confirmados zero CSVs brutos versionados.
4. Recalculados hashes dos cinco CSVs e dos outputs registrados no manifesto da Fase 2; todos coincidiram.
5. Lidos `event_log.parquet` (13.927), `quarantined_events.parquet` (21.659) e `subscription_episodes.parquet` (5.000); reconciliação inexplicada permaneceu zero.

### Execução

1. Construídas features main e strict com cutoff no primeiro churn ou `observation_end`.
2. Mantidos grãos separados de conta, episódio e evento; nenhum mega-join foi materializado.
3. Consultado `resolution_time_hours` no CSV de suporte somente para fechamentos utilizáveis, por lookup único e read-only.
4. Gerados Data Health, churn, reativação, uso, suporte, receita associada, coortes, jornadas agregadas e sensibilidade.
5. Findings passaram por gate de evidência e exclusão automática de status `UNSTABLE`.
6. Segmentos de atenção foram persistidos apenas no agregado, sem IDs de conta.

### Erros reais e correções

- **E031 — fixture incompleto:** o primeiro teste novo falhou porque o fixture de episódios omitia `subscription_id`. O fixture foi corrigido para refletir o contrato; 13/13 testes novos passaram na repetição.
- **E032 — cache do pytest no sandbox:** uma execução ficou bloqueada ao criar cache temporário. Foi encerrada e repetida com o cache provider desabilitado para a validação intermediária.
- **E033 — timeout de agregação:** duas execuções do pipeline excederam 120/180 segundos por filtros globais repetidos e reconstrução redundante de episódios estritos. Eventos e episódios foram pré-agrupados, strings Arrow foram convertidas em memória para slicing eficiente, e a tabela de episódios estrita desnecessária foi removida. A execução seguinte concluiu em 102,8 segundos.
- **E034 — revisão semântica:** a primeira versão pareava uma reativação futura com mais de um churn e estimava tickets abertos por diferença bruta de contagens. O pareamento passou a usar o churn imediatamente anterior e tickets abertos passaram a usar diferença de IDs.

### Revisão humana antes do commit

- população principal, estrita e quarentena separadas;
- cutoffs e janelas auditados contra eventos reais;
- episódios abertos preservados e censurados;
- MRR tratado como associado;
- `SMALL_SAMPLE` aplicado abaixo de 20;
- jornadas limitadas, agregadas e sem mineração formal;
- findings instáveis excluídos;
- linguagem, PII, texto livre e caminhos absolutos verificados;
- tamanhos dos três Parquets revisados;
- CSVs brutos imutáveis, não versionados e fora do staging.

### Validação final da Fase 3

- pytest: 57 testes aprovados, zero warnings;
- compileall: src e scripts aprovados;
- pipeline: duas execuções finais completas;
- idempotência: 18 arquivos comparados, zero divergências SHA-256;
- grãos: 500/500 contas únicas e 5.000/5.000 episódios únicos;
- privacidade: zero IDs operacionais nos JSONs/relatórios, zero emails e zero caminhos absolutos;
- linguagem: zero ocorrências das alegações explicativas proibidas;
- reconciliação: diferença inexplicada zero;
- dados brutos: cinco hashes intactos e zero CSVs versionados;
- escopo: somente submissions/carlos-henrique/ elegível para staging;
- gate: PASS_WITH_WARNINGS por cobertura de 39,1362%, sobreposição de 99,84% e outcomes sensíveis a warnings.

---

## Fase 4 ? survival analysis governada

### Gate e execu??o

1. Reexecutados `pwd`, raiz Git, branch, status, diffs, staging e log; confirmado HEAD `dd1f013cc502d9e690a1790331397897729edfd3`.
2. Confirmados 500 registros e 500 IDs ?nicos na tabela anal?tica, Parquets leg?veis, hashes do event log/epis?dios compat?veis e zero CSVs brutos versionados.
3. Instalados somente no `.venv` local: PyArrow 25.0.0, SciPy 1.18.0 e Matplotlib 3.11.1; ambiente global e requirements permaneceram inalterados.
4. Constru?do o dataset principal com 500 contas eleg?veis; a popula??o estrita teve 497 eleg?veis e tr?s exclus?es por aus?ncia de assinatura inicial `VALID`.
5. Fixados primeiro churn como endpoint e `2024-12-31T19:00:00` como censura administrativa.
6. Geradas Kaplan?Meier, Nelson?Aalen, RMST, dez compara??es log-rank eleg?veis com BH e seis cen?rios de sensibilidade.
7. Gerados landmarks 30/60/90 com features exclusivamente anteriores ou iguais ao marco e reconcilia??o integral de exclus?es.
8. Cox e curvas por assinatura foram formalmente n?o executados; n?o houve score, predi??o, causalidade, grafo, sequence mining ou dashboard.
9. Produzidos quatro Parquets, oito JSONs agregados, quatro relat?rios e seis PNGs.

### Erros reais e corre??es

- **E041 ? depend?ncias locais ausentes:** PyArrow, SciPy e Matplotlib n?o estavam dispon?veis. A instala??o foi restrita ao `.venv`, com vers?es registradas.
- **E042 ? timeout ap?s instala??o:** o comando de pip excedeu o timeout, mas a verifica??o posterior confirmou instala??o completa. Nenhuma segunda instala??o foi feita.
- **E043 ? cache de fontes fora da writable root:** o primeiro pipeline gerou outputs, mas Matplotlib tentou gravar no AppData e excedeu o timeout. `MPLCONFIGDIR` foi redirecionado para `.venv/.matplotlib`.
- **E044 ? custo de slicing temporal:** tr?s popula??es/origens e tr?s landmarks demoraram mais de 100 segundos. Strings Arrow foram convertidas em mem?ria para objetos antes dos slices; a execu??o caiu para aproximadamente 78 segundos sem mudar a regra temporal.
- **E045 ? fixture de mediana incorreto:** o teste `NOT_REACHED` continha evento quando restava uma conta em risco e corretamente levava KM a zero. O fixture passou a ter censura completa.
- **E046 ? diret?rio tempor?rio do pytest bloqueado:** AppData e `C:/tmp` n?o eram grav?veis pelo subprocesso Python no sandbox. O teste idempotente passou a usar arquivo transit?rio dentro do `.venv` ignorado.
- **E047 ? fixtures legados fora do sandbox:** duas su?tes antigas ainda dependiam de `tmp_path` no AppData. A execu??o completa foi repetida fora do sandbox apenas para os tempor?rios e aprovou 76/76 testes; nenhum arquivo versionado foi alterado pela escalada.

### Valida??o e revis?o humana

- testes novos: 19 aprovados;
- pytest completo: 76 aprovados em 3,92 segundos;
- pipeline final: duas execu??es completas consecutivas;
- idempot?ncia: 22 outputs, zero diverg?ncias SHA-256;
- conta: 500/500 IDs ?nicos; zero dura??o negativa eleg?vel;
- endpoint: 325 eventos e 175 censuras na principal; 46 eventos e 451 censuras na estrita;
- quarentena utilizada: zero;
- future features detectadas: zero;
- PII/IDs em JSONs, relat?rios ou figuras: zero;
- reconcilia??o inexplicada: zero;
- findings principais: dois, nenhum `UNSTABLE`;
- assinatura: an?lise n?o executada devido a 99,84% de overlap e depend?ncia;
- Cox: n?o executado por sensibilidade dos endpoints e proporcionalidade n?o testada;
- gr?ficos: seis PNGs revisados quanto a t?tulo, eixos, intervalos, suporte, cores, IDs e PII.

### Gate

`PASS_WITH_WARNINGS`. As curvas de conta s?o reproduz?veis e metodologicamente governadas, mas a diferen?a entre popula??es principal e estrita, a censura e os pressupostos impedem `PASS` pleno e qualquer uso individual ou causal.

---

## Fase 5 ? Journey mining e padr?es sequenciais

1. Gate Git e hashes das Fases 2?4 validados; event log ativo com 500 contas e zero quarentena anal?tica.
2. Depend?ncias locais verificadas; `prefixspan` ausente e substitu?do por implementa??o pr?pria simples e testada, sem instala??o.
3. Jornadas principal e estrita constru?das nos oito escopos com ordena??o est?vel, colapso consecutivo e buckets di?rios estruturados.
4. Transi??es e n-grams calculados antes da minera??o; suporte contabilizado por conta e denominadores preservados.
5. Enumera??o de subsequ?ncias executada com gaps de eventos/dias e pruning de padr?es fechados.
6. Pr?-churn comparado em janelas fixas contra pseudo-cutoff em `observation_end`; recorr?ncia e reativa??o descritas somente por eventos expl?citos.
7. Taxonomia determin?stica classificada em Parquet; agregados n?o exp?em IDs.
8. Sensibilidade principal/estrita reconciliada; padr?es HIGH, UNSTABLE ou pequenos bloqueados em findings.
9. Dez JSONs, quatro relat?rios e seis figuras gerados; nenhum grafo constru?do.

### Erros e corre??es

- A enumera??o inicial de subsequ?ncias excedeu a janela operacional de observa??o. A execu??o foi interrompida de forma segura; a busca passou a expandir apenas ?ndices dentro do gap configurado, preservando os mesmos par?metros.
- `matplotlib` reportou limita??o de `tight_layout` no gr?fico de padr?es pr?-churn; o arquivo foi salvo com bounding box expl?cito e ser? revisado visualmente.

### Revis?o humana

Escopos, limites, ordena??o, exposi??o, transi??es, n-grams, pruning, churn, recorr?ncia, reativa??o, estabilidade, taxonomia, findings, figuras, causalidade, PII e diff foram inclu?dos no checklist. O gate permanece `PASS_WITH_WARNINGS` por warnings e sensibilidade material.

---

## Fase 6 ? JourneyGraph governado

1. Gate Git, commit-base e hashes das Fases 2?5 validados; working tree e staging inicialmente limpos.
2. NetworkX verificado e instalado exclusivamente no `.venv` local.
3. Schema com dez labels, rela??es autorizadas, propriedades e sem?ntica proibida definido.
4. Chaves p?blicas an?nimas e determin?sticas constru?das com SHA-256 truncado e namespace documentado.
5. `INSTANCE_GRAPH` constru?do com 500 contas, 4.221 jornadas, 43.398 ocorr?ncias e ordem temporal por escopo.
6. Padr?es de n-gram, sequ?ncia fechada e pr?-churn normalizados; identidade preserva tipo, janela, escopo, outcome e popula??o.
7. `ANALYTICAL_GRAPH` constru?do somente com padr?es e transi??es ROBUST/SENSITIVE, suportados, n?o HIGH e n?o pequenos.
8. Seis subgrafos governados, m?tricas estruturais, sensibilidade de pesos, caminhos m?ximos de seis eventos e dez consultas executados.
9. Contas, jornadas, taxonomia, padr?es, transi??es, findings e MRR reconciliados com diferen?a inexplicada zero.
10. Dois GraphML completos, pacote Neo4j port?til, dez JSONs, cinco relat?rios e seis figuras gerados.
11. Gates de schema, duplica??o, temporalidade, promo??o, causalidade, PII, GraphML e escopo executados.
12. Pytest, compileall, dupla execu??o e compara??o SHA-256 integram o gate final.

### Revis?o orientada a decis?o

- O relat?rio abre com resultado executivo, escala do grafo e condi??es de uso.
- Toda m?trica preserva denominador, popula??o, peso e limita??o.
- Centralidade ? descrita como estrutura, nunca como import?ncia causal.
- MRR ? associado e reconciliado, nunca chamado de perda, economia ou receita evit?vel.
- Neo4j permanece opcional e n?o executado externamente.

### Valida??o e revis?o humana

- labels, rela??es, identificadores, anonimiza??o, temporalidade e qualidade revisados;
- padr?es, outcomes, taxonomia, centralidade, caminhos, MRR e consultas revisados;
- subgrafos, GraphML, CSVs derivados, Cypher, relat?rios e figuras revisados;
- PII, causalidade, IDs operacionais, ranking individual e escopo revisados;
- staging seletivo e diff final revisados antes do commit.

### Gate

`PASS_WITH_WARNINGS`. O JourneyGraph est? reconciliado e apto a alimentar uma watchlist governada somente com os gates de qualidade, estabilidade, suporte, sem?ntica n?o causal e revis?o humana preservados. Reativa??o anal?tica limitada, warnings herdados, CSV amostrado e aus?ncia de execu??o Neo4j externa impedem PASS pleno.

### Resultado final da validacao da Fase 6

- testes novos: 15 aprovados;
- pytest completo: 104 aprovados em 5,62 segundos na repeticao final;
- compileall de src e scripts: aprovado;
- pipeline final: duas execucoes completas consecutivas apos a ultima alteracao;
- idempotencia: 49 outputs, zero divergencias SHA-256;
- instance graph: 48.593 nos e 217.715 relacoes;
- analytical graph: 488 nos e 1.821 relacoes;
- promocao: 435 patterns e 43 transitions;
- reconciliacao inexplicada: zero;
- IDs operacionais, PII, quarentena, ranking individual e semantica causal: zero;
- Neo4j: 26 arquivos derivados; EventInstance amostrado por 250 jornadas; execucao externa nao realizada;
- figuras: seis PNGs revisados; o painel de reativacao passou a declarar explicitamente a ausencia de caminho promovido.

## Fase 7 ? Intervention Watchlist

1. Reexecutadas precondi??es Git, presen?a e hashes dos onze inputs; base `1c31ae2` limpa.
2. Perfilados 500 accounts, 13.927 eventos, popula??es MAIN/STRICT e cutoff `2024-12-31T19:00:00`.
3. Criadas 16 regras determin?sticas para sete filas, com quality-first e limites de volume.
4. Constru?das features retrospectivas, quatro componentes discretos e matriz expl?cita P1?P4.
5. Integrado somente JourneyGraph promov?vel, excluindo UNSTABLE, HIGH e small sample.
6. Gerados watchlist detalhada, resumo por conta, evidence packets, dez JSONs, cinco relat?rios e seis figuras.
7. Executadas valida??es de leakage, PII, temporalidade, causalidade, probabilidade, interven??o, MRR e reconcilia??o.
8. Pipeline executado duas vezes e hashes comparados; su?te completa e compileall executados antes do commit.

### Revis?o humana

Regras, cutoff, janelas, qualidade, componentes, filas, duplicidade, evid?ncias, linguagem, grafo, MRR, figuras, PII, reconcilia??o e diff staged foram inclu?dos no checklist final. W011 ? exce??o ampla exclusiva de qualidade; W015 permanece `BROAD_RULE_REVIEW_REQUIRED`. Nenhum item autoriza contato ou interven??o.

- **E053 - painel de reativacao vazio:** nenhum pattern de reativacao atingiu os gates e a primeira figura mostrava apenas o titulo. O painel passou a comunicar a ausencia de resultado e os gates preservados, sem criar evidencia artificial.

## Fase 8 ? Experiment Lab

1. Reexecutadas precondi??es Git e conferidos os hashes dos dez inputs autorizados sobre a base `1ed6655` limpa.
2. Criados cat?logo com dez interven??es e registro de oito hip?teses futuras, todas `UNTESTED`.
3. Aplicadas regras de elegibilidade cutoff-safe, conflitos futuros e bloqueios de qualidade ou unidade de randomiza??o ausente.
4. Calculados baselines hist?ricos, MDEs e power para propor??es, m?dias e tempo at? evento, com infla??o por atrito.
5. Simulada aloca??o determin?stica e bloqueada, estritamente marcada como `simulation_only` e sem outcomes.
6. Especificados ITT, guardrails, stopping rules, missingness, multiplicidade, heterogeneidade e an?lises de sensibilidade.
7. Gerados tr?s Parquets, onze JSONs agregados, oito especifica??es, seis relat?rios e seis figuras.
8. Validada a aus?ncia de IDs brutos, PII, futuro, resultados, uplift, execu??o e sem?ntica causal.

### Gate

`PASS_WITH_WARNINGS`. EXP003 e EXP007 n?o s?o vi?veis sem chaves operacionais; EXP001, EXP002, EXP004 e EXP008 est?o subdimensionados; EXP005 permanece piloto; EXP006 est? pronto somente para revis?o. Nenhum status autoriza execu??o.

### Erros e corre??es

- **E058 ? depend?ncia estat?stica opcional ausente:** `statsmodels` n?o estava instalada; f?rmulas transparentes com SciPy foram usadas sem ampliar depend?ncias.
- **E059 ? serializa??o de se??es em lista:** o normalizador de especifica??es passou a aceitar dicion?rios e listas sem perder itens.
- **E060 ? power para popula??o vazia:** desenhos sem popula??o eleg?vel passaram a retornar amostra n?o estim?vel como zero e status `NOT_FEASIBLE`.

### Resultado final da valida??o da Fase 8

- testes novos: 8 aprovados;
- pytest completo: 119 aprovados em 11,92 segundos na execu??o final fora do sandbox, com `--basetemp` isolado;
- compileall de `src` e `scripts`: aprovado;
- pipeline final: duas execu??es completas consecutivas ap?s a ?ltima altera??o de c?digo;
- idempot?ncia: 34 outputs, zero diverg?ncias SHA-256;
- registry: 8 experimentos e status causal `UNTESTED` em todos;
- assignment: 1.155 linhas candidatas, 654 eleg?veis e `simulation_only=true` em todas;
- invent?rio: 3 Parquets, 11 JSONs agregados, 8 especifica??es, 6 relat?rios e 6 figuras;
- leakage temporal, PII, execu??o, contatos, resultados, uplift e outcomes sint?ticos: zero;
- reconcilia??o inexplicada: zero;
- revis?o visual: seis PNGs inspecionados em montage; t?tulos, denominadores, escalas e aus?ncia de identificadores aprovados;
- revis?o humana: hip?teses, interven??es, linguagem, elegibilidade, exclus?es, randomiza??o, contamina??o, m?tricas, MDE, amostra, atrito, baselines, balanceamento, SAP, guardrails, stopping rules, ?tica, PII, causalidade, figuras, reconcilia??o e diff inclu?dos no checklist.
