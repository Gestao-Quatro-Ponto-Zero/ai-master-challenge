# G4 AI Master Challenge 003 — Lead Scorer

**Author:** Anderson Hirota · [linkedin.com/in/andersonhirota](https://linkedin.com/in/andersonhirota) · anderson@gtmsystemslab.com

## TL;DR

Construí um **Morning Brief opinionado** sobre o dataset de 8.800 oportunidades — não um pipeline browser scoreado. Quem abre o app não navega: age. Manager mode e Rep mode espelham a mesma tese ("brief é brief em qualquer nível"), com action layer bidirecional e composability via JSON export pra downstream agents.

## O que diferencia

- **Dual-mode com manager como player** — não orquestrador. Mesma estrutura de brief opinionado em Rep e Manager mode, com 3 tipos de must-act próprios do manager (closer / intervention / system decision)
- **Action layer bidirecional** — rep e manager AGEM dentro do app. Done/Defer/Skip + outcome notes. Rep escala via 🆘 Request manager help quando precisa de authority. Brief encolhe conforme decisões acontecem. Audit log file-based, exportável
- **LLM-as-judge contextual em duas vozes** — actions citam fatos específicos do deal (account, sector, days remaining, alpha/bleed do rep). Cache + validação contra preamble leak
- **Baseline-then-exceed honesto** — 3 baselines progressivos por autocrítica IA (v1→v2→v3) estabelecem o "teto IA puro". Esta submissão se mede contra ele

## Como rodar

```bash
cd solution/
pip install -r requirements.txt
streamlit run app.py
```

App em `http://localhost:8501`.

**LLM dependency:** todas as actions LLM-judged já estão pré-geradas em `solution/.judge_cache/`. **Você não precisa de Claude CLI nem ANTHROPIC_API_KEY pra avaliar o demo.** As únicas features que chamam LLM ao vivo são o "Generate" do Call Prep e o Regenerate — sem CLI degradam graciosamente. Decisão consciente: cache resolve 99% do demo, migração pra API seria risco grande horas antes do PR.

## Onde ir fundo

- **Profundidade técnica + narrativa de processo:** [`solution/README.md`](solution/README.md) — executive summary, 9 diferenciadores explicados, mapping pro Anthropic playbook (Eleanor Dorfman, SaaStr 2026), limitações honestas, process log completo (bugs encontrados, calls de design, gaps descobertos em revisão)
- **Evidências do baseline-then-exceed:** [`process-log/`](process-log/) — baselines v1/v2/v3 (outputs verbatim de cada iteração de IA pura) + `differentiation-rubric.md` (contrato escrito antes da Fase C)

## Stack

Streamlit · Python · Pandas · Claude CLI (LLM-as-judge). 6 módulos: `app.py`, `scoring.py`, `judge.py`, `manager.py`, `coaching.py`, `actions.py`.
