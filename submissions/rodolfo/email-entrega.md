**Assunto:** Submissão Challenge 001 — Diagnóstico de Churn | Rodolfo

---

Prezado time G4,

Segue a formalização da minha submissão ao **Desafio 001 — Diagnóstico de Churn** para a vaga de AI Master.

### O que foi entregue

Uma plataforma completa de diagnóstico, predição e prescrição de churn para a RavenStack (SaaS B2B), desenvolvida com **Spec-Driven Development** e deployada em produção no Railway.

**Link do dashboard:** https://churn-platform-production-8bea.up.railway.app

**Link do PR:** https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/87

**Stack utilizada:** Python 3.12, FastAPI, Pandas, Docker, Railway, OpenCode (LLM on-demand)

### Funcionalidades implementadas

- **Pipeline ETL** com 5 fontes de dados, schema validation e merge automático
- **Health Score** com 4 pilares (Usage, Support, Engagement, Financial) e 5 tiers de risco
- **REST API** com endpoints para execução do pipeline, listagem de contas em risco e explicação narrativa por conta
- **Dashboard corporativo** com identidade visual G4 (tema dark, acentos dourados), KPIs executivos, distribuição de health score, tabela priorizada de contas em risco e explicador LLM
- **Infraestrutura em produção** via Railway com Docker, health check e cron semanal
- **Integração com OpenCode** para geração de narrativas em linguagem natural, com cache de 24h e fallback semântico
- **19 testes automatizados** validando todos os componentes

### Resultados principais

A RavenStack apresenta **22% de churn rate** — 110 contas perdidas representando **$254.952/mês de MRR perdido**. Das 390 contas ativas, **85 estão em risco** (tiers Critical/At Risk), totalizando **$4.400/mês de MRR ameaçado**. O Health Score identificou que 60% das contas em risco têm queda significativa de uso como principal sintoma.

### Próximos passos (já especificados)

- **SPEC-6**: Modelagem preditiva com XGBoost
- **SPEC-7**: Survival Analysis (Kaplan-Meier + CoxPH)
- **SPEC-8**: Causal Inference & Uplift Modeling
- **SPEC-9**: Intervention Playbook automatizado

---

Estou à disposição para **apresentar a solução em uma call**, passando pela arquitetura, decisões de design, resultados e demonstrando o dashboard ao vivo. Posso também abordar como aplicaria a mesma abordagem em outros desafios de negócio.

Aguardo retorno.

Atenciosamente,

**Rodolfo**

rodolfo@dtsqd.com
