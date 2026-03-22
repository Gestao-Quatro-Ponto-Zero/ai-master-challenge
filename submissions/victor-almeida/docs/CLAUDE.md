# CLAUDE.md — AI Master Challenge: Lead Scorer (Challenge 003)

## Projeto

Submissão do Victor Almeida para o processo seletivo de **AI Master** do G4 Educação.
Challenge escolhido: **003 — Lead Scorer** (Vendas / RevOps).

## Objetivo

Construir uma **ferramenta funcional** que um vendedor abra, veja o pipeline, e saiba onde focar.
Não é documento, não é mockup — é software rodando.

## Contexto do problema

- 35 vendedores, ~8.800 oportunidades no pipeline
- Hoje a priorização é "no feeling" — vendedores decidem por intuição
- A Head de RevOps quer algo **simples e funcional**, não ML perfeito
- O vendedor precisa entender **por que** um deal tem score alto ou baixo (explainability)

## Dados

Dataset: CRM Sales Predictive Analytics (Kaggle, licença CC0)

| Arquivo | Conteúdo |
|---------|----------|
| `accounts.csv` | ~85 contas (setor, receita, funcionários, localização) |
| `products.csv` | 7 produtos (série, preço) |
| `sales_teams.csv` | 35 vendedores (manager, escritório regional) |
| `sales_pipeline.csv` | ~8.800 oportunidades (stage, datas, vendedor, produto, conta, valor) |
| `metadata.csv` | Metadados do dataset |

Relações: `sales_pipeline` é a tabela central, liga accounts, products e sales_teams.

### Localização dos dados

- **Fonte original:** `kaggle/` (raiz do repositório) — contém os CSVs brutos do Kaggle
- **Cópia na solução:** `submissions/victor-almeida/solution/data/` — CSVs copiados para uso direto pela aplicação

A aplicação carrega os dados de `solution/data/`. Se novos arquivos forem adicionados ao `kaggle/`, copiar para `solution/data/`.

## Estrutura da submissão

Tudo dentro de `submissions/victor-almeida/`:

```
submissions/victor-almeida/
├── README.md              ← Baseado no template de submissão
├── solution/              ← Código da aplicação
├── process-log/           ← Evidências de uso de IA
│   ├── screenshots/
│   └── chat-exports/
└── docs/                  ← Documentação adicional
```

## Regras críticas

- **Só modificar arquivos dentro de `submissions/victor-almeida/`** — PRs que alteram outros arquivos são rejeitados
- Process log é **obrigatório** — sem evidência de processo = desclassificado
- A solução precisa **rodar** seguindo as instruções de setup
- Precisa usar os **dados reais** do dataset
- Lógica de scoring/priorização precisa ir além de ordenar por valor
- Branch: `submission/victor-almeida`
- PR title: `[Submission] Victor Almeida — Challenge 003`

## Critérios de qualidade

1. Funciona de verdade? Roda seguindo instruções?
2. Scoring faz sentido? Usa features certas? Vai além do óbvio?
3. Vendedor não-técnico consegue usar e entender?
4. Interface ajuda a tomar decisão (não só mostra dados)?
5. Código limpo para manutenção

## Stack técnica

- **Backend/Frontend:** Python + Streamlit
- **Dados:** Pandas
- **Visualização:** Plotly (integrado ao Streamlit)
- **Dados:** CSVs carregados localmente

## Arquitetura da solução

```
submissions/victor-almeida/solution/
├── app.py                 ← Entrada principal do Streamlit
├── requirements.txt
├── data/                  ← CSVs do dataset
├── scoring/               ← Lógica de scoring (engine, velocity, seller_fit, account_health)
├── components/            ← Componentes de UI (pipeline_view, deal_detail, filters, metrics)
└── utils/                 ← Utilidades (data_loader, formatters)
```

## Algoritmo de scoring (resumo)

```
SCORE (0-100) = Stage(35%) + Valor Esperado(25%) + Velocidade(15%) + Seller-Fit(10%) + Saúde Conta(15%)
```

- **Stage:** Prospecting=15, Engaging=90
- **Valor Esperado:** log-scaled do close_value (proxy: preço produto se Prospecting)
- **Velocidade:** decay exponencial baseado em tempo no stage vs P75 dos Won (88 dias para Engaging)
- **Seller-Deal Fit:** win rate do vendedor no setor vs média do time (threshold: ≥5 deals)
- **Saúde da Conta:** win rate histórica da conta (threshold: ≥3 deals fechados)
- **Flags:** Deal Zumbi (tempo > 2× referência), Conta Recorrente Lost (2+ losses)

Detalhes completos no `PRD.md`.

## Peculiaridades dos dados

- **Prospecting:** sem engage_date, close_date, close_value (tudo null)
- **Engaging:** tem engage_date, sem close_date/close_value
- **Won:** close_value = valor real | **Lost:** close_value = 0
- **Data de referência:** `2017-12-31` (última data do dataset — usar como "hoje")
- **Revenue** das contas em milhões de USD
- Diferença de valor entre produtos: **486x** (GTK 500 vs MG Special)

## Diretrizes técnicas

- Preferir soluções simples e funcionais (scoring baseado em regras + heurísticas > ML sem interface)
- Explainability é essencial — mostrar POR QUE cada deal tem o score que tem
- Pensar no uso real: vendedor abre segunda-feira de manhã, o que precisa ver?
- Filtros por vendedor/manager/região agregam muito valor
- Comunicação em **português (PT-BR)**

## TDD — Test-Driven Development (OBRIGATÓRIO)

**Toda task DEVE seguir o fluxo TDD rigoroso:**

1. **Escrever o teste ANTES do código** — o teste define o comportamento esperado
2. **Rodar o teste e ver ele FALHAR** (Red) — confirma que o teste é real
3. **Implementar o código mínimo** para fazer o teste passar (Green)
4. **Refatorar** se necessário, mantendo os testes passando (Refactor)
5. **Só considerar a task concluída quando TODOS os testes passam genuinamente**

### Regras invioláveis

- **NUNCA burlar testes** — não alterar assertions para forçar pass, não skipar testes, não mockar o que deveria ser testado de verdade
- **NUNCA fingir que testes passaram** — sempre rodar `pytest` de verdade e mostrar o output real
- **NUNCA manipular o terminal** para esconder falhas — sem `|| true`, sem `2>/dev/null` em testes, sem grep seletivo no output
- **NUNCA comentar ou remover testes** que estão falhando para "resolver" o problema — corrigir o código, não o teste
- **NUNCA usar `assert True`** ou assertions triviais que sempre passam — cada assertion deve verificar comportamento real
- **Testes devem testar lógica real** — dados de entrada → processamento → resultado esperado verificável
- **Cada spec tem seus próprios critérios de teste** — consultar a seção "Testes TDD" da spec correspondente antes de implementar

### Estrutura de testes

```
submissions/victor-almeida/solution/
├── tests/
│   ├── __init__.py
│   ├── test_data_loader.py      ← Testes do data_model.md
│   ├── test_scoring_engine.py   ← Testes do scoring_engine.md
│   ├── test_deal_zombie.py      ← Testes do deal_zombie.md
│   ├── test_nba.py              ← Testes do next_best_action.md
│   ├── test_filters.py          ← Testes do filters.md
│   ├── test_metrics.py          ← Testes do metrics_summary.md
│   ├── test_pipeline_view.py    ← Testes do pipeline_view.md
│   └── test_formatters.py       ← Testes de utils/formatters.py
```

### Comando para rodar testes

```bash
cd submissions/victor-almeida/solution && python -m pytest tests/ -v
```

## Como se diferenciar

O avaliador vai ver várias submissões. As fracas são previsíveis:

**Anti-padrões a evitar (submissão fraca):**
- Output genérico que poderia ser sobre qualquer empresa
- Zero verificação (IA disse, candidato acreditou)
- Process log mostra 1 prompt → 1 resposta → submissão
- Foco em parecer inteligente em vez de resolver o problema
- Documento de 40 páginas onde 5 resolveriam

**O que nos diferencia (submissão forte):**
- Mostrar que **entendeu o problema antes de construir** — a análise do INSTRUCTIONS.md com perguntas de refinamento (EV, velocity, seller-fit, NBA, deal zumbi) evidencia pensamento estratégico
- IA usada **estrategicamente** — decomposição do problema em 5 componentes, calibração com dados reais, iteração
- Output **acionável** — não é dashboard passivo, é ferramenta com Next Best Action que diz ao vendedor o que fazer
- **Achados contra-intuitivos** dos dados (deals 90-150 dias têm WR mais alta, pipeline massivamente inflado) mostram que analisamos antes de construir
- Scoring com **5 componentes calibrados** vs a maioria que vai fazer ordenação por valor ou ML genérico

## Process log — o que capturar

O process log é **obrigatório** e diferenciador. Sem ele = desclassificado.

**O que o avaliador quer ver:**
1. Quais ferramentas de IA usou e por quê
2. Como decompôs o problema **antes** de promptar
3. Onde a IA errou e como corrigiu
4. O que adicionou que a IA sozinha não faria
5. Quantas iterações foram necessárias

**Formatos aceitos:** screenshots, screen recording, chat export, narrativa escrita, git history, notebook comentado.

**Evidenciar especificamente:**
- A conversa de refinamento (5 perguntas estratégicas antes de codar)
- Calibração do scoring com dados reais (não aceitamos defaults)
- Decisões de design com justificativa (por que Streamlit, por que regras vs ML)
- Iterações na UI pensando no vendedor não-técnico

## README da submissão (template obrigatório)

O `submissions/victor-almeida/README.md` deve seguir o template (`templates/submission-template.md`):

1. **Sobre mim** — Nome, LinkedIn, challenge escolhido
2. **Executive Summary** — 3-5 frases: o que fez, o que encontrou, principal recomendação
3. **Solução** — Abordagem, Resultados, Recomendações, Limitações
4. **Process Log** — Ferramentas usadas, workflow passo a passo, onde IA errou, o que adicionei
5. **Evidências** — Screenshots, chat exports, git history

## Checklist pré-PR

- [ ] Solução está em `submissions/victor-almeida/`
- [ ] Process log com evidências de uso de IA
- [ ] README segue o template
- [ ] Instruções de setup funcionam (testar do zero)
- [ ] Nenhum arquivo modificado fora da pasta
- [ ] Branch: `submission/victor-almeida`
- [ ] PR title: `[Submission] Victor Almeida — Challenge 003`
- [ ] Um PR único (atualizar via push na mesma branch)

## Comandos úteis

```bash
# Rodar a aplicação
cd submissions/victor-almeida/solution && pip install -r requirements.txt && streamlit run app.py
```
