# Prompt — Iteração 03 · Causa raiz, coortes e economia do onboarding

Transcrição fiel do prompt recebido pelo agente executor desta iteração (arquivado por evidência de processo, conforme regra de governança).

---

Você é o AGENTE EXECUTOR ÚNICO da ITERAÇÃO 03 — Causa raiz, coortes e economia do onboarding — de uma submissão real ao G4 AI Master Challenge. Esta é a análise central. Trabalhe em duas fases com hipóteses versionadas ANTES de analisar. NÃO avance para watchlist/lifecycle operacional (It04), recomendações finais (It05) ou relatório executivo final (It07).

REPO/BRANCH/ESCOPO
- Repo `/tmp/opencode/ai-master-challenge-work`; branch `submission/jose-nascimento`; pasta única permitida `submissions/jose-nascimento/`; HEAD esperado `6e7be698c484a6c80f41b45d59b4f3ab4a8ddf67`.
- Leia instruções oficiais, plano/checklist, todo o histórico It00–It02, contrato congelado `solution/docs/analytical-contract.md`, reports/evidence e scripts 01–02.
- NÃO leia/use os reports de pesquisa em `/home/ubuntu/aimaster_local` ou `/tmp/opencode/angle-research` como fonte desta execução. Toda hipótese/número/conclusão deve nascer do brief + contrato + CSVs pela solução própria.

FASE A — HIPÓTESES ANTES DA ANÁLISE (OBRIGATÓRIA)
1. Antes de rodar qualquer query exploratória nova sobre resultados de negócio, escreva `process-log/hypotheses/iteration-03-root-cause-hypotheses.md`. Para cada hipótese: pergunta, métrica/fonte/grão, teste falsificável, threshold/critério de decisão antes de ver o resultado, confundidores, resultado possível se refutada. Cubra no mínimo: composição/tenure; coortes; uso total vs per-account; suporte; segmentos (industry/channel/tier/trial); confiabilidade CSAT/reasons; economia de onboarding/CAC-equivalent.
2. Registre claramente que são hipóteses, não conclusões. Arquive este prompt em `process-log/prompts/iteration-03-prompt.md` já nesta fase.
3. Faça commit e push ANTES de implementar/rodar o script analítico: `docs: define churn hypotheses before analysis`. Registre hash/horário. Não amend depois; qualquer ajuste vira adendo datado, nunca reescrita retroativa.

FASE B — EXECUÇÃO DA ANÁLISE
4. Implemente script mínimo `solution/src/03_root_cause.py`, offline, paths relativos, deterministicamente gerando:
   - `solution/evidence/03_root_cause_report.md`;
   - tabelas CSV pequenas em `solution/out/tables/` necessárias para auditabilidade;
   - 4–6 gráficos PNG legíveis em `solution/out/charts/`, com títulos/unidades/fontes, sem decoração genérica;
   - se necessário, dados intermediários regeneráveis, mas evite duplicação pesada.
5. Teste as hipóteses sem forçar o resultado. A análise deve incluir:
   A. Série mensal 2023–2024: eventos e contas únicas; taxa com denominador elegível/ativo conforme contrato; gross subscription ending MRR e net account-state loss separados; decomposição do spike por tenure/coorte.
   B. Coortes: signup month/quarter e tempo até primeiro evento; trate censura no corte 2024-12-31. Implemente Kaplan–Meier descritivo sem nova dependência (ou método equivalente correto), mostrando at-risk e distinguindo taxa observada de estimativa censurada. Não compare Q4 com janela completa sem nota.
   C. Onboarding: primeiras janelas 30/60/90 dias por conta e por subscription, denominadores elegíveis; quantifique exposição contratual bruta precoce, não a chame automaticamente de receita perdida. Para CAC, o dataset não contém custo: use apenas cenários explicitamente nomeados `CAC-equivalent exposure` (ex. múltiplos de MRR) e análise de sensibilidade, nunca claim factual de CAC queimado.
   D. Uso: teste a frase "uso cresceu" separando volume total de intensidade por conta elegível; exclua registros pré-signup no cenário primário, faça sensibilidade; features pré-index somente. Não use atividade pós-churn como preditor.
   E. Suporte: sinais pré-index (tickets, escalação, response/resolution observáveis, CSAT somente fechados) com denominadores; respeite `closed_at` e política anti-leakage.
   F. Segmentos: industry/channel/tier/trial com N, eventos/contas, taxa ou sobrevivência, gross ending MRR; use mínimo de amostra/intervalos ou flags de instabilidade. Não rankeie apenas por contagem.
   G. Reasons/feedback/CSAT: quantifique independência/inconsistência e missingness; trate como evidência sugestiva. Não transformar reason_code em causa.
   H. Correlação vs causalidade: tabela de cada achado → associação observada → confundidores/alternativas → status (`descritivo`, `hipótese causal plausível`, `não identificável`) → dado adicional necessário.
6. Para sinais pré-evento, use desenho honesto: primeiro churn por conta; janelas antes da data índice; controles comparáveis por calendar time/tenure/tier quando viável. Se dados sintéticos ou temporais impedirem inferência, mostre o NO-GO com números. Evite modelo preditivo/ML.
7. Declare uma causa raiz operacional SOMENTE se sustentada por múltiplas evidências; se for composição de coorte/onboarding, demonstre mecanismo e tamanho. Separe "o que sabemos" de "o que ainda é hipótese". Qualquer convergência com análise pública é coincidência rederivada — use fraseado/estrutura próprios.
8. Inclua pelo menos 3 verificações manuais independentes com IDs/meses/cálculos: decomposição de um mês; uma conta early-event; um segmento/sinal. Valide números-chave com implementação independente do script.
9. Robustez: análise de sensibilidade para definições (event vs subscription, 30/60/90d, registros temporais válidos vs todos); intervalos/denominadores; zero divisão; censoring; múltiplos eventos não viram múltiplos logos.
10. Evidência/processo:
   - `process-log/reports/iteration-03-root-cause-report.md`: workflow, hipótese→resultado→decisão, erros reais/correções, alternativas, validações, limitações, handoff It04;
   - se decisões merecerem: `process-log/decisions/iteration-03-root-cause-decisions.md`;
   - preserve hipóteses originais; não invente erros.
11. Atualize plano/checklist: It03 `CONCLUDED` só após validação; gate 3x `PENDING`; futuras `PENDING`.
12. Valide baseline 2x e checksum de todos outputs; execute de CWD diferente; teste FAIL estrutural sem report stale/traceback; confira gráficos abrem/dimensões/labels; syntax/import; números report↔CSV; `git diff --check`; paths/segredos; escopo/Markdown/links.

CONTENÇÃO
- Sem ML/dashboard/app/Notion/PDF. Sem recomendações finais ou watchlist top-20 nesta etapa.
- Não adicionar dependência se stdlib+pandas+matplotlib/seaborn bastam.
- Gráficos devem responder perguntas, não preencher espaço.

GIT FASE B
- Antes do commit final: status/diff/log; só pasta permitida.
- Commit: `feat: diagnose churn root cause and cohort dynamics`.
- Sem amend/force/config/destrutivo. `git add -f` paths pretendidos; push; valide local==remote/tree limpo.

CRITÉRIOS DE ACEITAÇÃO
- Hipóteses commitadas antes do código/resultados.
- Causa raiz sustentada ou honestamente não identificável; spike decomposto; coortes censuradas corretamente; economia do onboarding parametrizada; sinais de uso/suporte sem leakage; segmentos com denominador; causalidade delimitada.
- Outputs regeneráveis, 4–6 gráficos, 3 checks manuais, sensibilidades, processo real, commits/push.

REPORT FINAL AO ORQUESTRADOR
Status PASS/BLOCKED; dois hashes/push; timeline provando hipóteses antes; síntese de cada hipótese (sustentada/refutada/inconclusiva) com números; causa raiz e nível de certeza; gráficos/tabelas; checks/sensibilidades; erros reais; validações; riscos e handoff It04. Use BLOCKED se censoring/leakage/denominadores não estiverem resolvidos.