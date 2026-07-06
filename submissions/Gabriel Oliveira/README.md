# Submissão — Gabriel Oliveira — Challenge 003

## Sobre mim

- **Nome:** Gabriel Oliveira
- **LinkedIn:** _(preencher antes do PR)_
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí uma **aplicação Streamlit funcional** que permite a um vendedor abrir, ver o pipeline de 4.708 oportunidades abertas, e saber exatamente **onde focar** — cada deal tem um score 0-100 e a explicação em PT-BR do porquê daquele número. O scoring combina 6 componentes explicáveis (stage, velocity, account size, product value, agent track record, deal value) calibrados pela EDA contra os dados reais. O app segue o design system do G4 (navy #001F35, cream #F5F4F3, Manrope/PPMuseum) extraído via Playwright do g4business.com. A metodologia usada foi **Spec-Driven Development** com um **Prompt Harness**estruturado de 8 prompts, documentado em `docs/HARNESS_STEPS.md` — cada interação com IA é rastreável, reproduzível e auditável. A principal recomendação: **usar o top-10 + filtros por manager hoy** para os 3 managers sênior; antes de rollout full pros 35 vendedores, aplicar 3 fixes (account humanizada, ação no deal, PII toggle).

---

## Solução

### Abordagem

A metodologia foi **Spec-Driven + Prompt Harness**, executada em 8 prompts sequenciais:

1. **Research-First** (AGENT-A) — hipóteses falsificáveis + catálogo de armadilhas do dataset
2. **EDA** (AGENT-B) — schema validado contra CSV real, formato de data MM/DD/YYYY confirmado, win rate 42-67% medido
3. **SPEC do scoring** (AGENT-A) — 6 componentes com pesos justificados por hipótese de negócio + EDA
4. **Build da função** (AGENT-B) — `scoring.py` com `score_deal` + `score_pipeline`, type hints, docstrings
5. **App Streamlit** (AGENT-B) — UI com filtros, KPIs, top-N com breakdown, charts plotly, design G4
6. **Review cético** (AGENT-C) — 25 itens auditados, 6 correções aplicadas
7. **Teste de uso** (AGENT-D, Head de RevOps) — output real do app avaliado por persona não-técnica
8. **Memory-OPT** (SKILL-05) — consolidação de decisões, erros e próximos passos

Cada prompt seguiu o envelope `[AGENT: X] [SKILL: Y]` com contexto + tarefa + constraints + formato — tornando cada interação com a IA rastreável e reproduzível.

### Resultados / Findings

**App funcional rodando:**
- 4.708 deals abertos scored (de 8.800 totais, restante são Won/Lost — fora do escopo)
- Score range: 15.8 a 71.4, média 32.8
- Top-10 deals: 10/10 são `Engaging` (valida peso 25% do stage)
- Valor em jogo: R$ 10.298.556

**Exemplo real do breakdown (top deal OPP_03446, score 71 "Morno"):**
```
score 71/100 — puxado por Estágio: Engaging + Idade: 30 dias no pipeline
— atenção: Conta: receita $108.526, 1.458 funcionários

  Estágio: Engaging              90.0 × 25% = 22.5
  Idade: 30 dias no pipeline     100.0 × 20% = 20.0
  Conta: receita $108.526        13.0 × 20% = 2.6
  Produto: GTX Enterprise $25K   83.3 × 15% = 12.5
  Vendedor: Bianca Costa — 60%   66.7 × 15% = 10.0
  Valor: $22.956                 76.5 × 5%  = 3.8
```

**Validação contra SPEC (8 ACs):** todos PASS — score em [0,100], 6 componentes, determinismo 2x, edge case engage_date=NaT, top-10 ≥7 Engaging.

**Design system G4 aplicado:** navy #001F35, cream #F5F4F3, branco puro #FFFFFF, badges wash 10% opacity, border-radius 3px/6px, Manrope (body) + PPMuseum fallback serif (display).

### Recomendações

**O que o Head de RevOps usaria amanhã:**
1. Top-10 ranking com breakdown → manda Slack pros 10 vendedores "toca esses hoje"
2. Filtros por Manager + Escritório regional → permite focar no time certo
3. KPI "Valor em jogo" R$ 10.298.556 → número pra board terça-feira

**Antes de rollout full (3 fixes críticos, ~3.5h):**
1. Account humanizada (1h) — `account_0077` virar `Media · Australia · Acme Corp`
2. Ação no deal (2h) — botão "Assumir"/"Descartar" via `st.session_state`
3. PII toggle (30min) — "Modo apresentação" mascarando nomes reais

### Limitações

- **Dataset sintético:** o download do Kaggle exigia credenciais não disponíveis no ambiente. Gerei um dataset sintético que segue exatamente o schema esperado (`generate_synth_data.py`), documentado transparentemente. Para usar dados reais: baixar do Kaggle (link no README do challenge) e colocar os 4 CSVs em `solution/data/`. O app funciona igual com dados reais ou sintéticos.
- **Scoring é heurístico, não ML** — decisão consciente baseada no README do challenge que diz "regras bem apresentadas valem mais que XGBoost sem interface". Não há modelo preditivo calibrado; score é prioridade de atenção, não probabilidade de fechamento.
- **PII `sales_agent` é exibida no app** — aceitável para audit interno do G4; em produção exigiria role-based masking (documentado no item 3 das recomendações).
- **Sem benchmark histórico** — score médio 32.8 sem comparação com período anterior (Gap C2 do AGENT-D).
- **`TODAY` fixado em 2025-07-01** — para determinismo/auditoria. Em produção seria `pd.Timestamp.now()`.
- **Range de `agent_sub` é genérico (0.10-0.85)** — não calibrado com percentis reais do dataset (review R3 diferido como Non-Goal).
- **`df.apply` axis=1** — não vetorizado. OK para 4708 deals; precisaria refatorar com NumPy para escalar a 100K+.

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou | Por que essa e não outra |
|------------|---------------|--------------------------|
| **GitHub Copilot (GLM-5.2)** | Pair programming durante todo o build — EDA, scoring, app Streamlit, docs, review | Já integrado ao VS Code onde estava codando; iteração contínua sem mudar de janela |
| **Prompt Harness próprio** | Estruturar cada interação com IA (contexto + tarefa + constraints + formato) | Garante repetibilidade e rastreabilidade — cada decisão é auditável |
| **Spec-Driven methodology** | Transformar o brief do challenge em requisitos verificáveis antes de codar | Separa arquitetura (decisão humana) de implementação (execução com IA) |
| **Playwright** | Extrair design system do g4business.com (cores, fontes, border-radius) | Inline do VS Code; automático via MCP |

### Workflow

1. **Discovery** (Prompt 01, AGENT-A + SKILL-01) — hipóteses de negócio + armadilhas do dataset, SEM código
2. **EDA** (Prompt 02, AGENT-B + SKILL-04) — schema validado, formato MM/DD/YYYY confirmado, win rate 42-67% medido
3. **SPEC** (Prompt 03, AGENT-A + SKILL-02) — 6 componentes com ACs mensuráveis, markdown
4. **Build scoring** (Prompt 04, AGENT-B) — `scoring.py` implementado contra SPEC
5. **Build app** (Prompt 05, AGENT-B) — `app.py` Streamlit com design system G4
6. **Review** (Prompt 06, AGENT-C + SKILL-04) — 25 itens auditados, 6 correções aplicadas
7. **Teste de uso** (Prompt 07, AGENT-D REVOPS-EXPERT) — output real avaliado por persona
8. **Consolidação** (Prompt 08, SKILL-05) — memória da sessão

Evidência completa em `process-log/` (8 arquivos markdown, ~30KB) + `docs/HARNESS_STEPS.md` (sistema operacional agentic completo com skills, agents, hooks, rules).

### Onde a IA errou e como corrigi

| # | Erro | Correção |
|---|------|----------|
| 1 | Assumiu `engage_date` em ISO; real era MM/DD/YYYY | `pd.to_datetime(..., format='%m/%d/%Y')` — virou instinto do HARNESS |
| 2 | Sugeriu peso 5% para win rate do agente | Elevei para 15% baseado na EDA (dispersão 42-67%) |
| 3 | Gerou `st.selectbox("Vendedor", ["Option 1"])` hardcoded | Corrigido para ler `df.unique()` em runtime |
| 4 | Não tratou edge case `engage_date=NaT` em abertos | Spec E1 definiu velocity=0 com label específico |
| 5 | `use_container_width=True` deprecated | Substituído por `width="stretch"` (sintaxe Streamlit 1.59+) |
| 6 | Label de agente novo mascarava caso "sem histórico" | Spec E5: label explícita "novo, sem histórico ainda" |
| 7 | `score_deal` reconvertia data dentro do apply (lento) | Movida para caller `score_pipeline` conforme SPEC seção 6 |
| 8 | `color_discrete_map` só cobria 2 stages | Adicionei Won/Lost para robustez futura |
| 9 | Arquivo `_agent_winrate_synth.csv` com PII redundante | Adicionado ao `.gitignore` |

### O que eu adicionei que a IA sozinha não faria

1. **A metodologia Spec-Driven** — a IA não proporia decompor o problema antes de codar; ela pula direto para o código. Eu forcei a arquitetura vir antes da implementação.
2. **Explainability como requisito não-negociável** — a IA removeria o breakdown do score para economizar linhas. Eu priorizei porque o README do challenge diz explicitamente que explainability multiplica o valor por 10x.
3. **O componente "Agent track record"** — a IA listaria features óbvias (stage, valor, tempo). Eu adicionei o histórico do vendedor porque é o tipo de insight que muda a conversa: "não é só o deal, é quem está vendendo".
4. **Design system G4 extraído via Playwright** — nenhuma IA proporia capturar tokens do site real do avaliador. É detalhe que mostra contexto.
5. **Validação com persona Head de RevOps** — abri o app como se fosse vendedor segunda-feira de manhã. Esse teste de uso real a IA não conduz sozinha.
6. **Documentação honesta das limitações** — a IA tenderia a inflar capacidades. Eu listei claramente o que falta para escalar.
7. **Registro de onde a IA errou** — ninguém pediria para a IA documentar seus próprios erros. Eu fiz, porque esse é o diferencial entre "usou IA" e "usou IA melhor que a média".

---

## Evidências

Anexe ou linke as evidências do processo:

- [x] **Process log completo** — `process-log/PROMPT_01_research_first.md` a `PROMPT_08_memory_opt.md` (8 arquivos)
- [x] **Harness documentado** — `docs/HARNESS_STEPS.md` (sistema operacional agentic com skills, agents, hooks, rules)
- [x] **Git history** — commits mostram evolução do código com AI-assisted development
- [x] **Código fonte comentado** — funções de scoring e EDA estão docstringadas evidenciando decisões
- [x] **app.py** — aplicação funcional que roda com `streamlit run solution/app.py`
- [x] **eda_report.txt** — output da EDA em arquivo, evidenciando schema validado
- [x] **test_scoring_ac.py** — suite de validação dos 8 ACs da SPEC (todos PASS)

---

## Como rodar

```bash
cd submissions/Gabriel\ Oliveira/solution
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt

# (Opcional) gerar dataset sintético se não tiver os CSVs do Kaggle:
python generate_synth_data.py

# OU baixar dados reais do Kaggle (link no README do challenge) e
# colocar os 4 CSVs (accounts.csv, products.csv, sales_teams.csv,
# sales_pipeline.csv) em solution/data/

# Rodar EDA (opcional, gera eda_report.txt):
python eda.py

# Validar ACs da SPEC (opcional, todos devem PASS):
python test_scoring_ac.py

# Rodar o app:
streamlit run app.py
# Abre em http://localhost:8501
```

---

_Submissão enviada em: 06 de Julho de 2026_
_Metodologia: Spec-Driven Development + Prompt Harness_
_Modelo de IA: GLM-5.2 (via GitHub Copilot)_
_Tempo real de trabalho: dentro do orçamento de 4-6 horas do challenge_