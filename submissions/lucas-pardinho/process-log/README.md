# Process log — G4 Focus

## Como ler este registro

Este é um relato curado e verificável do trabalho feito com IA. Não é um chat reescrito como se fosse transcrição, e não atribui à IA decisões que dependeram de julgamento humano. Quando uma etapa ainda depende da integração final, isso aparece como pendência, e não como sucesso presumido.

- **Responsável:** Lucas dos Santos Pardinho
- **Challenge:** 003 — Lead Scorer
- **Ferramenta principal de IA:** Codex
- **Formato de evidência escolhido:** narrativa escrita + artefatos executáveis + histórico Git/PR
- **Iterações de produto documentadas:** 6 macro-iterações; não foi usado um prompt único

## Decomposição antes de construir

O pedido da Head de RevOps foi traduzido em cinco perguntas, nesta ordem:

1. **Decisão:** qual ação o vendedor precisa tomar ao abrir a ferramenta?
2. **Evidência:** quais campos existiam antes do resultado e podem sustentar a recomendação?
3. **Risco:** onde o estado final do CRM pode vazar o futuro para o score?
4. **Produto:** como transformar um ranking em uma fila de trabalho compreensível?
5. **Operação:** como outra pessoa reproduz, testa e publica a solução?

Esse recorte evitou começar por framework ou por um algoritmo sofisticado sem contrato de uso.

## As seis macro-iterações

### 1. Brief, regras e entrega

**Uso da IA:** localizar requisitos obrigatórios, template, estrutura de pasta e regras do Pull Request.

**Julgamento humano:** escolher uma aplicação web executiva e operacional, em vez de limitar a entrega a notebook ou relatório.

**Verificação:** leitura direta de `challenges/build-003-lead-scorer/README.md`, `submission-guide.md`, `CONTRIBUTING.md` e do template oficial.

### 2. Integridade e perfil dos dados

**Uso da IA:** criar checks reproduzíveis de schema, chaves, ausências, datas, contagens e hashes.

**Fatos confirmados:**

- ZIP SHA-256 `74d535826330b616758ebb6bb393abf701a5126364a72fbe71003cb6a7a87a9c`;
- 8.800 oportunidades e 2.089 abertas;
- 1.425 contas ausentes;
- 500 datas de engajamento ausentes, todas em `Prospecting`;
- 2.089 datas e valores de fechamento ausentes, referentes ao pipeline aberto;
- todos os vendedores relacionam com a tabela de equipes;
- `GTXPro` versus `GTX Pro` quebrava 1.480 relacionamentos de produto.

**Correção:** os brutos foram preservados e o alias de produto passou a ser normalizado no pipeline, com relatório de qualidade.

### 3. Teste de viabilidade preditiva

**Uso da IA:** formular baselines e testar se os sinais estáticos realmente separavam ganhos e perdas fora do período de treino.

**Teste de realidade:** fechamentos anteriores a 2017-10-01 foram usados como referência (n=4.726; 64,37% `Won`) e o Q4 como holdout temporal (n=1.985; 60,25% `Won`). Produto, setor, região e porte ficaram em AUC ~0,489 e Brier pior que o baseline. Adicionar agente levou a AUC apenas a ~0,518.

**Onde a IA errou / direção rejeitada:** uma formulação inicial podia ser apresentada como “probabilidade de fechamento”. As métricas não sustentaram isso. Em uma iteração posterior, o código ainda atribuía 1% fixo a todo deal acima de 138 dias e treinava snapshots apenas com oportunidades já encerradas. A revisão removeu a constante arbitrária e incluiu oportunidades `Engaging` somente nas janelas de 60 dias completamente observáveis. O produto permaneceu uma priorização operacional; probabilidade conservadora, frescor e prioridade ficaram conceitualmente separados.

### 4. Score, filas e proteções

**Uso da IA:** comparar alternativas de regras, regularização, explicações e cortes de fila.

**Julgamento humano:**

- conversão é o eixo principal (65%), sem apagar acionabilidade/frescor (20%) e valor (15%);
- agente é dimensão de filtro/monitoramento, não atalho do score principal;
- `Prospecting` recebe qualificação separada;
- conta ausente reduz confiança, mas não elimina a oportunidade;
- cada linha precisa explicar o score e indicar a próxima ação.

**Saída:** cinco filas: **Foco agora**, **Acelerar**, **Nutrir**, **Resgatar ou desqualificar** e **Qualificar**.

### 5. Produto e implementação paralela

**Uso da IA:** dividir a construção em frentes com permissões de arquivo exclusivas: pipeline/artefatos, web/API e Docker/documentação.

**Julgamento humano:** manter os contratos JSON como fronteira entre as frentes, preservar escopo de cada agente e reservar integração/testes ao fluxo principal. Isso reduziu colisões e evitou que a interface reinventasse o score.

**Resultado obtido:** dashboard executivo, pipeline filtrável, carteira por vendedor, metodologia transparente, cinco rotas de API read-only e imagem Docker reproduzível.

### 6. Integração, validação e entrega

**Uso da IA:** executar testes automatizados, build de produção, health check e auditoria do diff; investigar falhas concretas antes de declarar conclusão.

**Critério de conclusão:** pipeline, testes, build, container, API e interface precisam de evidência separada. Um arquivo criado ou um processo iniciado não conta, sozinho, como validação.

Durante a integração, as frentes paralelas atingiram o limite de uso da ferramenta. O fluxo principal retomou os arquivos incompletos, revisou os contratos e executou todas as validações localmente.

Dois erros só apareceram em runtime:

- o navegador detectou hidratação divergente em valores monetários (`US$ 5 mi` no cliente versus `US$ 5,0 mi` no servidor); a formatação passou a ser determinística e o novo teste no container não registrou erros;
- o Buildx local não conseguia escrever em um diretório antigo pertencente a `root`; a imagem foi construída com configuração Docker temporária em `/tmp`, sem alterar permissões globais da máquina.

## Decision log

| ID | Decisão | Evidência / motivo | Alternativa rejeitada |
|---|---|---|---|
| D-01 | Produto web chamado G4 Focus | O brief pede software que o vendedor consiga abrir e usar. | Notebook como entrega principal. |
| D-02 | Prioridade, não promessa preditiva | Holdout temporal mostrou baixo poder dos sinais estáticos. | Rotular o score como “IA que prevê fechamento”. |
| D-03 | Separar probabilidade, frescor e prioridade | Cada conceito responde a uma pergunta diferente e precisa ser explicável. | Um número opaco misturando tudo. |
| D-04 | Tirar agente do score principal | Ganho marginal de AUC e risco de reforçar diferenças históricas. | Premiar/punir uma oportunidade pelo vendedor atual. |
| D-05 | Separar `Prospecting` | Não existe `engage_date` para os 500 prospects. | Inventar idade zero ou misturar os rankings. |
| D-06 | Tratar staleness como ação distinta | Deals antigos precisam de resgate/limpeza, não destaque permanente. | Ordenar sempre por valor ou taxa histórica. |
| D-07 | Artefatos JSON e app read-only | Reproduzível, simples de auditar e suficiente para o challenge. | Banco, autenticação e scheduler dentro do timebox. |
| D-08 | Docker + Railway via GitHub | Reduz setup e oferece demo publicável com deploy automático. | Depender apenas do ambiente local. |

## O que a IA não decidiu sozinha

- A promessa do produto e o cuidado de não vender sinal fraco como previsão forte.
- A separação entre limpeza de pipeline e priorização de oportunidade.
- O limite ético de não usar o vendedor como profecia autorrealizável.
- A escolha de otimizar uma fila que cabe no dia de trabalho, e não apenas uma métrica offline.
- A regra de que cada afirmação de funcionamento precisa de teste correspondente.

## Matriz de evidências de fechamento

| Evidência | Comando ou artefato | Status neste registro |
|---|---|---|
| Integridade dos dados | `generated/data-quality.json` | passou; 0 erros e 2 warnings explícitos |
| Metodologia executada | `generated/model-report.json` | passou; 81.634 snapshots e holdout temporal de 1.575 observações |
| Testes do pipeline | `python3 -m unittest discover -s analytics/tests -v` | 10/10 passaram |
| Build web | `npm run check` | passou com Next.js 16.3.4 |
| Testes web/API | Vitest em `web/lib/analytics.test.ts` | 5/5 passaram |
| Imagem e usuário não-root | `docker build` + `docker exec ... id` | passou; `nextjs`, UID/GID 1001 |
| Health local | `GET /api/health` no container | HTTP 200; fonte `generated`, 4/4 arquivos |
| UI local | navegador em desktop e 390 px | quatro telas inspecionadas; filtros funcionais e console limpo após correção |
| Deploy Railway | URL pública + `GET /api/health` | não alegado antes do deploy real |
| Rastreabilidade | histórico Git e Pull Request | pendente de commit, push e abertura do PR |

## Evidências não anexadas

Screenshots de conversa, screen recording e chat export não foram incluídos nesta pasta. O guia aceita narrativa escrita e histórico Git; esses são os formatos escolhidos. Se qualquer evidência visual for adicionada depois, ela deve ser real, datada e referenciada aqui — nunca um placeholder apresentado como prova.
