# Submissão — Gabriel Sudré — Challenge 003

> **Acesse a aplicação:** [https://caseg4.bredasudre.com](https://caseg4.bredasudre.com)  
> Login com qualquer e-mail via OTP. Documentação técnica: [docs/DOCS.md](docs/DOCS.md)

## Sobre mim

- **Nome:** Gabriel Breda Sudré
- **LinkedIn:** [www.linkedin.com/in/gabriel-breda-sudre](https://www.linkedin.com/in/gabriel-breda-sudre)
- **Challenge escolhido:** 003 — Lead Scorer

## Executive Summary

Construí uma plataforma web de priorização de oportunidades de vendas para um time de 35 vendedores distribuídos em escritórios regionais. A solução usa um *scoring engine* com 8 *features* ponderadas (*sigmoid*, *log scale*, *confidence weighting*) para classificar 2.089 oportunidades ativas em zonas de prioridade, integra IA (GPT-4o-mini) para explicações e recomendações acionáveis, e oferece um chat assistente com contexto completo do pipeline. A principal recomendação é que o vendedor abra a ferramenta segunda-feira de manhã, veja o "Foco Hoje" e saiba exatamente onde investir tempo, sem depender de intuição ou análises manuais. 

Toda a explicação do Score é fornecida diretamente no card do Deal, além de uma opção para comparar com outros Deals e ver qual deles faz mais sentido e por quê. A aplicação foi desenvolvida com Supabase como *Backend* para facilitar uma possível escalação futura e integração com uma ferramenta de CRM. Por se tratar de uma aplicação beta, todos os usuários logados automaticamente assumem a *rule* de admin (as demais *rules* do sistema já estão configuradas).

---

## Solução

1. **Análise dos dados primeiro**: Antes de codar, analisei a proposta e os 4 CSVs com o Claude Code, justamente para conseguir definir uma estratégia mais clara para completar o desafio. Fiquei cerca de 50 minutos na fase de planejamento de estratégia e arquitetura e, durante essa etapa, identifiquei inconsistências (*typos*, 1.425 deals sem conta), distribuições de *stages*, *win rates* homogêneos (61-65% em todos os setores) e preços com *range* extremo (R$ 55 a R$ 26.768). Isso definiu as decisões de normalização.

2. **Scoring iterativo (4 versões)**: A v1 comprimia scores entre 30-61. Identifiquei os problemas (*sigmoid cliff*, *min-max* dominado por *outlier*), corrigi com *log scale* e *sigmoid* suave (v2), validei com agente externo que identificou *feedback loop* e *features* duplicadas, e implementei correções finais (v3/v4). Basicamente, para definir o score, criei uma v1 simples e, depois de implementada, fui utilizando agentes externos (sem contexto) para avaliar a lógica. Todos os resultados dessas análises eu passei ao agente principal e aplicamos o que fazia sentido.

3. **Arquitetura de produção**: Comecei com Streamlit para validar a estrutura (rápido, mas travado com 2.089 deals) e migrei para React + FastAPI + Supabase. A decisão custou um retrabalho, mas entregou uma ferramenta que um vendedor não técnico consegue usar e sem gargalos. A ideia de disponibilizá-la via WEB (VPS da Hostinger + Supabase Cloud) foi justamente para abstrair a necessidade de usuários não técnicos terem que instalar dependências e ferramentas para o funcionamento correto.

4. **IA como camada de valor, não de decisão**: O *scoring* é determinístico e explicável. A IA adiciona linguagem natural, recomendações de próximos passos e chat, mas não substitui a lógica. O ideal seria que tivesse uma descrição dos produtos e empresa para criar um RAG vetorial para a IA auxiliar no fechamento, dando sugestões mais alinhadas ao produto; no entanto, vejo como uma possível *feature* futura.

### Resultados / Findings

- **2.089 oportunidades ativas** com score (range 38-78, média 51.6).
- **8 features de scoring** com pesos validados por agente externo independente.
- **16 componentes React** com *dark/light mode*, comparação *side-by-side* e *health score* do pipeline.
- **13 endpoints API** autenticados com CRUD completo.
- **3 roles** (admin/vendedor/manager) com visibilidade controlada via RLS.
- **22 testes de validação** (10 *scoring* + 12 *pipeline*) passando.
- **Chat IA** com contexto completo: métricas, zonas, *top deals*, distribuições e critérios de score.
- **Deploy**: Docker + EasyPanel na Hostinger.
- **Tempo total**: 4h37min de desenvolvimento ativo.

### Recomendações

1. Conectar a um CRM real (Salesforce, HubSpot) para dados em tempo real, visto que o dataset estático é a principal limitação.
2. Teste A/B dos pesos de *scoring* com dados de conversão real do time.
3. Adicionar *feature* de velocidade do deal (Prospecting → Engaging) quando o dado de criação estiver disponível.
4. Implementar notificações automáticas para deals em risco (*aging* acima do limiar).

### Limitações

- Dataset estático com dados antigos (2016-2017). O *scoring* foi calibrado para esse período com o `REFERENCE_DATE` configurável para produção.
- *Win rates* homogêneos (61-65%) limitam a diferenciação por setor/produto. Trata-se de uma limitação do dataset, não do modelo.
- 68% dos deals ativos sem conta definida, o que resultou em uma penalização do *scoring*, perdendo a eficácia de `account_fit`.
- Cache em memória, por se tratar de uma aplicação com dados estáticos. Para produção, o ideal seria utilizar o Redis.

---

## Process Log — Como usei IA

> **Este bloco é obrigatório.** Sem ele, a submissão é desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Opus 4) | Arquitetura, implementação completa (backend + frontend), debugging, validação |
| OpenAI GPT-4o-mini | Runtime na aplicação: explicações de deals, recomendações, chat assistente |
| Agente externo (via prompt) | Validação independente da lógica de scoring — revisão crítica com 8 ações prioritárias |
| Supabase | Banco de dados PostgreSQL, autenticação OTP, Row Level Security |
| Vite + React + Tailwind | Frontend SPA com TypeScript |
| FastAPI | Backend API REST |
| Recharts | Gráficos do dashboard |

### Workflow

1. **Discussão de arquitetura (45min):** Analisei o challenge, debati *stack* (Streamlit vs React, CSV vs Supabase, local vs cloud), defini *scoring* com 9 *features* iniciais e documentei em `infraestrutura_base.md`.
2. **Setup Supabase (40min):** Criei schema com FKs *surrogate*, importei CSVs e validei a integridade dos dados.
3. **Scoring engine v1-v4 (1h30):** Implementei, testei, identifiquei compressão, corrigi fórmulas, enviei para validação externa e implementei correções e ajustes.
4. **Interface (2h):** Comecei com Streamlit para testes visuais (funciona, mas trava muito), migrei para React + FastAPI e implementei dashboard com gráficos, pipeline com zonas, histórico e chat flutuante.
5. **Refinamentos (40min):** Pedi ao Claude para seguir a mesma linha de DS do site do G4; implementei *dark mode*, CRUD de deals, comparação *side-by-side*, *health score*, *guardrails* de IA, traduções PT-BR e ícones Lucide.

### Onde a IA errou e como corrigi

1. **Scoring comprimido (v1):** A IA implementou *min-max* simples, fazendo com que o GTK 500 (R$ 26.768) dominasse o `potential_value`; 95% dos deals tinham `aging=0`. Corrigi com *log scale* e *sigmoid* baseado em mediana dos deals ativos.
2. **Feature duplicada:** `product_price_tier` era cópia idêntica de `potential_value`, ou seja, 5% do peso era desperdiçado. Detectado por agente externo e removido.
3. **Import via porta errada:** A IA tentou a porta 5432 (*transaction mode* do PgBouncer), que cancelava *statements*. Diagnostiquei e mudei para 6543 (*session mode*).
4. **Feedback loop no agent_performance:** Vendedores com *win rate* baixo recebiam scores piores → focavam em menos deals → perdiam mais. Corrigido reduzindo o peso de 12% para 5% e simetrizando.
5. **agent_load penalizava produtividade:** Lógica invertida (menos deals = melhor) premiava vendedores ociosos. Corrigi para desvio da média.
6. **Colunas fantasma no /api/init:** Após colapsar *features*, o endpoint ainda referenciava colunas antigas. Corrigido na auditoria final.

### O que eu adicionei que a IA sozinha não faria

1. **Decisão de Supabase centralizado:** A IA sugeriu CSV local. Identifiquei que 35 vendedores precisam de uma fonte única de dados.
2. **Validação externa do scoring:** Enviei um prompt estruturado para um agente independente avaliar a lógica. A IA que construiu o *scoring* não identificaria seus próprios problemas.
3. **Migração Streamlit → React:** Decisão de UX baseada em experiência, não em sugestão da IA.
4. **Design alinhado ao G4:** Extraí cores (*navy/gold*), tipografia (Manrope) e *patterns* do site oficial do G4.
5. **Tradução contextual:** *Won/Lost* → Ganho/Perdido. Decisão de UX para vendedores BR.
6. **REFERENCE_DATE configurável:** Parametrizável via *env var* para cenários de produção vs. avaliação.

---

## Evidências

- [x] **Git history com commits incrementais:** [github.com/G4bsudr3/lead-scorer](https://github.com/G4bsudr3/lead-scorer) — repositório de desenvolvimento com histórico real de commits
- [x] **Chat export completo:** `process-log/chat-exports/session-lead-scorer-2026-03-30.jsonl` — 2.590 linhas da sessão Claude Code (secrets sanitizados), mostrando toda a evolução v1→v4, debugging, decisões e correções
- [x] Screenshots de utilização de IA e infraestrutura (6 capturas)
- [x] Documento de arquitetura iterado: `docs/infraestrutura_base.md`
- [x] Schema SQL versionado: `solution/supabase/schema.sql`
- [x] Process log detalhado: `process-log/PROCESS_LOG.md`
- [x] Testes automatizados: `test_scoring.py` (10 checks) + `test_pipeline.py` (12 checks)
- [x] Aplicação funcional deployada via Docker no EasyPanel

---

## Documentação

- [docs/DOCS.md](docs/DOCS.md) — Documentação técnica completa: setup, **lógica detalhada do scoring (8 fatores, pesos e justificativas)**, funcionalidades, segurança e limitações.
- [docs/infraestrutura_base.md](docs/infraestrutura_base.md) — Documento de arquitetura criado na fase de planejamento (evidência de processo).

---

_Submissão enviada em: 31/03/2026_