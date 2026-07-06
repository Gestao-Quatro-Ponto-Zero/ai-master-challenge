# HARNESS — Gabriel's AI Master Operating System

> **The harness-native operator system for agentic work.**
> Built from real-world multi-harness engineering workflows.
>
> Not just configs. A complete system: skills, instincts, memory optimization,
> continuous learning, security scanning, and research-first development.
> Production-ready agents, skills, hooks, rules, MCP configurations, and legacy
> command shims evolved over intensive daily use building real products.

**Operador:** Gabriel
**Contexto de uso:** AI Master Challenge — Challenge 003: Lead Scorer
**Modelo de IA:** GLM-5.2 (via GitHub Copilot)
**Data:** 06 de Julho de 2026

---

## 0. Como ler este documento

Este `.md` é o **harness** que governa como Gabriel opera com IA. Ele não é teoria — é o sistema efetivamente aplicado para resolver o desafio Lead Scorer. Cada seção mapeia para uma decisão concreta: skills usadas, instintos ativados, prompts emitidos para o GLM-5.2, design system aplicado na UI, e arquitetura de memória.

A filosofia aqui é baseada no princípio do regulamento do challenge:

> *"O valor de um AI Master não é saber pedir pra IA. É saber o que pedir, quando desconfiar, o que ajustar, e o que só um humano com contexto consegue fazer."*

---

## 1. Compreensão do Desafio

### Challenge 003 — Lead Scorer

**Stakeholders:**
- **Head de Revenue Operations** — quer uma ferramenta útil, não um notebook acadêmico
- **35 vendedores** — precisam saber onde focar segunda-feira de manhã
- **Managers regionais** — precisam ver pipeline dos seus reportes
- **Time de RevOps** — precisa dar manutenção no código

**Problema de negócio:**
- Pipeline de ~8.800 oportunidades
- Priorização atual é "no feeling" — cada vendedor decide sozinho
- Resultado: tempo desperdiçado em deals que não fecham + oportunidades boas esfriando

**O que a solução precisa fazer:**
1. Mostrar o pipeline de forma acionável
2. Atribuir score de priorização a cada deal (não só ordenar por valor)
3. Explicar **por que** cada deal tem aquele score
4. Filtrar por vendedor/manager/região
5. Rodar de verdade — não mockup

### Prioridades (rankeadas)

| # | Prioridade | Por que | Impacto se feito vs. não feito |
|---|-----------|--------|---------------------------------|
| P0 | **Score explicável 0-100** | é o critério central do challenge | sem isso, não é Lead Scorer |
| P0 | **App funcional rodando** | "precisa rodar, não é PowerPoint" | desclassificação implícita se não rodar |
| P1 | **Filtros por vendedor/manager/região** | citado como "imeditamente mais útil" | transforma de demo em ferramenta |
| P1 | **UX de vendedor não-técnico** | critério de qualidade explícito | adesão real vs. abandono |
| P2 | **Visualizações (distribuição de scores, KPIs)** | ajuda a decisão, não só mostra dado | eleva de tabela para dashboard |
| P3 | **Comparação com ML baseline** | valida a heurística | bonus de profundidade |
| P4 | **Whitelabel com identidade G4** | diferencia a entrega | polish que mostra texto |

---

## 2. Skills Ativadas

Skills são capacidades discretas que Gabriel liga/desliga conforme a etapa. Cada skill tem um trigger, um prompt-pattern, e uma saída esperada.

### SKILL-01 — Research-First Development
**Trigger:** antes de escrever a primeira linha de código
**Prompt pattern:**

```
[SKILL: RESEARCH-FIRST]
Contexto: {desafio}
Antes de implementar, liste:
1. Hipóteses de negócio a validar com os dados
2. Perguntas que um Head de RevOps faria
3. Features óbvias vs. features que só um AI Master traria
4. Armadilhas do dataset (vieses, nulos, formatos)
Não escreva código ainda. Apenas o plano de pesquisa.
```

**Output esperado:** lista de questões e hipóteses, não código.

### SKILL-02 — Spec-Driven Architecture
**Trigger:** antes de cada milestone de implementação
**Prompt pattern:**

```
[SKILL: SPEC-DRIVEN]
Tarefa: {milestone}
Escreva a SPEC técnica:
- Propósito (1 frase)
- Inputs e Outputs esperados
- Critérios de aceitação mensuráveis
- Edge cases conhecidos
- Dependências
Sem spec → sem implementação. Sem spec aprovada → sem commit.
```

### SKILL-03 — Explainability-First Modeling
**Trigger:** ao desenhar a lógica de scoring
**Prompt pattern:**

```
[SKILL: EXPLAINABILITY-FIRST]
Construa a função de scoring com estas constraints:
1. Score final 0-100
2. Cada componente deve ser explicável em uma frase em PT-BR para leigo
3. Retornar dict de {componente: (contribuição, label_explicativa)}
4. Nada de ML black-box nesta versão — regras + heurísticas
Raciocínio de cada peso deve ser citado na docstring.
```

### SKILL-04 — Security & Secret Scan
**Trigger:** antes de cada commit
**Prompt pattern:**

```
[SKILL: SEC-SCAN]
Revise este diff procurando:
- Hardcoded secrets/credentials
- Paths absolutos que quebram em outra máquina
- Dados pessoais (PII) vazando no código
- Dependências com CVEs conhecidas
- `.env`/chaves Kaggle no repositório
Flag cada item suspeito — não assuma que está limpo.
```

### SKILL-05 — Continuous Memory Optimization
**Trigger:** ao final de cada sessão ou etapa concluída
**Prompt pattern:**

```
[SKILL: MEMORY-OPT]
Resuma desta sessão:
1. Decisões tomadas e por quê
2. Prompts que funcionaram bem (padronizar)
3. Erros da IA e correções aplicadas
4. Estado atual do repositório
5. Próximos 3 passos imediatos
Salve no /memories/session/ para persistir contexto.
```

### SKILL-06 — Legacy Command Shim
**Trigger:** quando comando/sintaxe antiga é referenciada
**Prompt pattern:**

```
[SKILL: SHIM]
Comando legado citado: {cmd}
Traduza para versão moderna e cross-platform (Win/Linux/Mac).
Se equivalente chain no PowerShell 5.1 (`;` não `&&`).
Aponte para a versão canônica no projeto.
```

---

## 3. Instincts (Instintos de Operação)

Instintos são checagens automáticas que o operador humano roda mentalmente, sem esperar a IA perguntar. São o "second nature" do AI Master.

| Instinto | Quando ativa | Ação |
|----------|-------------|------|
| **"Checar tipos dos dados"** | qualquer `.csv` carregado | `df.dtypes`, `df.head()`, nulos |
| **"Checar formato de data"** | qualquer coluna com `_date` | nunca assumir ISO; testar com um NaT |
| **"Nominalizar colunas antes de normalizar"** | antes de MinMax | checar se a coluna é numérica mesmo, outliers extremos |
| **"Edge case 'deal sem engage_date'"** | qualquer feature temporal |vais retornar 0 e sinalizar "sem dados", não NaN |
| **"Nada de inventar nome de coluna"** | qualquer código gerado | validar contra `df.columns` real |
| **"Caminhos absolutos = red flag"** | qualquer `open('/Users/...')` | trocar por `pathlib.Path` relativo ao repo |
| **"Process log ou desclassificação"** | cada decisão tomada | deixar rastro no harness/log |
| **"Outro dev vai dar manutenção"** | cada função escrita | docstring + tipagem + nome claro |
| **"Vendedor não é data scientist"** | cada UI decision | texto em PT-BR, zero jargão |
| **"GLM-5.2 alucina colunas"** | cada geração de código | cruzar com schema real antes de rodar |

---

## 4. Agents (Papéis que GLM-5.2 assume via Prompt)

Cada "agent" é um envelope de prompt que ajusta o comportamento da IA para um tipo de tarefa. Isso é diferente de skill: skill é capacidade, agent é persona/contexto.

### AGENT-A — The Architect
**Persona:** senior solution architect
**Prompt envelope:**

```
[AGENT: ARCHITECT]
Você é arquiteto de solução sênior. Modo thinker, não coder.
- Responda em tópicos, nãoEm código ainda
- Justifique cada decisão técnica com trade-offs
- Considere custo de manutenção e tempo (4-6h é o budget)
- Cite padrões que conhece, não invente padrões
Tarefa: {decisão arquitetural}
```

### AGENT-B — The Builder
**Persona:** full-stack dev produtivo
**Prompt envelope:**

```
[AGENT: BUILDER]
Você é dev full-stack entregando features contra uma spec já aprovada.
- Código limpo, tipado, docstringado
- Use pandas para dados, Streamlit para UI, plotly para charts
- Sem invenções de coluna — só os nomes reais que vou te passar
- Sempre trate edge cases (nulos, tipos errados, lista vazia)
- Commits por feature coeso, não por linha
Spec: {colar a spec}
Implemente: {tarefa atômica}
```

### AGENT-C — The Reviewer
**Persona:** code reviewer cético
**Prompt envelope:**

```
[AGENT: REVIEWER]
Você é code reviewer rigoroso. Assuma que tem bug.
- Leia cada linha procurando: tipos errados, edge cases, hardcode, PII
- Verifique se o output bate com a spec declarada
- Pondere se o código é idiomático da versão moderna da lib
- Não diga "looks good" — diga o que falta
CódigoCódigo: {colar}
```

### AGENT-D — The Domain Expert (RevOps)
**Persona:** Head de RevOps julgando a ferramenta
**Prompt envelope:**

```
[AGENT: REVOPS-EXPERT]
Você é Head de RevOps. Você abriu esta tela segunda-feira 9h.
- Você não tem paciência para jargão técnico
- Você quer saber: onde focar hoje, qual deal priorizar, por quê
- Você odeia scoring que não explica o motivo
- Você adora poder filtrar por seus reportes
Reaja a esta interface/relatório: {colar prints/JSON scores}
O que falta? O que confunde? O que você usaria?
```

---

## 5. Design System (fonte canônica)

A seção de design deste harness foi substituída pelo super prompt canônico:

- `docs/G4-DESIGN-SYSTEM-PROMPT.md`

Regra operacional:

- Esse arquivo prevalece sobre qualquer versão antiga desta seção.
- Tokens legados (`--g4-success`, `--g4-warning`, `--g4-danger`) estão deprecados.
- Para qualquer iteração de UI, use o bloco `<<< >>>` do super prompt sem alterar a paleta/tipografia fora dos tokens definidos.

Observação:

- Quando houver nova extração visual do site, atualize primeiro `docs/G4-DESIGN-SYSTEM-PROMPT.md` e só depois referências neste harness.

---

## 6. Prompts Reais que GLM-5.2 Vou Usar

Estes são os prompts reais que vou colar no GitHub Copilot (GLM-5.2) na ordem de execução do desafio. Cada um carrega o agent + skill ativos.

### Prompt 01 — Research-First (AGENT-A + SKILL-01)

```
[AGENT: ARCHITECT] [SKILL: RESEARCH-FIRST]

Estou resolvendo o Challenge 003 Lead Scorer do G4 AI Master Challenge.
Brief: construir ferramenta que vendedores usem pra priorizar ~8.800 deals.
Tenho 4 CSVs: accounts.csv (~85), products.csv (7), sales_teams.csv (35),
sales_pipeline.csv (~8800). Ligados por account/product/sales_agent/opportunity_id.

Antes de codar, me ajude a:
1. Listar 5 hipóteses de negócio sobre o que faz um deal fechar
2. Quais features óbvias vs. quais um AI Master traria (não óbvias)
3. Que armadilhas devo checar no dataset (nulos, formato de data, PII)
4. Quais perguntas o Head de RevOps faria ao ver a ferramenta

Em tópicos, sem código. Quero o plano de pesquisa.
```

### Prompt 02 — EDA contra schema real (AGENT-B + SKILL-04)

```
[AGENT: BUILDER] [SKILL: SEC-SCAN]

Escreva script EDA em pandas para sales_pipeline.csv.
Requisitos:
- Carregar de solution/data/sales_pipeline.csv (path relativo com pathlib)
- Não assumir nomes de coluna — print df.columns e dtypes primeiro
- Checar nulos por coluna
- Distribuição de deal_stage
- Win rate (Won / Won+Lost) por sales_agent, ordenado
- Distribuição de close_value por stage
- Tempo médio entre engage_date e close_date por stage
  (USAR format='%m/%d/%Y' — descobri na mão que é MM/DD/YYYY)

Sem hardcode. Sem PII printado. Salvar resultados em solution/eda_report.txt
também, não só printar.
```

### Prompt 03 — Spec do Scoring (AGENT-A + SKILL-02)

```
[AGENT: ARCHITECT] [SKILL: SPEC-DRIVEN]

Escreva SPEC da função score_deal(row, agent_winrate).
Requisitos não-negociáveis:
- Score 0-100
- 6 componentes com pesos informados por mim (passo uma tabela)
- Explicabilidade: retornar dict {componente: (subscore, label_ptBR)}
- Sem ML, só regras/MinMax
- Edge case: engage_date NaN → componente velocity=0 com label explicativa

Componentes e pesos:
- stage advancement 25%
- pipeline velocity 20%
- account size 20%
- product value 15%
- agent track record 15%
- deal value 5%

Saída: SPEC markdown, não código. Quero aprovar antes do build.
```

### Prompt 04 — Build da função de scoring (AGENT-B)

```
[AGENT: BUILDER]

Implemente a spec aprovada emAnexo: {colar spec}
Arquivo: solution/scoring.py
Constraints:
- Função score_deal(row: dict, agent_winrate: dict) -> tuple[int, dict]
- Componentes normalizados via MinMax respeitando ranges reais dos dados
- Docstring cite o porquê de cada peso
- Type hints
- Tratar deals Prospect sem engage_date (velocity=0, label específica)
- Não usar sklearn nesta versão — matemática pura com numpy/pandas
```

### Prompt 05 — App Streamlit (AGENT-B + Design System)

```
[AGENT: BUILDER]

Construa solution/app.py com Streamlit seguindo o Design System G4:
- Fundo branco, texto navy #001F35, secondary bg cream #F5F4F3
- Font: Manrope (body), serif (display)
- CTA/badges: border-radius 3px
- Layout: sidebar filtros (vendedor, manager, escritório, stage) lendo
  valores reais de sales_teams.csv e sales_pipeline.csv — não inventar
- Topo: 4 KPIs (deals ativos, score médio, valor pipeline, top deal)
- Tabela principal: deals ordenados por score, com badge colorido
  (>80 verde, 50-80 amarelo, <50 vermelho) — cores wash não batidas
- Cada deal expansível: mostrar breakdown do score com cada componente
  e label explicativa em PT-BR
- Gráfico plotly: distribuição de scores (histograma) + scatter
  score x close_value

Use os dados reais, paths relativos, sem hardcode.
```

### Prompt 06 — Review (AGENT-C + SKILL-04)

```
[AGENT: REVIEWER] [SKILL: SEC-SCAN]

Revise este diff rigorosamente. Assuma que tem bug.
{colar arquivos}
Procure:
- Hardcode de paths absolutos
- Chaves Kaggle/PII no código
- Edge cases não tratados (NaN, dtype errado, lista vazia)
- Invenções de coluna que não existem no dataset
- Código não-idiomático de Streamlit
- Falta de docstring/type hints
Resposta: item a item, com linha, problema, correção sugerida.
Nada de "looks good".
```

### Prompt 07 — Teste de uso pelo Head de RevOps (AGENT-D)

```
[AGENT: REVOPS-EXPERT]

Aqui está o output do app rodando em dados reais:
{colar prints/JSON de exemplo}
Como Head de RevOps julgando:
- O que você usaria amanhã?
- O que confunde?
- O que falta (próximas 3 iterações)?
Seja brutalmente honesto — não é elogio que me ajuda.
```

### Prompt 08 — Consolidar Process Log (SKILL-05)

```
[SKILL: MEMORY-OPT]

Resuma esta sessão inteira para /memories/session/:
1. Decisões e por quês
2. Prompts que funcionaram (vira template)
3. Erros do GLM-5.2 e correções
4. Estado do repositório
5. Próximos 3 passos
Formato markdown conciso.
```

---

## 7. Memory Architecture

Estrutura de memória usada durante toda a execução.

```
/memories/
├── repo/
│   └── g4-design-system.md        ← design tokens extraídos do site
├── session/
│   ├── desafio-g4-contexto.md     ← contexto do challenge
│   ├── session-state.md           ← estado da sessão atual
│   └── prompts-que-funcionaram.md ← library de prompts validados
└── (user memory não usada neste challenge)
```

**Regras de memória:**
- `repo/` persiste entre sessões — vou consultar na próxima vez que abrir este repo
- `session/` é scratch — limpo ao final
- Cada prompt bem-sucedido vai pra `prompts-que-funcionaram.md` para futura padronização
- Não duplico memória — se algo mudou, atualizo in place

---

## 8. Hooks (Gatilhos Automatizados)

Hooks são checagens que rodam automaticamente em eventos do workflow.

| Evento | Hook | Ação |
|--------|------|------|
| Antes de commit | `sec-scan` | rodar grep por secrets/PII no diff |
| Após carregar CSV | `dtype-check` | forçar print de dtypes no output |
| Após gerar tabela | `pct-null-alert` | alert se >20% de nulos em qualquer coluna |
| Após gerar função | `edge-test` | rodar com input NaN e vazio |
| Após código Streamlit | `run-app` | `streamlit run app.py --server.headless true` para smoke test |
| Após cada milestone | `log-append` | anexar decisão no PROCESS_LOG.md |
| Final de sessão | `memory-consolidate` | rodar SKILL-05 |

---

## 9. Rules (Regras Hard)

Estas regras não podem ser violadas. Se a IA propuser algo contra, rejeito.

1. **Não inventar nomes de coluna** — cruzar sempre com `df.columns` real
2. **Não hardcodear paths absolutos** — usar `pathlib.Path(__file__).parent`
3. **Não deixar PII no repositório** — e-mails, nomes reais, IDs de clientes
4. **Não commitar sem spec aprovada** para features de peso
5. **Não commitar sem rodar o app** — sem smoke test, sem commit
6. **Não usar `&&` no PowerShell** — usar `;` (Win 5.1)
7. **Não modificar arquivos fora de `submissions/seu-nome/`** — regra do challenge
8. **Não usar ML black-box nesta versão** — explainability > acurácia aqui
9. **Não escrever documento de 40 páginas** — 5 resolvem
10. **Não omitir erros da IA no Process Log** — transparência é critério de avaliação

---

## 10. Continuous Learning Loop

```
    ┌───────────────────────────────────────┐
    ▼                                       │
 Executar Prompt ──> Avaliar Output ──> Decidir
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                        Funcionou?           Falhou?
                              │                   │
                              ▼                   ▼
                  Padronizar em /memories/   Corrigir + logar erro
                              │                   │
                              └─────────┬─────────┘
                                        ▼
                            Próximo prompt refinado
```

---

## 11. Estado Atual do Desafio

**Feito:**
- [x] Fork + clone do repositório
- [x] Branch `submission/gabriel` criada (no mundo real) — no workspace usamos `submission/seu-nome` como placeholder
- [x] Pasta `submissions/seu-nome/{solution,process-log,docs}` criada
- [x] Process log de evidência iniciado (`process-log/PROCESS_LOG.md`)
- [x] Este harness (`docs/HARNESS.md`)

**Próximos passos imediatos:**
1. Renomear `submissions/seu-nome` para `submissions/gabriel`
2. Configurar ambiente Python (venv + requirements.txt)
3. Baixar os 4 CSVs do Kaggle para `solution/data/`
4. Executar Prompt 01 (Research-First)
5. Executar Prompt 02 (EDA)
6. Iterar até ter app rodando

---

## 12. Glossário do Harness

| Termo | Definição |
|-------|-----------|
| **Spec** | documento técnico verificável, aprovado antes de implementação |
| **Skill** | capacidade operacional ativável via prompt tag |
| **Agent** | persona/contexto assumido pela IA via prompt envelope |
| **Instinct** | checagem mental automática que o operador humano roda sem precisar pedir |
| **Hook** | checagem automatizada disparada por evento do workflow |
| **Rule** | regra hard — violação exige justificativa explícita |
| **Prompt Harness** | estrutura repetível que envelopa cada interação com IA |
| **Spec-Driven** | metodologia onde spec vem antes de prompt, prompt vem antes de código |
| **Velocidade do GLM-5.2** | tendência à alucinação de colunas — sempre validar contra schema |

---

## 13. Apêndice — Como Gabriel deve usar este Harness no ECC

> ECC = "Engenharia de Contexto.xpathContraste com Copilot" — o ritual de aplicar o harness em cada bloco de trabalho.

**Passo a passo do ECC:**
1. Abrir este `HARNESS.md` na sidebar
2. Identificar qual agent + skill a próxima tarefa requer
3. Copiar o prompt envelope correspondente da Seção 6
4. Substituir placeholders `{...}` por contexto concreto da tarefa
5. Colar no GitHub Copilot chat
6. Avaliar output contra a expectativa da spec/skill
7. Aceitar ou pedir correção com `[AGENT: REVIEWER]`
8. Anexar evidência no `PROCESS_LOG.md`
9. Ao final da sessão, rodar SKILL-05 (MEMORY-OPT)

Este fluxo garante que cada interação com IA é:
- **Rastreável** (prompt nomeado, agent identificado)
- **Reproduzível** (outro dia, mesma tarefa, mesmo template)
- **Verificável** (saída batever com spec?)
- **Melhorável** (prompts que funcionaram viram template na memória)

---

_Assinado:_ Gabriel
_Sistema:_ Harness-Native Operator v1.0
_Desafio:_ AI Master Challenge — Challenge 003 Lead Scorer
_Modelo_:_ GLM-5.2 (GitHub Copilot)
_Data início:_ 06/07/2026