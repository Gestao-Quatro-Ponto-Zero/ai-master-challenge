# Prompt do Agente — Adendo de Arquitetura de Orquestração Multiagente (transcrição fiel)

**Tipo:** prompt integral recebido pelo agente documentador deste adendo · **Arquivado em:** 2026-08-28 · **Uso:** evidência de processo (process log obrigatório). Transcrição fiel do prompt recebido; apenas formatação markdown aplicada (conteúdo preservado).

---

Você é o AGENTE DOCUMENTADOR SEQUENCIAL de um adendo obrigatório do candidato na submissão ao G4 AI Master Challenge. Sua tarefa é pesquisar brevemente, corrigir e aprofundar a seção de ferramentas/process log sobre a arquitetura multiagente real. NÃO altere código analítico, outputs de dados, findings ou status da Iteração 04.

## REPO/BRANCH

- Repo `/tmp/opencode/ai-master-challenge-work`, branch `submission/jose-nascimento`, pasta única permitida `submissions/jose-nascimento/`.
- HEAD esperado `fb9d2decd2e27b356eeed6527c4555287c48b8c2`.
- Leia instruções oficiais (especialmente process log), README da submissão, plano/checklist, process reports e prompts existentes. Preserve histórico; não reescreva relatórios antigos como se a descrição sempre existisse.

## FATOS DE RUNTIME A DOCUMENTAR COM PRECISÃO

1. Harness compartilhado: **OpenCode**. O orquestrador e os subagentes operam via harness OpenCode; os subagentes `deepseek-max` são executados via OpenCode Go.
2. Orquestrador: modelo runtime exato **`openai/gpt-5.6-sol`**, usado no perfil de máxima capacidade da sessão (o candidato o chama de **GPT 5.6 Sol Max**). Papel: manter contexto global/estado do projeto, decompor etapas, escrever prompts/contratos, arbitrar divergências dos revisores, decidir rework, controlar gates e risco. Não executa scripts nem edita a solução; delega a subagentes.
3. Executores: subagente `deepseek-max`, powered by **DeepSeek V4 Flash at max reasoning effort via OpenCode Go**. Exatamente um executor por iteração, contexto novo/limpo e escopo fechado; implementa, testa, documenta, commit/push.
4. Revisores: também DeepSeek V4 Flash (`deepseek-max`) via OpenCode Go, três instâncias independentes em paralelo, mesmo prompt e contexto separado, read-only no repo; produzem reports externos únicos. Não são diversidade de modelo — são independência de contexto/amostragem — e erros correlacionados ainda são possíveis.
5. Corretor: um novo DeepSeek V4 Flash sequencial lê os três reports, resolve findings materiais, testa, registra review summary e commit/push.

## PESQUISA BREVE (OBRIGATÓRIA, SEM INVENTAR)

- Pesquise 2–4 fontes primárias/oficiais, em chamadas web sequenciais (não paralelas), sobre: OpenCode agents/subagents/context isolation/tooling; documentação oficial relevante do provedor/modelo se existir; padrões de multi-agent review/checker ou context isolation. Prefira docs oficiais/OpenCode/GitHub oficial/papers primários.
- NÃO use rankings de blog, claims de benchmark sem fonte, preço exato, nem afirme que um modelo é objetivamente "o melhor do mundo". Explique como decisão arquitetural: o modelo de fronteira/maior capacidade disponível nesta sessão foi reservado ao trabalho global de alta alavancagem e maior custo relativo; o Flash, mais rápido/eficiente, aos trabalhos bounded/repetíveis. Se desempenho/custo não for verificável publicamente para esses IDs exatos, rotule como propriedade operacional/decisão desta execução, não fato universal.
- Registre URLs, data de acesso e qual claim cada fonte sustenta. Se não houver fonte oficial para `gpt-5.6-sol`/`DeepSeek V4 Flash`, diga explicitamente que os IDs/características vêm da metadata runtime do harness, não da web.

## ALTERAÇÕES OBRIGATÓRIAS

1. Atualize a tabela `Ferramentas usadas` no `submissions/jose-nascimento/README.md` com linhas separadas para:
   - OpenCode harness + orquestrador GPT 5.6 Sol (`openai/gpt-5.6-sol`, perfil máximo);
   - executores DeepSeek V4 Flash (`deepseek-max`, max reasoning/OpenCode Go);
   - revisores DeepSeek V4 Flash (3 independentes read-only/mesmo prompt);
   - corretores sequenciais DeepSeek V4 Flash.
   Explique para que cada um foi usado. Não declare checks da submissão concluídos ainda.
2. Crie `process-log/management/orchestration-architecture.md`, objetivo e legível, com:
   - diagrama textual/fluxo serial: Orchestrator → Executor → Review A/B/C paralelo read-only → Fixer sequencial se necessário → próximo gate;
   - tabela de componentes/modelos/harness/contexto/permissões/outputs;
   - rationale: inteligência máxima no orquestrador de alto impacto; custo/latência contidos delegando tarefas bounded ao Flash; contexto limpo reduz ancoragem/contaminação e libera janela para etapa; implementação serial evita conflitos e mantém git linear; 3 revisores independentes reduzem chance de erro escapar; fixer serial resolve consenso/divergência;
   - limitações: mesmo modelo nos 3 reviews, independência não elimina correlação, reports não substituem validação executável, orchestrator também pode errar, custo total/time budget;
   - exemplos reais do processo até It04 (sem exagerar): schema stale detectado 3/3 na It01; revenue-lens detectado na It02; janela pré-signup detectada na It03; commits/review summaries como evidência;
   - pesquisa/fontes e distinção runtime metadata vs external claims.
3. Atualize `process-log/management/orchestrator-checklist.md` apenas nos itens de ferramenta/processo já comprovados, com referência ao novo arquivo. Não mude status de It04 review gate (continua PENDING).
4. Crie `process-log/prompts/orchestration-architecture-addendum-prompt.md` com este prompt integral e `process-log/reports/orchestration-architecture-addendum-report.md` com: pesquisa; decisões; mudanças; validações; limitações; git; handoff para review gate It04.
5. Não altere prompt/reports históricos para ocultar fatos; novo adendo é a fonte atual de verdade e deve admitir que a descrição inicial era curta/incompleta.

## VALIDAÇÃO/GIT

- Antes: status/diff/log, preserve tudo. Só pasta permitida.
- Verifique factualidade dos IDs e papéis, URLs válidas, ausência de claims não sustentados, Markdown/links, `git diff --check`, escopo, segredos/paths pessoais.
- `git add -f` apenas paths pretendidos.
- Commit `docs: document multi-agent orchestration architecture`.
- Sem amend/force/config/destrutivo. Push; confirme local==remote/tree limpo.

## REPORT FINAL

Status PASS/BLOCKED; hash/push; fontes pesquisadas e claims; descrição final dos quatro papéis; arquivos; validações; limitações; confirmação It04 gate ainda PENDING e handoff aos 3 reviewers. Se confundir modelo/harness ou usar claim sem fonte, BLOCKED.