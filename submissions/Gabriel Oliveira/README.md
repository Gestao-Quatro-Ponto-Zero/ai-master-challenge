# Submissão — Gabriel Oliveira — Challenge 003

## Sobre mim

- **Nome:** Gabriel Oliveira
- **LinkedIn:** https://www.linkedin.com/in/gabrielrodrigues/
- **Challenge escolhido:** 003 — Lead Scorer (Vendas / RevOps)

---

## Executive Summary

Construí uma **aplicação Streamlit funcional** que permite a um vendedor abrir, ver o pipeline de 2.089 oportunidades abertas, e saber exatamente **onde focar** — cada deal tem um score 0-100 e a explicação em PT-BR do porquê daquele número. O scoring combina 6 componentes explicáveis (stage, velocity, account size, product value, agent track record, deal value) calibrados pela EDA contra os **dados reais do challenge** (CRM Sales Predictive Analytics, Kaggle/CC0 — 8.800 oportunidades, 85 contas, 35 vendedores). O app segue o design system do G4 (navy #001F35, cream #F5F4F3, Manrope/PPMuseum) extraído via Playwright do g4business.com. A metodologia usada foi **Spec-Driven Development** com um **Prompt Harness** estruturado de 8 prompts, documentado em `docs/HARNESS_STEPS.md` — cada interação com IA é rastreável, reproduzível e auditável. A principal recomendação: **usar o top-10 + filtros por manager hoje** para os managers sênior; antes de rollout full pros 35 vendedores, aplicar 3 fixes (enriquecimento das contas sem cadastro, ação no deal, PII toggle).

---

## Solução

### Abordagem

A metodologia foi **Spec-Driven + Prompt Harness**, executada em 8 prompts sequenciais:

1. **Research-First** (AGENT-A) — hipóteses falsificáveis + catálogo de armadilhas do dataset
2. **EDA** (AGENT-B) — schema validado contra CSV real, formato de data ISO 8601 (YYYY-MM-DD) confirmado, win rate 55-70% medido
3. **SPEC do scoring** (AGENT-A) — 6 componentes com pesos justificados por hipótese de negócio + EDA
4. **Build da função** (AGENT-B) — `scoring.py` com `score_deal` + `score_pipeline`, type hints, docstrings
5. **App Streamlit** (AGENT-B) — UI com filtros, KPIs, top-N com breakdown, charts plotly, design G4
6. **Review cético** (AGENT-C) — 25 itens auditados, 6 correções aplicadas
7. **Teste de uso** (AGENT-D, Head de RevOps) — output real do app avaliado por persona não-técnica
8. **Memory-OPT** (SKILL-05) — consolidação de decisões, erros e próximos passos

Cada prompt seguiu o envelope `[AGENT: X] [SKILL: Y]` com contexto + tarefa + constraints + formato — tornando cada interação com a IA rastreável e reproduzível.

### Resultados / Findings

**App funcional rodando (dados reais do challenge):**
- 2.089 deals abertos scored (de 8.800 totais: 1.589 Engaging + 500 Prospecting; restante são Won/Lost — fora do escopo de priorização)
- Score range: 12.2 a 69.8, média 32.7
- Top-10 deals: 10/10 são `Engaging` (valida peso 25% do stage)
- Valor em jogo: R$ 4.966.215 (soma do preço de lista dos produtos dos deals abertos — no dataset real `close_value` só existe para deals Won/Lost)

**Exemplo real do breakdown (top deal 4ZQTMS3Z — Violet Mclelland / conta Kan-code, score 70 "Morno"):**
```
score 70/100 — puxado por Estágio: Engaging + Conta: receita US$ 11.698M, 34.288 funcionários
— atenção: Valor esperado do deal: $0

  Estágio: Engaging                          90.0 × 25% = 22.5
  Idade: 38 dias no pipeline                 91.1 × 20% = 18.2
  Conta: receita US$ 11.698M, 34.288 func.  100.0 × 20% = 20.0
  Produto: MG Special — ticket $55            0.2 × 15% =  0.0
  Vendedor: Violet Mclelland — win rate 63%  60.1 × 15% =  9.0
  Valor esperado do deal: $0                  0.0 × 5%  =  0.0
```
Este caso ilustra a explainability: o deal sobe pelo estágio + conta gigante, mas o vendedor vê na hora que o produto é de ticket baixo (MG Special, $55) — contexto que um número solto esconderia.

**Validação contra SPEC (8 ACs):** todos PASS — score em [0,100], 6 componentes, determinismo 2x, edge case engage_date=NaT, top-10 ≥7 Engaging.

**Design system G4 aplicado:** navy #001F35, cream #F5F4F3, branco puro #FFFFFF, badges wash 10% opacity, border-radius 3px/6px, Manrope (body) + PPMuseum fallback serif (display).

### Recomendações

**O que o Head de RevOps usaria amanhã:**
1. Top-10 ranking com breakdown → manda Slack pros 10 vendedores "toca esses hoje"
2. Filtros por Manager + Escritório regional (Central/East/West) → permite focar no time certo
3. KPI "Valor em jogo" R$ 4.966.215 → número pra board terça-feira

**Antes de rollout full (3 fixes críticos, ~3.5h):**
1. Enriquecer contas sem cadastro (1h) — ~16% dos deals abertos não têm `account` vinculado no CRM; puxar setor/receita para dar contexto ao card
2. Ação no deal (2h) — botão "Assumir"/"Descartar" via `st.session_state`
3. PII toggle (30min) — "Modo apresentação" mascarando nomes reais

### Limitações

- **Dados reais do challenge:** a solução usa os 4 CSVs reais do dataset [CRM Sales Predictive Analytics](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics) (Kaggle, licença CC0). O download público (`https://www.kaggle.com/api/v1/datasets/download/agungpambudi/crm-sales-predictive-analytics`) não exige credenciais. Os 4 CSVs já estão versionados em `solution/data/`.
- **Contas sem cadastro:** ~16% dos deals no pipeline não têm `account` vinculado no CRM (data quality real). Esses deals recebem subscore de account_size = 0 com label explícito "sem cadastro vinculado — enriquecer dados da conta", em vez de crédito indevido.
- **`close_value` só existe para deals fechados:** no dataset real, deals abertos (Prospecting/Engaging) não têm `close_value`. Para o "valor em jogo" e o componente de deal value, usamos o preço de lista do produto (`sales_price`) como valor potencial.
- **Scoring é heurístico, não ML** — decisão consciente baseada no README do challenge que diz "regras bem apresentadas valem mais que XGBoost sem interface". Não há modelo preditivo calibrado; score é prioridade de atenção, não probabilidade de fechamento.
- **PII `sales_agent` é exibida no app** — aceitável para audit interno do G4; em produção exigiria role-based masking (documentado no item 3 das recomendações).
- **Sem benchmark histórico** — score médio 32.7 sem comparação com período anterior (Gap C2 do AGENT-D).
- **`TODAY` fixado em 2017-12-31** — dia seguinte ao fim da base real (2016-10 a 2017-12), para que a velocity do pipeline faça sentido e o resultado seja determinístico/auditável. Em produção seria `pd.Timestamp.now()`.
- **Range de `agent_sub` calibrado (0.50-0.72)** — reflete a faixa real de win rate observada na EDA (55-70%), estreita porque os vendedores têm performance homogênea neste dataset.
- **`df.apply` axis=1** — não vetorizado. OK para 2.089 deals; precisaria refatorar com NumPy para escalar a 100K+.

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
2. **EDA** (Prompt 02, AGENT-B + SKILL-04) — schema validado, formato ISO 8601 (YYYY-MM-DD) confirmado, win rate 55-70% medido
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
| 1 | Assumiu formato de data ISO na 1ª versão sintética; ao migrar para os dados reais, confirmei ISO 8601 e travei `format='%Y-%m-%d'` | Parsing explícito no `score_pipeline`, sem inferência silenciosa |
| 2 | Sugeriu peso 5% para win rate do agente | Elevei para 15% baseado na EDA (win rate real 55-70%) |
| 3 | Gerou `st.selectbox("Vendedor", ["Option 1"])` hardcoded | Corrigido para ler `df.unique()` em runtime |
| 4 | Não tratou edge case `engage_date=NaT` em abertos | Spec E1 definiu velocity=0 com label específico |
| 5 | `use_container_width=True` deprecated | Substituído por `width="stretch"` (sintaxe Streamlit 1.59+) |
| 6 | Label de agente novo mascarava caso "sem histórico" | Spec E5: label explícita "novo, sem histórico ainda" |
| 7 | `score_deal` reconvertia data dentro do apply (lento) | Movida para caller `score_pipeline` conforme SPEC seção 6 |
| 8 | `color_discrete_map` só cobria 2 stages | Adicionei Won/Lost para robustez futura |
| 9 | `NaN or 0` não zerava contas sem cadastro → `min(cap, NaN)` do Python devolvia o cap e dava score de conta máximo indevido | Coerção NaN-safe (`_num`/`_minmax`) tratando None/NaN como 0 |
| 10 | `GTXPro` no pipeline não casava com `GTX Pro` do catálogo (data quality real) → `sales_price` NaN | Normalização do nome antes do merge |

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

# Os 4 CSVs reais do challenge já estão em solution/data/.
# Para rebaixá-los do Kaggle (CC0, sem credenciais):
#   curl -sL -o crm.zip \
#     "https://www.kaggle.com/api/v1/datasets/download/agungpambudi/crm-sales-predictive-analytics"
#   unzip -o crm.zip -d data/

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