# Chat Export — Sessão 01: Planejamento do MVP

**Data:** 2026-05-28
**Plataforma:** Claude (Cowork mode) — modelo Opus 4.7
**Participantes:** Pedro Henrique (candidato) ↔ Claude (atuando como PM + Engenheiro de Software)
**Contexto:** Sessão de planejamento estratégico para o Challenge 002 do processo seletivo AI Master no G4 Educação.

---

## Sumário executivo

Sessão de planejamento que evoluiu em 6 turnos:

1. Briefing inicial + leitura do desafio
2. Calibração estratégica via perguntas multiple-choice
3. Plano de execução v1 (protótipo Streamlit enxuto)
4. **Mudança de escopo:** de protótipo para webapp completo com 2 personas + voice + RAG
5. Revisão de compliance com `CONTRIBUTING.md`
6. Acesso aos datasets via `kagglehub` + consolidação do checklist na SPEC

**Output final:**
- `docs/00-PLANO-DE-EXECUCAO.md` — plano estratégico
- `docs/SPEC-MVP.md` v1.2 — spec única consolidada (visão, stack, schema, sprints, compliance)
- Estrutura de pastas em compliance com regras do CONTRIBUTING

---

## Turno 1 — Briefing inicial

### Pedro:

> Estou participando de um desafio técnico para uma vaga na G4 educação. Conforme os arquivos que você tem acesso. Preciso que use sua expertise bem como as instruções dadas para traçar o melhor plano de desenvolvimento de um MVP para o challenge 002. Vamos iniciar com um bom planejamento, entendendo cada parte do projeto.

### Claude:

**Ações executadas:**
- Leu `README.md`, `challenges/process-002-support/README.md`, `submission-guide.md`, `templates/submission-template.md`, `CONTRIBUTING.md`, índice `challenges/README.md`
- Identificou entregáveis obrigatórios do Challenge 002:
  - Diagnóstico operacional (Dataset 1)
  - Proposta de automação com IA (ambos datasets)
  - Protótipo funcional (diferencial)
  - Process Log obrigatório
- Identificou datasets disponíveis:
  - Dataset 1: `suraj520/customer-support-ticket-dataset` (~30k registros)
  - Dataset 2: `adisongoh/it-service-ticket-classification-dataset` (~48k textos em 8 categorias)

**Decisão:** antes de gerar plano, calibrar abordagem via 3 perguntas-chave.

---

## Turno 2 — Calibração estratégica

### Claude (perguntas):

1. **Conforto com código:** Python full / vibe coding / foco em produto
2. **Tempo:** sessão concentrada / 2-3 sessões / 4-5h corridas
3. **Diferencial buscado:** diagnóstico+ROI / protótipo técnico / frame de processo / os três combinados

### Pedro (respostas):

- **Stack:** "Quero foco em produto, não código"
- **Tempo:** "Pouco tempo (4-5h corridas)"
- **Diferencial:** "Os três combinados (recomendado)"

### Claude (análise interna registrada na memória):

A combinação escolhida é a mais ambiciosa possível. Tradeoff: 4-5h + sem código + os três diferenciais exige cortes inteligentes (zero-shot em vez de treinar modelo, EDA focal em vez de exaustivo, Streamlit em vez de React).

---

## Turno 3 — Plano de execução v1

### Claude (entregáveis):

**Memória persistente criada:**
- `MEMORY.md` (índice)
- `user_pedro_profile.md` — perfil + preferências
- `project_g4_challenge_002.md` — contexto do projeto
- `feedback_no_code_first.md` — Claude escreve código, Pedro executa

**Task list criada (6 fases):**
1. Fase 0 — Alinhamento e setup
2. Fase 1 — Diagnóstico operacional com dados
3. Fase 2 — Protótipo funcional (Streamlit + Claude API) ← *será reescrita no Turno 4*
4. Fase 3 — Frame de processo + matriz humano-vs-IA
5. Fase 4 — Submission write-up + Process Log
6. Fase 5 — Verificação final + PR

**Arquivo gerado:** `docs/00-PLANO-DE-EXECUCAO.md` cobrindo:
- Leitura do que o desafio realmente testa (julgamento ≠ análise técnica)
- Janela de diferenciação vs baseline ("candidato cola brief no ChatGPT")
- Tradeoff honesto da combinação escolhida
- Arquitetura inicial: notebook + Streamlit **Triage Copilot**
- Plano em 5 fases timeboxed
- O que NÃO fazer (cortes deliberados)
- 5 critérios de "pronto"

**Mensagem condensada ao Pedro:**
- Leitura estratégica do desafio
- Janela de diferenciação
- Tradeoff assumido
- Próximo passo: baixar os datasets

---

## Turno 4 — Mudança de escopo (de protótipo para webapp)

### Pedro:

> Sua ideia parece boa, no entanto, quero deixar claro algumas necessidades. Me ajude a montar o plano, tendo em vista que: vamos entregar um MVP funcional que:
>
> **(1)** tenha o poder de analisar os 2 datasets via algum script em python, acredito;
>
> **(2)** consiga responder de forma lógicas as seguintes questões:
> - Onde o fluxo trava? Gargalos por canal, prioridade, tipo de ticket.
> - O que impacta satisfação? Quais variáveis mais influenciam o CSAT?
> - Quanto estamos desperdiçando? Quantifique em horas e custo.
> - O que automatizar — classificação, roteamento, respostas, triagem, duplicatas.
> - O que NÃO automatizar — quais tipos exigem julgamento humano.
> - Como funcionaria na prática — fluxo proposto.
>
> **(3)** sistema para o dir. de operacoes (admin) e para o cliente final (que costuma usar o app para abrir e acompanhar seus tickets)
>
> **(4)** do ponto de vista do admin, o app deverá conseguir analisar os datasets e saber responder de forma criteriosa às perguntas
>
> **(5)** do ponto de vista do cliente final, ele deverá poder abrir um ticket, mas além disso, uma ideia que tive aqui: ele poderá gravar sua solicitação via áudio, visando simplificar um processo que no ideal, ele nem deveria passar, teremos tbm um modelo tipo whisper da openai para transcrever o áudio e já dar possíveis respostas ao pesquisar na base na coluna resolution do dataset (essa busca devera ser feita via RAG: embeddings - viA Supabase Vector Store).
>
> Assim, quero apenas que de forma abrangente mas breve, voce me gere um as especificacoes para eu executar em um outro code assistant o desenvolvimento do mvp

### Claude:

**Análise:** mudança significativa de escopo — de protótipo enxuto para produto full-stack. Mais ambicioso, mas defensável (mostra visão de produto, não só análise). Saída precisa ser uma **spec única, executável em outro code assistant**.

**Memória atualizada:** registrada mudança de escopo em `project_g4_challenge_002.md`.

**Task #3 atualizada:** "Fase 2 — MVP webapp completo (Next.js + Supabase)".

**Arquivo gerado:** `docs/SPEC-MVP.md` v1.0 com 13 seções:

1. Visão do produto — "o maior ganho não é responder ticket mais rápido — é evitar que ele exista"
2. Personas e jobs-to-be-done (admin + cliente final)
3. Stack: **Next.js 14 + Supabase (Postgres + pgvector + Auth + Storage) + OpenAI (GPT-4o-mini + Whisper + embeddings)**
4. Arquitetura alto-nível (frontend → API routes → OpenAI + Supabase + insights.json offline)
5. Módulos do MVP (7 subseções, do script Python offline ao dashboard admin)
6. **Schema SQL completo do Supabase** (profiles, support_tickets_kb com pgvector, tickets, deflection_events, função `match_kb`, RLS)
7. API Routes do Next.js (transcribe, rag-search, classify, tickets, deflection, insights) com prompts
8. Variáveis de ambiente (`.env.local`)
9. Estrutura de pastas
10. Sprints de execução (5 sprints com prompts sugeridos)
11. Critérios de aceite do MVP
12. O que NÃO está no MVP (deixar explícito pro avaliador)
13. Próximo passo pra Pedro

**Decisão de produto destacada:** introduziu tabela `deflection_events` + status `deflected` → **taxa de deflexão como KPI principal**. Diferencia: prova que sistema EVITA tickets, não só processa mais rápido.

---

## Turno 5 — Revisão de compliance com CONTRIBUTING.md

### Pedro:

> ótimo, parece promissor. Mas voce revisou as regras de alteracao dos arquivos e etc? Deixe especificado com base no arquivo CONTRIBUTING

### Claude (autocorreção):

**Problema identificado no SPEC v1.0:** Seção 9 mostrava estrutura de pastas Next.js (`/app`, `/components`, `/lib`) como se fosse raiz do projeto. Um code assistant interpretaria isso como **raiz do repo** e rodaria `create-next-app` lá — violando a regra crítica do CONTRIBUTING ("PRs que alteram arquivos fora de `submissions/seu-nome/` serão rejeitados") e **desclassificando a submissão antes da avaliação técnica**.

**Correções aplicadas:**

1. **Estrutura física do repo reorganizada:**
   - Criou `submissions/pedro-henrique-silva/solution/`
   - Criou `submissions/pedro-henrique-silva/process-log/screenshots/`
   - Criou `submissions/pedro-henrique-silva/process-log/chat-exports/`
   - Criou `submissions/pedro-henrique-silva/docs/`
   - Moveu `00-PLANO-DE-EXECUCAO.md` e `SPEC-MVP.md` pra `docs/`

2. **SPEC v1.1:**
   - **Nova Seção 0** no topo: "Regras obrigatórias de submissão" com branch, pasta única permitida, estrutura obrigatória, título do PR, restrição de escopo. Inclui aviso explícito ao code assistant de que tudo é relativo a `solution/`.
   - **Seção 9 corrigida** com header destacado: "Tudo abaixo é relativo a `submissions/pedro-henrique-silva/solution/` — não à raiz do repo."
   - **Seção 13 (próximo passo)** com comandos git exatos (fork → branch → `cd solution/` → `create-next-app` → push → PR title exato)

3. **Arquivo separado criado:** `docs/COMPLIANCE-CHECKLIST.md` (depois consolidado no SPEC no Turno 6) com armadilhas comuns dos code assistants e 4 comandos de verificação final.

### Mensagem ao Pedro:

Listou as 7 regras do CONTRIBUTING numa tabela, apontou o erro específico do SPEC original, mostrou estrutura reorganizada, e explicou que o COMPLIANCE-CHECKLIST deve ser passado junto com o SPEC pro code assistant.

---

## Turno 6 — kagglehub + consolidação

### Pedro:

> outro para incluir na spec mvp: o acesso aos dataset:
> dataset 1:
> ```python
> import kagglehub
> path = kagglehub.dataset_download("suraj520/customer-support-ticket-dataset")
> print("Path to dataset files:", path)
> ```
>
> dataset2:
> ```python
> import kagglehub
> path = kagglehub.dataset_download("adisongoh/it-service-ticket-classification-dataset")
> print("Path to dataset files:", path)
> ```
>
> ---
> adicione esse compliance checklist ao mesmo arquivo de spec mvp

### Claude:

**SPEC v1.2 — alterações:**

1. **Seção 5.1 enriquecida** com:
   - Snippet `download_datasets.py` usando `kagglehub` pros 2 datasets
   - Setup: `pip install kagglehub pandas scikit-learn openai supabase`
   - Nota sobre autenticação (`~/.kaggle/kaggle.json`)
   - **Aviso crítico:** CSVs não devem ser commitados (GitHub rejeita > 100MB) — sugestão: commitar amostra de 100 linhas
   - Pipeline reorganizado em 3 scripts: `download_datasets.py` → `analyze_datasets.py` → `populate_kb.py`

2. **Seção 9** atualizada com `download_datasets.py` adicionado.

3. **Nova Seção 13** (incorpora todo o checklist) com 4 subseções:
   - 13.1 Regras críticas (rejeição automática)
   - 13.2 Regras de conteúdo (penalização)
   - 13.3 Armadilhas comuns do code assistant
   - 13.4 Verificação final (4 comandos git/ls)

4. **Antiga Seção 13** renumerada para Seção 14 (Próximo passo).

5. **`COMPLIANCE-CHECKLIST.md` deletado** (eliminada duplicação — agora single source of truth).

6. **Versão bumped para 1.2:** "acesso aos datasets via kagglehub + checklist de compliance incorporado".

---

## Estado final da pasta de submissão

```
submissions/pedro-henrique-silva/
├── docs/
│   ├── 00-PLANO-DE-EXECUCAO.md     ← plano estratégico (Turno 3)
│   └── SPEC-MVP.md                  ← spec consolidada v1.2 (Turnos 4-6)
├── process-log/
│   ├── chat-exports/
│   │   └── 01-planning-session.md   ← este arquivo
│   └── screenshots/                 ← (vazio — pra preencher)
└── solution/                        ← (vazio — código entra aqui)
```

---

## Memória persistente (`spaces/.../memory/`)

```
MEMORY.md
user_pedro_profile.md             ← perfil + preferências de colaboração
project_g4_challenge_002.md       ← contexto + escopo atualizado
feedback_no_code_first.md         ← Claude escreve código, Pedro executa
```

---

## Decisões estratégicas registradas nesta sessão

| # | Decisão | Por quê |
|---|---|---|
| 1 | Stack: Next.js + Supabase + OpenAI | Code assistants entendem nativamente; BaaS resolve Auth + DB + pgvector + Storage |
| 2 | Análise dos datasets em script Python **offline** | Não faz sentido recalcular agregação de 30k linhas em produção; gera `insights.json` estático |
| 3 | Taxa de deflexão como KPI principal | Diferencia da solução baseline: prova que o sistema EVITA tickets, não só os processa mais rápido |
| 4 | Zero-shot LLM em vez de fine-tuning | Economiza tempo; acurácia suficiente pra MVP; argumentação estratégica mais defensável |
| 5 | Reorganizar estrutura física antes do código | Compliance com CONTRIBUTING é binário (passa ou desclassifica) |
| 6 | Mesclar checklist no SPEC | Single source of truth pro code assistant; reduz risco de esquecer regras |
| 7 | `kagglehub` em vez de download manual | Reprodutibilidade + pipeline automático ponta-a-ponta |

---

## Onde a IA (Claude) errou e como corrigi

1. **SPEC v1.0 com estrutura de pastas ambígua:**
   - Erro: mostrei `/app`, `/components` como se fosse raiz do projeto
   - Impacto: code assistant interpretaria como raiz do repo, violando CONTRIBUTING
   - Correção (Turno 5, apontada pelo Pedro): nova Seção 0 + Seção 9 com header explícito de "relativo a `solution/`"

2. **Duplicação SPEC + COMPLIANCE-CHECKLIST:**
   - Erro: criei dois arquivos no Turno 5 com conteúdo parcialmente redundante
   - Impacto: code assistant teria que ler dois contextos; risco de divergência
   - Correção (Turno 6, apontada pelo Pedro): mesclei o checklist na Seção 13 do SPEC e deletei o arquivo separado

3. **Faltou pipeline de download dos datasets:**
   - Erro: SPEC v1.0 falava em "Carregar Dataset 1 e Dataset 2" sem especificar como
   - Impacto: code assistant teria que adivinhar (provavelmente sugerir download manual)
   - Correção (Turno 6, fornecida pelo Pedro): integrei `kagglehub` no pipeline

---

## O que o humano agregou que a IA sozinha não faria

1. **Pegou a falha de compliance** no SPEC v1.0. O Claude tinha lido o CONTRIBUTING mas não amarrou na spec — foi cobrança direta do Pedro que disparou a correção.
2. **Trouxe o `kagglehub`** como decisão de pipeline. Claude provavelmente sugeriria download manual ou via `kaggle CLI`.
3. **Definiu o escopo ambicioso** (2 personas + voice + RAG) em vez de aceitar o protótipo enxuto que Claude tinha proposto inicialmente.
4. **Forçou consolidação dos arquivos** em vez de aceitar a duplicação SPEC + CHECKLIST.

---

*Export gerado em 2026-05-28 ao final da Sessão 01.*
*Próxima sessão: geração dos scripts Python (`download_datasets.py`, `analyze_datasets.py`, `populate_kb.py`) ou início do Sprint 1 do MVP em outro code assistant.*
