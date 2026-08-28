# Prompt — Iteração 02 · Reconciliação das definições/grãos de churn e contrato analítico

Transcrição fiel do prompt recebido pelo agente executor desta iteração (arquivado por evidência de processo, conforme regra de governança).

---

Você é o AGENTE EXECUTOR ÚNICO da ITERAÇÃO 02 — Reconciliação das definições/grãos de churn e contrato analítico — de uma submissão real ao G4 AI Master Challenge. Execute somente esta etapa, sequencialmente, com código, evidência, validações e git. NÃO avance para causa raiz/coortes (Iteração 03) nem recomendações.

REPO/BRANCH/ESCOPO
- Repo: `/tmp/opencode/ai-master-challenge-work`
- Branch: `submission/jose-nascimento`
- Pasta única permitida: `submissions/jose-nascimento/`
- HEAD esperado: `b9823daa6a7c39920066cbccd086c007d5921d28`
- Leia instruções oficiais completas, `execution-plan.md`, checklist, todo material da It00/It01 (reports, prompts, reviews/fixes), `solution/evidence/01_audit_report.md` e os 5 CSVs commitados.
- Não use resultados de `/home/ubuntu/aimaster_local` como fonte; toda decisão/número deve ser rederivado dos CSVs pela solução.

OBJETIVO
Resolver a inconsistência entre `accounts.churn_flag`, `subscriptions.churn_flag/end_date` e `churn_events`, definindo um contrato canônico por pergunta de negócio; construir uma base account-month determinística sem dupla contagem; explicitar regras temporais/leakage; provar invariantes. O produto desta etapa deve permitir as análises posteriores sem misturar métricas incompatíveis.

TAREFAS OBRIGATÓRIAS
1. Inspecione git/status/log/remoto. Atualize status da It02 logicamente `OPEN` durante execução e `CONCLUDED` somente após validação; demais futuras `PENDING`.
2. Implemente `solution/src/02_reconcile_churn.py` (nome previsto ou equivalente) com paths relativos, offline e dependências mínimas. Deve gerar deterministicamente:
   - `solution/evidence/02_consistency_report.md`;
   - `solution/docs/analytical-contract.md`;
   - uma base processada account-month em formato aberto/auditável (CSV), preferencialmente `solution/data/processed/account_month.csv`, somente se sua utilidade justificar o tamanho; caso não commite, explique e forneça geração reproduzível.
3. Reconcilie quantitativamente, no mínimo:
   - contas flagadas em `accounts`;
   - subscriptions encerradas/flagadas e contas únicas;
   - eventos e contas únicas em `churn_events`;
   - interseções/diferenças 35/277/125 auditadas na It01 (recalcule, não copie);
   - alinhamento temporal `churn_date` vs `end_date`: matching documentado, distribuição de lags e sensibilidade a janelas razoáveis;
   - múltiplos eventos/reativações sem contar episódio como logo perdido.
4. Escreva um contrato ANALÍTICO claro, sem fingir que uma fonte resolve tudo. Defina explicitamente:
   - snapshot/data-limite e janela observacional;
   - grão de cada métrica (account, subscription, event, account-month);
   - definição primária para cada pergunta: churn/eventos para diagnóstico, churn de assinatura/receita, status de conta e risco; explique quando NÃO podem ser comparadas;
   - denominadores e fórmulas (logo churn, revenue/MRR churn, activity signal), política de múltiplas subscriptions e regra determinística de "winner"/estado da conta;
   - semântica de intervalos de assinatura (inclusive/exclusive), cancelamento, reativação e sobreposição;
   - política anti-leakage: apenas informações disponíveis antes da data índice; campos/eventos pós-churn proibidos em risco;
   - política para registros temporalmente inválidos detectados na It01 (uso/tickets pré-signup; uso fora da janela da subscription): inclua análise de sensibilidade ou justificativa; não descarte 76,6% silenciosamente;
   - CSAT/reason/feedback tratados como evidência sugestiva conforme qualidade, não prova causal.
5. Construa account-month com exatamente uma linha por `account_id`×mês na janela escolhida. Resolva múltiplas subscriptions sem somar cegamente MRR sobreposto; compare pelo menos duas regras (soma ingênua vs estado/winner), quantifique impacto e justifique a escolhida. Inclua colunas suficientes para futuras coortes/receita/risco, sem target leakage.
6. Invariantes/gates executáveis: unicidade account-month; MRR não negativo; datas válidas; active accounts ≤500; transições fecham; abertura + movimentos = fechamento (contagem e MRR, com tolerância explícita); totais de cada lente reconciliam à fonte; nenhum campo pós-data índice em features de risco. FAIL estrutural deve exit 1 + report atualizado, sem stale/traceback (reutilize a lição It01).
7. Faça verificações manuais independentes de pelo menos 3 casos: uma conta com divergência flag/evento, uma com múltiplos churns/reativação, uma com subscriptions sobrepostas; registre IDs, cálculo e conclusão metodológica. Não use esses casos para afirmar causa raiz.
8. Evidência/processo:
   - prompt integral em `process-log/prompts/iteration-02-prompt.md`;
   - report `process-log/reports/iteration-02-reconciliation-report.md` com workflow, decisões, alternativas rejeitadas, erros reais/correções (sem inventar), resultados, comandos, validações, riscos e handoff It03;
   - decisão humana explícita em `process-log/decisions/iteration-02-analytical-contract-decisions.md` (ou seção inequívoca no report): problema → opções → evidência → decisão → trade-off.
9. Atualize plano/checklist honestamente. Review gate It02 permanece `PENDING` até os três revisores; não marque etapas futuras.
10. Valide execução duas vezes/idempotência; checksum dos outputs; teste em sandbox ao menos um FAIL estrutural relevante; syntax/import; `git diff --check`; paths/segredos; escopo; Markdown/links; compare números reportados ao output.

CONTENÇÃO
- Sem ML, dashboard, app, causal inference avançada ou recomendações.
- Prefira uma função/script legível a framework. Nenhum banco binário.
- Output CSV/Markdown, não PDF.

GIT
- Antes: status/diff/log. Preserve tudo; sem revert/destrutivo/config/amend/force.
- Root ignora submissions: `git add -f` somente nos arquivos pretendidos.
- Commit esperado: `feat: reconcile churn definitions and analytical grain`.
- Push para origin; valide HEAD local=remoto e tree limpo.

CRITÉRIOS DE ACEITAÇÃO
- Divergências explicadas/quantificadas; contrato impede mistura entre lentes.
- Account-month único e determinístico, sem MRR dobrado por overlap; invariantes fecham.
- Regras temporais/leakage e qualidade explicitadas.
- Outputs regeneráveis/idempotentes; 3 casos manuais; FAIL robusto; nenhuma causa raiz prematura.
- Evidência, plano/checklist, commit/push completos no escopo.

REPORT FINAL
Status PASS/BLOCKED; hash/push; definições escolhidas; números de reconciliação; impacto de overlap; invariantes; 3 checks manuais; erros/correções; validações; riscos e handoff exato It03. Se contrato/invariantes não fecharem, use BLOCKED.