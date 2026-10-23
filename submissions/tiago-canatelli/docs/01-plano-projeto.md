# 01 · Plano de Projeto — Diagnóstico de Churn RavenStack

> Challenge 001 · AI Master Challenge (G4) · Documento vivo, iniciado em 2026-10-23.
> Este plano faz parte do process log: registra como o problema foi entendido e decomposto **antes** de qualquer execução.
> Complementos: [02-plano-tecnico.md](02-plano-tecnico.md) · skills em `../.claude/skills/`.

---

## 1. Contexto e problema de negócio

A RavenStack (SaaS B2B, ~500 contas, assinaturas mensais/anuais) viu o churn subir. Três áreas dão leituras que não fecham:

| Área | Afirma | O que pode estar escondendo |
|---|---|---|
| Financeiro | "O churn subiu" | Churn de **logos** ≠ churn de **receita**: poucas contas grandes podem pesar mais que muitas pequenas |
| CS | "A satisfação está ok" | Média esconde distribuição; quem cancela pode **não responder** a pesquisa; escalações e tempo de resposta pioram antes do churn |
| Produto | "O uso cresceu" | Efeito mix / Paradoxo de Simpson: o total sobe com contas novas ou um segmento, enquanto o uso **por conta** cai em outros |

**Pergunta do CEO:** "O que está acontecendo de verdade?"

## 2. Objetivos

| # | Objetivo | Como medimos que foi atingido |
|---|---|---|
| O1 | Explicar a **causa raiz** do churn, cruzando as 5 tabelas | Cada causa tem número, janela temporal e teste de causalidade documentado |
| O2 | Identificar **segmentos e contas específicas** em risco | Lista de contas ativas ordenada por MRR em risco, com motivo |
| O3 | Recomendar **ações priorizadas** com impacto estimado | Cada ação tem dono, métrica, prazo e MRR recuperável estimado |
| O4 | Deixar uma **ferramenta que o CS e o CEO usem amanhã** | Painel + assistente de IA consultável, com prompts prontos e editáveis |
| O5 | Documentar a jornada com IA (obrigatório) | Process log completo no template de submissão |

## 3. Escopo

**Dentro**
- Data lake no Supabase (landing raw + camadas bronze/silver/gold) com ingestão auditável
- Catálogo de dados e qualidade de dados
- Views de KPIs na camada gold
- Monorepo com deploy no Render (dashboard, API do assistente + MCP, cron de ingestão)
- Painel React: acompanhamento da ingestão, catálogo, dashboards de KPI, fila de contas em risco
- Assistente de IA no painel, conectado ao Claude e preparado para outros provedores (OpenAI, Gemini, compatíveis), com biblioteca de prompts editáveis, que responde com o **porquê** e os números
- MCP aberto para Claude e outras IAs (ChatGPT, Cursor, Gemini CLI…)
- RAG sobre as análises (hipóteses, KPIs, catálogo, qualidade, relatório) com busca híbrida e citações
- Experiência de uso cuidada (skill `react-ux-engineer`)
- 8 perfis de análise por área (Executivo, Financeiro, CS, Suporte, Produto, Marketing, Vendas, Dados), personalizáveis, cada um com sua base de RAG, e **análise 360** que cruza as lentes
- Painéis em três camadas: geral, por área e por persona de cliente
- Modelo preditivo de risco de churn
- Relatório de diagnóstico para o CEO + README de submissão + PR

**Fora**
- Integração com sistemas reais (CRM, billing) — dataset é público e sintético
- Autenticação multiusuário complexa (um login simples basta)
- Envio automático de e-mails ou mensagens a clientes

## 4. Stakeholders e personas

| Persona | Precisa de | Entregável que atende |
|---|---|---|
| CEO (não técnico) | Entender o porquê e decidir em 10 minutos | Relatório executivo de 1 página + dashboard CEO |
| Head de CS | Saber **quem** ligar esta semana e o que dizer | Fila de contas em risco + playbook + assistente |
| Head de Produto | Saber se o "uso cresceu" é real e onde não é | Dashboard de uso por segmento e por feature |
| Financeiro | Previsibilidade da receita, refunds, concentração | Painel e perfil Financeiro |
| Suporte | Se o atendimento segura ou empurra clientes | Painel e perfil Suporte |
| Marketing | Que canal traz clientes que ficam | Painel e perfil Marketing |
| Vendas | ICP, plano e licenças a priorizar | Painel e perfil Vendas |
| Avaliadores G4 | Ver profundidade, julgamento e uso inteligente de IA | Process log, git history, diário de hipóteses |

## 5. Perguntas de negócio → indicadores

| Pergunta | KPIs (definidos na skill `churn-business-analyst`) |
|---|---|
| Quanto estamos perdendo? | Logo churn rate, Gross MRR churn, GRR, NRR, MRR perdido por mês |
| Quem está saindo? | Churn por plano, indústria, país, canal, trial vs pago, faixa de MRR, tempo de casa |
| Por que estão saindo? | Motivo declarado × comportamento (uso, erros, tickets) nos 30/60/90 dias antes |
| A satisfação está mesmo ok? | CSAT médio **e** taxa de resposta, FRT, tempo de resolução, % escalado — churners vs ativos |
| O uso cresceu para todos? | Uso por conta ativa por segmento/mês, adoção por feature, taxa de erro, uso de beta |
| Quem vai sair em seguida? | Score de risco × MRR = **MRR em risco**, por conta e por segmento |
| O que fazer primeiro? | MRR recuperável estimado ÷ esforço da ação |

## 6. Fases e cronograma

Budget recomendado pelo desafio: 4–6h. O escopo acima soma ~8h; por isso há **cortes pré-definidos** (seção 8).

| Fase | Entregáveis | Skill principal | Timebox |
|---|---|---|---|
| F0 · Setup | Fork + branch, projeto Supabase, dados do Kaggle, estrutura de pastas | engenharia | 30 min |
| F1 · Planejamento + skills | Este plano, plano técnico, skills | todas | 45 min |
| F2 · Ingestão e lake | raw → bronze → silver, registro de execuções, catálogo, data quality | cientista de dados + engenharia | 1h |
| F3 · Diagnóstico | Diário de hipóteses com veredito e números; causa raiz | cientista de dados + business | 2h |
| F4 · Gold + modelo | Views de KPI, `account_360`, score de risco | cientista de dados | 1h |
| F5 · Painel + IA | Painel React (ingestão, catálogo, KPIs, risco, assistente), MCP, prompts | engenharia | 1h30 |
| F6 · Relatório + submissão | Relatório CEO, README no template, process log, PR | business + process log | 1h |

**Marcos:** M1 dados no silver com DQ verde · M2 causa raiz com números · M3 painel mostrando gold · M4 PR aberto.

## 7. Papéis: humano × IA

| Atividade | IA faz | Eu (humano) decido/verifico |
|---|---|---|
| Hipóteses | Sugere hipóteses e queries | Escolho quais testar, descarto as óbvias, cobro o teste de causalidade |
| Código (pipeline, SQL, React, MCP) | Gera e refatora | Reviso, rodo testes, valido números contra o CSV |
| KPIs | Propõe fórmulas | Fixo as definições de negócio (ex.: o que conta como churn, reativação) |
| Relatório | Rascunha | Corto, priorizo por $, garanto que o CEO entende |
| Process log | Lembra de registrar | Escrevo os erros da IA e o meu julgamento |

## 8. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Estourar o budget com infra | Análise rasa | Timebox por fase; cortar nesta ordem: (0) perfis além de Executivo/CS/Produto/Suporte saem só com instruções e prompts de fábrica, sem painel próprio; análise 360 sem upload de documentos, (1) outros provedores ficam só preparados (adaptador + teste), sem avaliação comparativa, (2) RAG só com hipóteses e feedback, (3) modelo vira regras de score, (4) MCP só pelo painel, (5) catálogo vira página estática. **Diagnóstico e relatório não encolhem** |
| Projeto Supabase free pausar por inatividade | Bloqueia testes e o painel | Reativar antes de trabalhar; tudo roda no Supabase SaaS (sem ambiente local) |
| Migration errada no único ambiente | Dados ou schema quebrados | Migrations pequenas e versionadas; destrutivas só com confirmação; reingestão reconstrói tudo a partir do `raw/` |
| Dataset sintético com sinais fracos | Conclusões frágeis | Dizer isso com clareza no relatório; reportar efeitos com intervalo/tamanho de amostra |
| Confundir correlação com causa | Recomendação errada | Checklist de causalidade obrigatório (skill do cientista de dados) |
| Leakage no modelo | Modelo "perfeito" e inútil | Snapshot temporal; features só até a data de corte |
| Resposta parecida com o baseline das IAs | Reprovação | Cruzar as 5 tabelas, achar o paradoxo, entregar ferramenta usável, process log honesto |
| Segredos no git (chaves Supabase/Anthropic) | Vazamento | `.env` fora do git; chave de IA só como env var secreta no Render |

## 9. Critérios de aceite (definição de pronto)

- [ ] As 5 tabelas aparecem cruzadas em pelo menos uma conclusão principal
- [ ] Todo claim do relatório tem número e a query/view de origem
- [ ] Toda causa apontada passou pelo checklist de causalidade (ou está marcada como hipótese)
- [ ] Lista de contas específicas em risco com MRR
- [ ] 3–5 ações com dono, métrica, prazo e impacto estimado em MRR
- [ ] Painel rodando com instruções de setup
- [ ] README segue o template; process log com ferramentas, workflow, erros da IA e minha contribuição
- [ ] PR com título `[Submission] Tiago Canatelli — Challenge 001`, só alterando `submissions/tiago-canatelli/`

## 10. Decisões abertas

| Decisão | Opções | Recomendação |
|---|---|---|
| Projeto Supabase | ✅ Decidido: projeto `G4-Analysys` (`hzerhfuwziundqqezgcm`, us-east-1), criado em 2026-10-23, vazio | — |
| Dados | Token Kaggle / download manual dos 5 CSVs | Token (reprodutível no README) |
| Hospedagem | ✅ Decidido: monorepo com deploy no Render (dashboard, API/MCP, cron) | — |
| Nome e LinkedIn no README | — | Preciso dessas informações |
| Modelo de embedding do RAG | Voyage AI / OpenAI `text-embedding-3-small` / local (`fastembed`) | Voyage (qualidade, recomendado pela Anthropic) — exige chave |
| Provedores extras no lançamento | OpenAI, Gemini, OpenAI-compatível | Deixar adaptadores prontos; habilitar os que tiverem chave |
| Definição de churn | ✅ Decidido em 2026-10-23: `churn_events` é a fonte de verdade; flags viram achado de qualidade | — |
