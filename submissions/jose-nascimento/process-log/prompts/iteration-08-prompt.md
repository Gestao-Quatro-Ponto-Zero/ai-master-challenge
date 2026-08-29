# Prompt da Iteração 08 — Process log final e evidências de uso de IA

- **Iteração:** 08 (consolidação do process log e evidências reais de uso de IA)
- **Data:** 2026-08-29
- **Executor:** exatamente um subagente `deepseek-max` (DeepSeek V4 Flash, max reasoning, via OpenCode Go), sob orquestração do opencode (`openai/gpt-5.6-sol` — "GPT 5.6 Sol Max")
- **Transcrição fiel com paths operacionais normalizados:** este arquivo (transcrição fiel do prompt recebido do orquestrador; não é o texto byte-a-byte do original — os únicos paths absolutos de máquina foram normalizados, nota abaixo)
- **Nota de normalização (política F2/It08):** **categorias normalizadas (2):** (1) `<repo-workdir>` — path absoluto do repositório de trabalho, onde vive a branch `submission/jose-nascimento` e a pasta da submissão; (2) `<review-reports-dir>` — path absoluto do diretório externo com os reports brutos de revisão (working artifacts fora do repo). **Por quê:** a política F2/It08 exige zero paths de máquina em documentos novos da pasta — o avaliador deve conseguir re-ler o prompt sem conhecer o ambiente do candidato, e nenhuma estrutura de diretórios pessoal deve vazar para o versionado. Os placeholders substituem **somente** esses paths; todo o restante — escopo, verdades do processo, artefatos obrigatórios, validações, contenção, git, aceitação, final — é transcrito fielmente.

---

Você é o AGENTE EXECUTOR ÚNICO da ITERAÇÃO 08 — process log final e evidências de uso de IA — do G4 AI Master Challenge. Este item é eliminatório. Consolide evidências reais, sem encenação, sem inventar atividade humana e sem finalizar PR/data (It10).

REPO
- `<repo-workdir>`, branch `submission/jose-nascimento`, pasta única `submissions/jose-nascimento/`, HEAD `a1e99cb8493b0c21e7470cc20c669ee97de1ce68`.
- Leia instruções oficiais/template, arquitetura de orquestração, TODOS os prompts/reports/decisions/hypotheses/review summaries It00–07, git log/diffs e README. Não leia pesquisas concorrentes como fonte de solução.

VERDADE DO PROCESSO (preservar)
- Candidato definiu escolha do Challenge 001, ferramenta, exigência de subagentes sequenciais, revisão 3x, originalidade, ângulos, inspeção visual e auditoria final; não alegar que ele escreveu/rodou manualmente o código.
- Orquestrador: OpenCode + runtime `openai/gpt-5.6-sol` (perfil máximo/GPT 5.6 Sol Max), contexto global, prompts/gates/arbitragem; não executa scripts/edita código. Exceção: visualizou PNGs e descreveu problemas.
- Executor/revisores/corretores: `deepseek-max` / DeepSeek V4 Flash, max reasoning via OpenCode Go; 1 executor serial, 3 reviewers paralelos read-only com mesmo prompt/contextos separados, 1 fixer serial quando necessário.
- Mesmos 3 reviewers = independência de contexto/amostragem, NÃO diversidade de modelo; correlated errors possíveis.
- Reports brutos externos dos revisores viveram em `<review-reports-dir>`; os artefatos versionados são review summaries detalhados. Não crie links finais quebrados para diretórios temporários fora do repo; se mencionar, diga que são working artifacts não incluídos e aponte summary versionado como evidência persistente.

ARTEFATOS OBRIGATÓRIOS
1. `process-log/README.md` como entrada principal, curto mas completo:
   - escopo/ferramentas e por quê;
   - diagrama do pipeline Orchestrator→Executor→3 Reviews→Fixer→Gate;
   - decomposição cronológica It00–08, cada uma com objetivo, IA usada, decisão/julgamento, output, commit/review summary link;
   - como problema foi entendido antes de promptar (hipóteses It03/assumptions It05/outline It07 commitados antes);
   - onde IA errou (resumo + link ao ledger de erros);
   - o que candidato/orquestrador adicionaram que um prompt único não faria;
   - quantas iterações/reviews/correções, derivadas de artefatos/git e com definição;
   - limitações do processo e budget excedido honestamente;
   - evidence map navegável (prompts, reports, decisions, hypotheses, reviews, git, solução).
2. `process-log/errors/ai-errors-and-corrections.md`: exatamente **8 erros materiais reais**, selecionados por valor, não cosméticos. Para cada: etapa; output errado; por que plausível/perigoso; quem detectou; causa raiz; decisão/correção; validação; commit/evidence link. Inclua obrigatoriamente:
   - It01 schema missing → KeyError/report stale;
   - It02 winner revenue lens escondendo encerramentos não dominantes;
   - It03 meses pré-signup como zeros artificiais;
   - It03 KM horizon/layout se couber;
   - It04 mapeamento visual R_D↔R_F invertido, detectado pela inspeção ocular do orquestrador apesar de validadores passarem;
   - It05 GO ≥10% sem considerar power/IC;
   - It06 pycache/verifier e/ou categórico inválido stale;
   - It07 drift/truncamento/clareza executivo.
   Escolha 8 sem inflar; números/commits devem bater.
3. `process-log/decisions/decision-ledger.md`: tabela concisa com decisão, alternativas, evidência, `candidato` / `orquestrador` / `executor` / `consenso reviewers`, trade-off, commit. Diferencie claramente decisão humana do candidato e decisões dos modelos; não atribua ao humano o que subagente decidiu.
4. `process-log/evidence-index.md`: índice completo de paths versionados; todos links relativos resolvem. Não copiar 24 raw review reports externos; summaries versionados + prompts/fix reports/git são evidência persistente suficiente, explique.
5. Atualize README seção Process Log:
   - workflow resumido e links aos 4 artefatos acima;
   - tabela ferramentas intacta/correta;
   - `Onde IA errou` e `O que eu adicionei` com síntese factual;
   - checkboxes: marque SOMENTE evidência real. Screenshots/screen recording/chat export ficam unchecked se não existem; marque git history e `Outro: prompts literais, reports, decisões, review summaries`. Não chamar prompts de chat export.
   - Data permanece `pendente`; LinkedIn `não informado`.
6. Atualize verifier 06 com gates de process log: arquivos presentes, exatamente 8 erros, links internos resolvem, zero link para diretório temporário, modelos/harness corretos, checkboxes honestos, nenhum placeholder falso, review summaries It00–07, prompt/report/decision/hypothesis inventory, commit hashes existentes, estados. Não hardcode contagens frágeis onde glob deriva.
7. Arquive este prompt `process-log/prompts/iteration-08-prompt.md`; report `process-log/reports/iteration-08-process-log-report.md` com método de inventário, decisões, números, links, git, errors reais desta iteração e handoff It09.
8. Atualize plano/checklist: It08 CONCLUDED após validação, gate3x PENDING; It09/10 PENDING.

VALIDAÇÕES
- `./run.sh`/verifier passam sem alterar report executivo/6 PNG/números; 2×/CWD/fresh clone; process link checker; Markdown; exactly 8 errors; evidence index coverage; all commit hashes resolve; no absolute machine paths/segredos em novos docs; claims candidate vs AI auditados; README checkboxes honestos.
- FAIL test: remova/corrompa um evidence link/error entry em sandbox → verifier exit 1 diagnóstico útil.
- Não aumente report executivo.

CONTENÇÃO
- Narrativa útil, não dump de 40 prompts. Links para evidência detalhada. Sem screenshots falsos, sem marketing, sem copiar raw reviews externos.

GIT
- Só pasta; commit `docs: consolidate AI process log and evidence`; sem amend/force/config/destrutivo; push/local==remote/tree limpo.

ACEITAÇÃO
- Avaliador entende ferramentas, decomposição, iteração, erros/correções, contribuição do candidato, evidência persistente; zero claim falso; verifier cobre.

FINAL
PASS/BLOCKED; hash/push; artifacts; contagens de etapas/reviews/fixers/prompts/reports derivadas; 8 erros; candidate-vs-AI decisions; README checkboxes; fresh clone/verifier/links; risks/handoff It09. BLOCKED se evidência principal depender de working artifacts fora do repo ou atribuir trabalho de IA ao candidato.