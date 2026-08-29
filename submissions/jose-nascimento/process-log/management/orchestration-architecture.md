# Arquitetura de Orquestração Multiagente — Challenge 001 (Diagnóstico de Churn · RavenStack)

- **Tipo:** adendo obrigatório de ferramentas/process log (fonte atual de verdade de ferramenta/processo)
- **Data:** 2026-08-28
- **Status:** vigente; complementa o execution-plan (§1, regras de orquestração) e detalha o que a tabela "Ferramentas usadas" do README apenas resumia
- **Escopo:** descreve como o trabalho foi realmente executado (harness, modelos, papéis, contexto, permissões, outputs), o rationale, as limitações e as fontes da descrição

> **Nota de honestidade:** a descrição inicial do processo (README scaffold, Iteração 00) era **curta e incompleta** — listava "opencode (orquestrador)" e "deepseek-max (subagente via OpenCode Go)" sem detalhar modelos, papéis, contexto, permissões e limitações. Este adendo corrige e aprofunda essa descrição; o histórico anterior está preservado no git e nos prompts/reports antigos, que não foram reescritos como se esta descrição sempre existisse.

---

## 1. Resumo

O trabalho roda em um **harness compartilhado — OpenCode**. Um **orquestrador** (modelo `openai/gpt-5.6-sol`, chamado pelo candidato de **GPT 5.6 Sol Max**, perfil de máxima capacidade da sessão) mantém o contexto global e o estado do projeto, decompõe as etapas em iterações, escreve os prompts/contratos de cada etapa, arbitra as divergências dos revisores, decide rework e controla gates e risco — **sem executar scripts nem editar a solução**. Cada iteração é executada por **exatamente um executor** (`deepseek-max`, powered by **DeepSeek V4 Flash at max reasoning effort via OpenCode Go**) com contexto novo/limpo e escopo fechado. Ao fim de cada etapa, **3 revisores independentes** (mesmo modelo, mesmo prompt, contextos separados, read-only no repo) produzem reports externos únicos; se houver findings materiais, um **corretor sequencial** (novo `deepseek-max`) os resolve, testa, registra o review summary e faz commit/push. O fluxo é serial por iteração: `Orchestrator → Executor → Review A/B/C (paralelo, read-only) → Fixer (se necessário) → próximo gate`.

---

## 2. Fluxo serial (diagrama textual)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ORQUESTRADOR — OpenCode harness · openai/gpt-5.6-sol ("GPT 5.6 Sol Max") │
│ contexto global da sessão · não executa scripts · não edita a solução    │
└──────────────────────────────────────────────────────────────────────────┘
        │  decompõe etapa · escreve prompt/contrato · define escopo, critérios
        │  objetivos de aceitação e commit esperado
        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ EXECUTOR — exatamente 1 subagente `deepseek-max` por iteração            │
│ (DeepSeek V4 Flash, max reasoning, via OpenCode Go)                      │
│ contexto novo/limpo · escopo fechado · pasta única permitida             │
│ implementa → testa → documenta → commit/push                             │
└──────────────────────────────────────────────────────────────────────────┘
        │  iteração CONCLUDED (validada pelo executor)
        ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ REVISÃO 3× — 3 subagentes `deepseek-max` INDEPENDENTES, EM PARALELO      │
│ mesmo prompt · contexto separado por instância · READ-ONLY no repo       │
│ (sandboxes fora do repo) → 3 reports externos únicos (veredicto+findings)│
└──────────────────────────────────────────────────────────────────────────┘
        │  finding material?                          │
        ▼  sim                                        ▼  não
┌────────────────────────────────────────────────────────┐   gate CONCLUDED
│ FIXER — 1 subagente `deepseek-max` SEQUENCIAL          │   → próxima
│ lê os 3 reports · resolve findings materiais · testa   │   iteração
│ · registra review summary · commit/push                │
└────────────────────────────────────────────────────────┘
        │
        ▼
   gate do checklist (B3) concluído → próxima iteração (serial)
```

---

## 3. Componentes

| Componente | Modelo (runtime) | Harness | Contexto | Permissões | Outputs |
|---|---|---|---|---|---|
| **Orquestrador** | `openai/gpt-5.6-sol` ("GPT 5.6 Sol Max" — perfil de máxima capacidade da sessão) | OpenCode (harness compartilhado) | Global da sessão: estado do projeto, execution-plan, checklist, decisões, arbitragens | Gerencia agentes (Task); **não** executa scripts de análise nem edita a solução | Prompts/contratos por iteração, decisões de arbitragem/rework, controle de gates e risco, documentos de governança |
| **Executor** (1 por iteração) | `deepseek-max` = DeepSeek V4 Flash, max reasoning | OpenCode via OpenCode Go | Novo/limpo a cada iteração; escopo fechado pelo prompt integral (paths, critérios, commit esperado) | Escrita apenas na pasta permitida `submissions/jose-nascimento/`, bash, git (`git add -f` em paths pretendidos) | Código analítico, outputs/evidências/tabelas/gráficos, report de iteração, commit/push |
| **Revisores** (3 por gate) | `deepseek-max` = DeepSeek V4 Flash | OpenCode via OpenCode Go | Separado por instância: 3 contextos independentes, mesmo prompt de revisão | **Read-only** no repo (sandboxes fora do repo; working tree intacto antes/depois) | 3 reports de revisão externos únicos, com veredicto e findings (ex.: `/tmp/opencode/ai-master-review-reports/`) |
| **Corretor** (sequencial, se necessário) | `deepseek-max` = DeepSeek V4 Flash | OpenCode via OpenCode Go | Novo, inicia lendo os 3 reports do gate | Escrita na pasta permitida, bash, git | Correções materiais, recálculos/validações pós-fix, review summary no ledger, commit/push |

**Permissões e isolamento:** o harness OpenCode dá suporte nativo a subagentes com contexto novo (child sessions), modos (`primary`/`subagent`) e permissões por agente — inclusive agentes read-only — o que viabiliza tecnicamente os papéis acima (ver §8, fonte 1).

---

## 4. Papéis em detalhe

### 4.1 Orquestrador (`openai/gpt-5.6-sol` — "GPT 5.6 Sol Max")

- Mantém o contexto global/estado do projeto (plano, checklist, decisões, acumulado de tempo, riscos).
- Decompõe o desafio em iterações e escreve, para cada uma, o **prompt integral** com escopo fechado, critérios objetivos de aceitação, validações e commit esperado (arquivados em `process-log/prompts/`).
- Arbitra divergências entre revisores, decide rework/correção e controla gates (estados `PENDING`/`OPEN`/`CONCLUDED`).
- **Não executa scripts nem edita a solução** — delega a execução a subagentes (regra B8 do checklist; execution-plan §1.1).

### 4.2 Executor (`deepseek-max` — DeepSeek V4 Flash, max reasoning, via OpenCode Go)

- Exatamente **um executor por iteração**, em sequência (nunca dois implementando em paralelo).
- Recebe **contexto novo/limpo** (sem arrastar o histórico da etapa anterior) e escopo fechado.
- Implementa, testa, documenta e faz commit/push; reporta PASS/BLOCKED com hash, arquivos, validações, riscos e handoff.

### 4.3 Revisores (3 × `deepseek-max` — DeepSeek V4 Flash, via OpenCode Go)

- **Três instâncias independentes em paralelo**, mesmo prompt de revisão e contexto separado por instância.
- **Read-only no repo**: trabalham em sandboxes fora do repo; o working tree permanece limpo antes/depois.
- Produzem **reports externos únicos** (veredicto + findings), que o orquestrador consolida no ledger (`process-log/reviews/iteration-XX-review-summary.md`).
- **Não são diversidade de modelo** — são independência de contexto/amostragem; erros correlacionados ainda são possíveis (ver §6).

### 4.4 Corretor (sequencial `deepseek-max` — DeepSeek V4 Flash, via OpenCode Go)

- Um **novo** subagente sequencial que lê os 3 reports do gate, resolve os **findings materiais** (erros factuais, violações de regra, claims falsas, risco de reprovação), testa/recalcula, registra o review summary e faz commit/push.
- Findings LOW/redação podem ser aceitos com justificativa ou corrigidos no mesmo passe (política de contenção, execution-plan §2.4).

---

## 5. Rationale (por que esta arquitetura)

1. **Inteligência máxima no orquestrador, de alta alavancagem.** Decompor o problema, escrever contratos e arbitrar revisões são as decisões de maior impacto do processo; o modelo de fronteira/maior capacidade disponível nesta sessão foi **reservado** a esse trabalho global — inclusive por seu custo relativo maior. É uma **decisão arquitetural desta execução**, não uma afirmação universal sobre os modelos (ver §8, distinção runtime vs external).
2. **Custo/latência contidos delegando tarefas bounded ao Flash.** Implementar com escopo fechado, revisar read-only e corrigir são trabalhos bem delimitados/repetíveis; o DeepSeek V4 Flash (mais rápido/eficiente) os executa, contendo custo e latência do ciclo completo (1 executor + 3 revisores + eventual corretor por iteração).
3. **Contexto limpo reduz ancoragem/contaminação e libera a janela para a etapa.** Cada executor/corretor parte de contexto novo: não herda conclusões parciais, tonificações ou erros de etapas anteriores, e tem a janela de contexto inteira disponível para o escopo corrente.
4. **Implementação serial evita conflitos e mantém git linear.** Um executor por vez elimina conflitos de escrita e produz um histórico auditável, commit a commit, por iteração.
5. **3 revisores independentes reduzem a chance de erro escapar.** Três leituras críticas read-only do mesmo resultado, com contextos separados, tornam menos provável que um problema material passe despercebido (na prática, até aqui: ver §7).
6. **Fixer serial resolve consenso/divergência.** Um único passe de correção consolida os 3 reports, evita correções concorrentes e registra a matriz finding→ação no ledger.

---

## 6. Limitações (declaradas, não escondidas)

1. **Mesmo modelo nos 3 reviews.** A independência é de contexto/amostragem, não de modelo: vieses sistemáticos do modelo (ex.: interpretação comum de um contrato) podem aparecer nos 3 reports — **erros correlacionados ainda são possíveis**.
2. **Independência não elimina correlação.** Mesmo prompt + mesmo modelo + mesmo corpus → os 3 revisores podem compartilhar o mesmo mal-entendido (ex.: na It01, os 3 convergiram no mesmo finding M1 — bom para confiança, mas converge não é prova).
3. **Reports de revisão não substituem validação executável.** Veredicto de revisor é leitura crítica, não execução; por isso cada iteração mantém validações executadas (re-execução idempotente, verificações manuais independentes, sandboxes de falha estrutural, recálculos).
4. **O orquestrador também pode errar.** Arbitragem, gates, contratos e prompts são produzidos por um modelo — erros de orquestração (escopo, critérios, decisões) são possíveis e são mitigados pela revisão 3x do resultado de cada etapa.
5. **Custo total e time budget.** O ciclo por iteração multiplica tokens (executor + 3 revisores + corretor); o acumulado é controlado no checklist (F11) com a política de contenção do execution-plan (§2) — o adendo atual registrou ~40 min adicionais.
6. **IDs/características não verificáveis publicamente.** `openai/gpt-5.6-sol` e o perfil "max reasoning" vêm da metadata do harness da sessão; não há documentação pública oficial localizada para o ID exato do orquestrador (ver §8).

---

## 7. Exemplos reais do processo até a Iteração 04 (sem exagero)

| Iteração | O que o gate 3x pegou | Veredictos | Correção sequencial (commit) |
|---|---|---|---|
| It00 | Governança/README: ferramenta alegada incorreta (Claude Code/deepseek-v4-flash) e estrutura | `PASS_WITH_FIXES` ×3 | `docs: address iteration 00 review findings` |
| It01 | **Schema stale detectado 3/3**: schema quebrado crashava com `KeyError` e não regravava o relatório (relatório stale) — convergência dos 3 revisores | `PASS_WITH_FIXES` ×3 | `fix: handle schema failures in data audit` |
| It02 | **Lente de revenue churn degenerada** (M1: 18.507 vs 398.462/255 ocultos vs 1.179.139 exposição) + números hardcoded (M2) | `PASS` ×2 + `PASS_WITH_FIXES` ×1 | `fix: strengthen revenue churn contract` |
| It03 | **Janela pré-signup detectada na revisão** (M1: H4 contava meses anteriores ao signup como zero; Δ 13,7 p.p. era artefato) + 11 correções factuais/robustez | `PASS_WITH_FIXES` ×3 | `fix: correct exposure windows in root cause analysis` (recálculo independente 49/49) |
| It04 | Implementação validada pelo executor (34 PASS / 0 WARN / 0 FAIL pós-gate; 3 MVs; backtest recalculado 3/3; commits `feat: prioritize accounts by lifecycle and validated risk signals` + `fix: report R1 exposure of repeat-event and reactivated accounts by lens`) | `PASS_WITH_FIXES` ×3 | `fix: refine lifecycle evidence and essential charts` (D7 KM finais; sensibilidade 180d qualificada; R_B/S3 rounding; 42,6% ≠ maioria; narrativa derivada em runtime com gates G13; F11 honesto; refinamento visual 6 PNGs; pruning It04_a/b/e_support/f_segment → t12/t13/t06/t07) |

**Evidência no repo:** commits semânticos com autor do candidato; ledgers `process-log/reviews/iteration-XX-review-summary.md` (matriz finding→ação→arquivo:linha, recálculos, riscos, gate); reports de correção (`iteration-XX-review-fix-report.md`); prompts integrais arquivados em `process-log/prompts/`; este adendo.

---

## 8. Pesquisa e fontes (registro honesto)

Pesquisa breve realizada em **2026-08-28**, em chamadas web sequenciais, priorizando fontes primárias/oficiais. Nenhum ranking de blog, claim de benchmark sem fonte ou preço é usado como justificativa.

| # | Fonte (primária/oficial) | URL | Data de acesso | Claim que sustenta |
|---|---|---|---|---|
| 1 | OpenCode — Docs "Agents" (oficial) | https://opencode.ai/docs/agents (também https://opencode.ai/v2/docs/agents) | 2026-08-28 | OpenCode é um harness de agentes com agents primários e subagentes; **subagentes rodam em child sessions com contexto novo (fresh context)**; modos `primary`/`subagent`/`all`; permissões configuráveis por agente, incluindo agentes read-only (ex.: plan nega edição de arquivos) — sustenta a viabilidade técnica de contexto isolado, revisores read-only e papéis descritos em §3/§4 |
| 2 | OpenCode — Docs "Go" (oficial) | https://opencode.ai/docs/go | 2026-08-28 | **OpenCode Go** é o provedor oficial de baixo custo do OpenCode, com lista curada de modelos open de coding testados para uso agêntico; IDs usam o formato `opencode-go/<model-id>`; **DeepSeek V4 Flash** consta da lista pública (ID `deepseek-v4-flash`; endpoint de chat completions) — sustenta "subagentes `deepseek-max` via OpenCode Go". **Obs.:** a lista pública do Go mostra "GPT 5.6 Luna" e **não** contém `gpt-5.6-sol` — ver distinção abaixo |
| 3 | DeepSeek (oficial) — model card do DeepSeek-V4-Flash na org oficial do Hugging Face | https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash | 2026-08-28 | DeepSeek-V4-Flash é um modelo oficial da família DeepSeek V4 (MoE, 284B total / 13B ativos, contexto de 1M tokens). Existem também o model card oficial em PDF (https://fe-static.deepseek.com/chat/transparency/deepseek-V4-model-card-EN.pdf) e as docs oficiais de API (https://api-docs.deepseek.com/, model ID `deepseek-v4-flash`, com parâmetros de thinking/reasoning effort) — sustenta a identidade externa do modelo "DeepSeek V4 Flash" |
| 4 | Anthropic Engineering — "How we built our multi-agent research system" (fonte primária de engenharia) | https://www.anthropic.com/engineering/multi-agent-research-system | 2026-08-28 | Padrão orquestrador-trabalhador (orchestrator-worker): subagentes operam em paralelo com **context windows próprios**; separação de preocupações reduz path dependency e permite investigações independentes — sustenta o padrão de contexto isolado por subagente e a divisão lead/worker. Claims quantitativas do post são avaliações internas do próprio time (não reivindicadas aqui como verdade universal) |

### Distinção runtime metadata vs claims externas (exigência do adendo)

- **`openai/gpt-5.6-sol` ("GPT 5.6 Sol Max", perfil de máxima capacidade):** vem da **metadata runtime do harness** da sessão (informada pelo candidato/orquestrador). **Não há fonte oficial pública localizada** para esse ID exato — a lista pública do OpenCode Go contém outra variante da família (GPT 5.6 Luna) — e desempenho/custo não são verificáveis publicamente. Portanto, é tratado como **propriedade operacional/decisão desta execução**, não fato universal.
- **`deepseek-max` = DeepSeek V4 Flash com "max reasoning" via OpenCode Go:** a identidade do modelo (DeepSeek V4 Flash) é verificável em fontes oficiais (itens 2 e 3); a **configuração exata "max reasoning effort" nesta sessão é metadata do harness** (a API oficial da DeepSeek expõe parâmetros de reasoning effort, mas o valor efetivamente usado via OpenCode Go não é verificável publicamente).
- Nenhuma claim de "melhor do mundo", ranking ou benchmark é usada; a escolha de modelo é explicada como **decisão arquitetural** (§5), não como fato objetivo externamente verificável.

---

## 9. Status e handoff

- **Gate de revisão 3x da Iteração 04: `CONCLUDED`** (2026-08-28) — 3 veredictos `PASS_WITH_FIXES` (review-9c41f7a2 / review-df141f4f / review-3a4f8efa); escopo da revisão incluiu a implementação It04 **e** este adendo (fonte atual de verdade de ferramenta/processo), o README atualizado, o checklist e o prompt/report do adendo; findings do adendo: nenhum material (URLs 3/3 e claims verificadas; distinção runtime vs externa correta; único ponto F7/L2 = wording do F11, corrigido). Ledger: `process-log/reviews/iteration-04-review-summary.md`; correção: `process-log/reports/iteration-04-review-fix-report.md`.
- Iteração 05 em diante: `PENDING`; o fluxo serial acima se repete a cada etapa.
- Arquivos de referência: `process-log/management/execution-plan.md` (regras 1–8), `process-log/management/orchestrator-checklist.md` (itens B1–B6, F11), `process-log/prompts/orchestration-architecture-addendum-prompt.md` e `process-log/reports/orchestration-architecture-addendum-report.md` (registro deste adendo).