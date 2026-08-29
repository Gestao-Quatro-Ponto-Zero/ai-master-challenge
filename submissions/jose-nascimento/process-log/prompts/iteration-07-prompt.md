# Prompt integral — Iteração 07 (relatório executivo final e narrativa CEO)

Arquivado em 2026-08-29 pelo executor antes da implementação (prática das
Iterações 01–06). Texto integral recebido pelo agente executor:

---

Você é o AGENTE EXECUTOR ÚNICO da ITERAÇÃO 07 — relatório executivo final e narrativa CEO — do G4 AI Master Challenge. Transforme outputs validados em uma entrega concisa, acionável e reproduzível. NÃO finalize ainda process log/checklists/PR (It08–10).

REPO
- `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD `fa6572f2913e0c001099b24993a7b4bc9634cb37`.
- Leia instruções oficiais/template, contrato/evidence/reviews/fixes It01–06, action plan, watchlist/tables, os 6 gráficos finais e README atual. Não leia/cite pesquisas externas/concorrentes.

FASE A — OUTLINE ANTES DA REDAÇÃO
1. Crie `process-log/decisions/iteration-07-executive-report-outline.md` ANTES do gerador, com estrutura, 1 mensagem central, 3 provas, ask executivo, claims permitidos/proibidos, gráficos/tabelas escolhidos, word budget (alvo ~1.500–2.000 palavras no report; README curto), critérios de CEO-readability. Arquive prompt em `process-log/prompts/iteration-07-prompt.md`.
2. Commit/push separado antes do relatório: `docs: define executive report narrative`. Não reescreva esse outline retroativamente; adendo se reviews exigirem.

FASE B — REPORT GERADO E README
3. Implemente `solution/src/07_generate_executive_report.py`, paths relativos/offline/determinístico, que lê CSVs/evidence validados e gera `solution/report-executivo.md`. Números materiais devem vir dos inputs em runtime, com gates; não copiar manualmente.
4. Estrutura obrigatória do relatório (Português, pyramid principle/answer first):
   - **Executive summary + decisão solicitada**: 250–350 palavras, causa operacional, tamanho, incerteza, 2 ações Now e ask explícito;
   - **Como medimos churn**: reconcilie 110 snapshot vs 486 subs/312 contas vs 600 eventos/352 contas; lente por pergunta; sem misturar;
   - **O que mudou / causa raiz**: 43 primeiros eventos/191 elegíveis=22,51% em dez/24 vs mediana 13,01% 6m; deixe claro que todos episódios em dez=117 e que 43 é hazard de primeiro evento; composição 0–3m 83,7%; R1 ≤90d 68,4%; KM/censura; status `hipótese causal plausível`, não prova;
   - **O que não explica**: uso total +225,3% vs intensidade mediana 0%; H4 corrigido; suporte/CSAT/reasons sem discriminação/confiabilidade; evita narrativa falsa;
   - **Segmentos e contas**: lifecycle states, não industry; 80 onboarding atuais / 621.981 winner MRR; top20 operational priority 392.030 (10,7%), 8 onboarding validados + 12 exposure-only; mostre 8–10 account_ids específicos e link para CSV completo, com MRR/evidência/limitação;
   - **Ações priorizadas**: ACT-03 instrumentação Now/SLA30d → ACT-01 experimento; ACT-02 triage em paralelo; ACT-04 Later. Owner, prazo, first signal, métrica e stop/go 3 estados;
   - **Impacto em faixa**: 2,7/6,9/13,0 eventos afetados; 21.104/53.497/101.078 US$ de MRR-equivalent exposure em 90d, com premissas/range vs CI; NÃO revenue saved/forecast;
   - **Não fazer agora**: ML/score, descontos amplos, reason/CSAT como causa, automação sem holdout;
   - **Limitações e próximos dados**: sinteticidade/decoupling, all-active, proxies, baixo power;
   - **Reprodução/evidence map**: `./run.sh`, runtime aproximado, links relativos para contrato/evidence/tabelas/process log.
5. Embed exatamente os 6 PNGs necessários, com paths relativos corretos, caption com takeaway (não repetir fonte minúscula). Nenhum gráfico novo; nenhum PDF/HTML/Notion.
6. Tabelas compactas (máximo necessário): lentes; 3 evidências; contas específicas; ações; impacto/assumptions; causal status/evidence map. Evite 40 páginas/parede de números. O relatório deve ser compreensível sem abrir código, mas auditável por links.
7. Atualize `submissions/jose-nascimento/README.md` usando o template oficial como índice executivo:
   - Sobre mim (Nome; LinkedIn: `não informado` se não fornecido — nunca placeholder inventado; Challenge 001);
   - Executive Summary 3–5 frases + decisão pedida;
   - Solução/Abordagem/Resultados/Recomendações/Limitações em resumo, links para report, run, contract, watchlist, process log;
   - tabela de ferramentas/orquestração já correta — preserve/integre, não apague;
   - Workflow/process/evidências ainda podem apontar para artefatos existentes, mas não marque itens finais como concluídos antes It08/09;
   - data de submissão fica `pendente` até It10.
8. Integre pipeline: `run.sh` executa scripts 01–05, depois gerador 07, depois verifier 06. Atualize Makefile/solution README/verifier/manifests/contagens de forma derivada; fresh clone deve regenerar `report-executivo.md` byte-idêntico e manter exatamente 6 PNGs. Não renomeie verifier.
9. Gates do gerador/verifier:
   - todos números-chave report==tables;
   - claims proibidos em contexto afirmativo zero;
   - links relativos existem; exatamente 6 imagens e cada uma usada uma vez;
   - word count dentro do budget razoável; contas do report subset da t16; ação/impacto consistente t18/t19/t20;
   - report não menciona concorrentes/pesquisa interna/baseline copiado.
10. Validações: run 2×/CWD/fresh clone; deterministic outputs/tree clean; Markdown headings/links/images/tables; 6 PNGs inspeção programática; 3 spot checks manual independente; FAIL input ausente sem report stale; no new dependency.
11. Evidência: report `process-log/reports/iteration-07-executive-report.md` com timeline 2 commits, decisões, word count, links, checks, erros reais, validações, riscos/handoff It08. Atualize plano/checklist It07 CONCLUDED/gate3x PENDING, futuras PENDING.

ESTILO
- Direto, sem marketing, sem emoji, sem jargão desnecessário. Cada claim = número + definição/limite. "Churn precoce" não é causalidade provada. Use US$ conforme dados; não converta BRL.

GIT FASE B
- Commit `docs: deliver executive churn diagnosis`; push; local==remote/tree limpo; somente pasta; sem amend/force/config/destrutivo.

ACEITAÇÃO
- Responde integralmente causa raiz, segmentos/contas, ações/impacto; CEO entende/age; 6 gráficos legíveis; report reproduzível; README completo; honestidade estatística; process/git.

REPORT FINAL
PASS/BLOCKED; 2 hashes/timeline; mensagem central/ask; word count; números/churn lenses/accounts/actions/impact; pipeline fresh clone; link/image gates; errors; risks/handoff It08. BLOCKED se qualquer número divergente ou claim de receita/causalidade indevida.

---