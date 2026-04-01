# 📋 AI Master Challenge — Auditoria de Evidências do Projeto

**Data de Geração:** 2026-03-24
**Repositório:** DESAFIOG4
**Branch Atual:** `submission/gscopetti`
**Status:** Ativo

---

## 🎯 Visão Geral do Projeto

### Tipo de Projeto
**AI Master Challenge** — Plataforma de seleção baseada em desafios para identificar profissionais capazes de usar IA generativa como alavanca estratégica para resolver problemas complexos.

### Descrição Oficial
> O G4 está construindo um novo tipo de profissional: o **AI Master**. Uma pessoa capaz de entrar em qualquer área — vendas, suporte, marketing, operações — e usar IA generativa para resolver problemas reais de forma transformacional.

### Organização Responsável
- **G4 Educação**
- Website: https://g4educacao.com
- Descrição: Maior plataforma de educação executiva do Brasil

---

## 📁 Estrutura do Projeto

```
DESAFIOG4/
├── .aios-core/                    # Framework AIOS (arquivos principais)
├── .claude/                       # Configuração Claude Code
│   ├── CLAUDE.md                 # Instruções para Claude Code
│   ├── rules/                    # Regras contextuais (agent-authority, workflow-execution, etc.)
│   └── hooks/                    # Hooks de integração
├── .antigravity/                 # Documentação/recursos adicionais
├── .codex/                       # Índice de conhecimento
├── .cursor/                      # Configurações do Cursor
├── .gemini/                      # Recursos específicos
├── ai-master-challenge/          # Desafios do projeto
├── challenges/                   # Descrição dos 4 desafios
├── lead-scorer/                  # Possível solução de exemplo
├── public/                       # Recursos públicos
├── .gitignore                    # Configuração Git
├── .env                          # Variáveis de ambiente
├── LICENSE                       # Licença do projeto
├── README.md                     # Documentação principal
├── CONTRIBUTING.md               # Guia de contribuição
├── submission-guide.md           # Guia de submissão
├── templates/                    # Templates para submissões
│   └── submission-template.md   # Template padrão
└── nul                          # Arquivo de configuração/dados

```

---

## 📊 Histórico de Commits (Git)

### Estatísticas
- **Total de Commits Analisados:** 5
- **Branch Atual:** `submission/gscopetti`
- **Status da Branch:** Behind by 3 commits (fork/submission/gscopetti)
- **Autor Principal:** João Vitor Chaves Silva
- **Data dos Commits:** 2026-03-02

### Histórico Cronológico

| Commit | Hash | Data | Autor | Mensagem |
|--------|------|------|-------|----------|
| 1 | `4aed364` | 2026-03-02 | João Vitor Chaves Silva | feat: PR-only submissions — remove email option |
| 2 | `bcdfd2e` | 2026-03-02 | João Vitor Chaves Silva | docs: add baseline warning — AI-only submissions won't pass |
| 3 | `4b55509` | 2026-03-02 | João Vitor Chaves Silva | refactor: clean up repo structure — remove duplicates, add missing files |
| 4 | `d4c8fc7` | 2026-03-02 | João Vitor Chaves Silva | feat: add README.md for each challenge with detailed descriptions |
| 5 | `d91427f` | 2026-03-02 | João Vitor Chaves Silva | feat: AI Master Challenge — initial structure with 4 challenges |

### Análise por Tipo de Commit

| Tipo | Quantidade | Descrição |
|------|-----------|-----------|
| `feat:` | 3 | Novas funcionalidades |
| `docs:` | 1 | Atualizações de documentação |
| `refactor:` | 1 | Reorganização de código/estrutura |

---

## 🎪 Desafios Disponíveis

### Estrutura de Desafios
Todos os desafios estão na pasta `/challenges` com READMEs individuais detalhando contexto, critérios de qualidade e dados de referência.

### 4 Desafios Principais

#### **001 — Diagnóstico de Churn**
- **Categoria:** Dados / Analytics
- **Caminho:** `./challenges/data-001-churn/`
- **Tipo de Entregável:** Análise de dados
- **Contexto:** Identificar padrões de churn em base de clientes

#### **002 — Redesign de Suporte**
- **Categoria:** Operações / Customer Experience (CX)
- **Caminho:** `./challenges/process-002-support/`
- **Tipo de Entregável:** Redesign de processo
- **Contexto:** Otimizar fluxo de atendimento ao cliente

#### **003 — Lead Scorer**
- **Categoria:** Vendas / Revenue Operations (RevOps)
- **Caminho:** `./challenges/build-003-lead-scorer/`
- **Tipo de Entregável:** Código funcional / Protótipo
- **Contexto:** Construir sistema de scoring de leads

#### **004 — Estratégia Social Media**
- **Categoria:** Marketing
- **Caminho:** `./challenges/marketing-004-social/`
- **Tipo de Entregável:** Análise + Recomendações
- **Contexto:** Definir estratégia de redes sociais

### Tempo Estimado
- **Budget por Desafio:** 4-6 horas
- **Observação:** Sem deadline fixo; vagas limitadas

---

## 📝 Documentação Principal

### Arquivos Documentação Core

#### 1. **README.md** (Documentação Principal)
- **Tamanho:** 1,232 caracteres
- **Conteúdo:**
  - O que é um AI Master (4 princípios)
  - Como funciona (5 passos)
  - 4 Regras obrigatórias
  - Informações sobre baseline
  - O que não está sendo avaliado
  - O que está sendo avaliado
  - Lista de desafios com links
  - FAQ com 5 perguntas
  - Informações sobre G4

#### 2. **CONTRIBUTING.md** (Guia de Contribuição)
- **Tamanho:** 2,170 caracteres
- **Conteúdo:**
  - Passo a passo para submissão (7 passos)
  - Estrutura de pasta recomendada
  - Checklist pré-PR (6 itens)
  - Regras do PR
  - Guia para iniciantes em Git

#### 3. **submission-guide.md** (Guia de Submissão)
- **Tamanho:** 3,246 caracteres
- **Conteúdo:**
  - 2 partes obrigatórias (Solução + Process Log)
  - 6 formatos aceitos para evidências
  - O que queremos no process log
  - Estrutura de solução recomendada
  - O que torna submissões fortes/fracas

#### 4. **templates/submission-template.md** (Template de Submissão)
- **Propósito:** Estrutura padrão para READMEs de submissões
- **Localização:** `./templates/`

---

## 🔐 Regras de Submissão

### Regras Obrigatórias

1. **Use IA**
   - Esperado que use qualquer ferramenta de IA
   - Queremos ver *como* você usa, não apenas se usa
   - Status: ✅ OBRIGATÓRIO

2. **Qualquer Ferramenta é Permitida**
   - Claude, ChatGPT, Gemini, Cursor, Claude Code, Copilot, scripts custom, APIs
   - Status: ✅ FLEXÍVEL

3. **Envie Evidências do Processo**
   - A solução sozinha não basta
   - Process log é obrigatório
   - Status: ✅ OBRIGATÓRIO

4. **Sem Evidência = Desclassificação**
   - Submissões sem process log são automaticamente rejeitadas
   - Status: ✅ CRÍTICO

### Sobre o Baseline

**Baseline Existente:**
- Desafios já rodados em múltiplos modelos de IA
- Respostas de referência já existem (Claude, GPT, Gemini)
- Paridade com baseline é insuficiente

**Esperado:**
- Superar substancialmente o baseline
- Demonstrar julgamento crítico
- Adicionar valor além da saída bruta de IA

---

## 📬 Formato de Submissão

### Estrutura de Pasta Obrigatória

```
submissions/seu-nome/
├── README.md            ← Segue template de templates/submission-template.md
├── solution/            ← Sua solução (análise, código, protótipo)
│   ├── ...
│   └── ...
├── process-log/         ← Evidências de uso de IA
│   ├── screenshots/     ← Prints das conversas
│   ├── chat-exports/    ← Exports de chats
│   └── ...
└── docs/                ← Documentação adicional (opcional)
```

### Formatos Aceitos para Process Log

| Formato | Descrição | Status |
|---------|-----------|--------|
| **Screenshots** | Prints das conversas com AI | ✅ Aceito |
| **Screen Recording** | Vídeo do workflow (Loom, gravação de tela) | ✅ Aceito |
| **Chat Export** | Export da conversa (Claude, ChatGPT) | ✅ Aceito |
| **Narrativa Escrita** | Documento passo a passo | ✅ Aceito |
| **Git History** | Commits mostrando evolução com AI | ✅ Aceito |
| **Notebook Comentado** | Jupyter/Colab com comentários | ✅ Aceito |

### O Que Deve Conter o Process Log

- Quais ferramentas de IA foram usadas e por quê
- Como o problema foi decomposto antes de promptar
- Onde a IA errou e como foi corrigido
- O que foi adicionado que a IA sozinha não faria
- Quantas iterações foram necessárias

---

## ✅ Critérios de Avaliação

### O Que NÃO Está Sendo Avaliado
- ❌ Conhecimento de linguagem de programação específica
- ❌ Memorização de frameworks ou metodologias
- ❌ Experiência prévia no setor de educação
- ❌ Qual ferramenta de IA foi usada (X ou Y)

### O Que ESTÁ Sendo Avaliado
- ✅ Entendimento do problema antes de executar
- ✅ Uso inteligente de IA (não apenas copy-paste)
- ✅ Resultado resolve o problema de verdade
- ✅ Alguém consegue entender e agir com base na entrega

### Indicadores de Submissão Forte

1. ✅ Candidato claramente entendeu o problema
2. ✅ IA foi usada estrategicamente
3. ✅ Output é acionável
4. ✅ Process log mostra iteração e julgamento
5. ✅ Comunicação é clara

### Indicadores de Submissão Fraca

1. ❌ Output genérico (poderia ser sobre qualquer empresa)
2. ❌ Zero evidência de verificação
3. ❌ Process log mostra 1 prompt → 1 resposta
4. ❌ Foco em parecer inteligente vs. resolver
5. ❌ Documentação excessiva (40 páginas onde 5 resolveriam)

---

## 🔍 Status Atual do Repositório

### Informações de Git

**Branch Atual:** `submission/gscopetti`

**Status:**
```
Your branch is behind 'fork/submission/gscopetti' by 3 commits,
and can be fast-forwarded.
```

**Arquivos Não Rastreados (Untracked):**
- `.aios-core/` — Framework AIOS
- `.antigravity/` — Recursos adicionais
- `.claude/` — Configuração Claude Code
- `.codex/` — Índice de conhecimento
- `.cursor/` — Configurações Cursor
- `.env` — Variáveis de ambiente
- `.gemini/` — Recursos Gemini
- `lead-scorer/` — Possível solução de referência
- `nul` — Arquivo de configuração

**Arquivos Rastreados e Modificados:** Nenhum

### Estrutura de Submissões

**Pasta Esperada:** `submissions/`
**Status:** Vazia (nenhuma submissão ainda)

---

## 🛠️ Tecnologias e Frameworks

### AIOS Framework (Synkra AIOS)
- **Versão:** Integrado no projeto
- **Localização:** `.aios-core/`
- **Tipo:** Meta-framework para orquestração de agentes de IA
- **Componentes:**
  - Sistema de agentes (aios-master, dev, qa, architect, pm, etc.)
  - Tasks executáveis
  - Workflows multi-step
  - Templates e checklists
  - Sistema de regras

### Claude Code
- **Configuração:** `.claude/`
- **Modo:** AIOS Master Agent
- **Funcionalidades:** Orquestração de desenvolvimento com suporte a agentes especializados

### Ferramentas de Documentação Suportadas
- GitHub Markdown
- YAML (configurações)
- PDF (análises)
- Jupyter Notebooks (análises com código)
- Código executável (qualquer linguagem)

---

## 🎯 Definição de um AI Master

Segundo o projeto, um AI Master é um profissional que:

### 4 Princípios Fundamentais

1. **Entende o Problema de Negócio**
   - Antes de abrir qualquer ferramenta
   - Contexto é rei

2. **Usa IA Generativa como Alavanca**
   - Não como muleta
   - Uso estratégico

3. **Entrega Soluções Funcionais**
   - Não apresentações bonitas
   - Output é acionável

4. **Sabe o Que Automatizar e o Que Não**
   - Julgamento crítico
   - Discernimento estratégico

---

## 📋 Checklist de Submissão

### Antes de Abrir o PR

- [ ] Escolheu um challenge e leu o README completo
- [ ] Solução está na pasta `submissions/seu-nome/`
- [ ] Incluiu process log com evidências de IA
- [ ] README segue o template em `templates/submission-template.md`
- [ ] Se construiu código, incluiu instruções de setup
- [ ] Não modificou nenhum arquivo fora da pasta

### Título do PR
Formato obrigatório: `[Submission] Seu Nome — Challenge XXX`

Exemplo: `[Submission] João Silva — Challenge 003`

---

## 📚 Recursos Adicionais

### Documentação Interna
- **AIOS Constitution:** `.aios-core/constitution.md`
- **Agent Authority Rules:** `.claude/rules/agent-authority.md`
- **Workflow Execution:** `.claude/rules/workflow-execution.md`
- **Story Lifecycle:** `.claude/rules/story-lifecycle.md`

### Convenções de Commit
- **Tipo:** `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
- **Formato:** `type: description [Issue/Story ID]`
- **Exemplo:** `feat: add challenge 001 baseline [G4-001]`

### Integração com Git
- **Plataforma:** GitHub
- **Fluxo:** Fork → Branch → Submissão via PR
- **Autenticação:** GitHub CLI (gh)

---

## 🔗 Links Importantes

| Recurso | URL |
|---------|-----|
| G4 Educação | https://g4educacao.com |
| Desafios | `./challenges/README.md` |
| Template | `./templates/submission-template.md` |
| Issues | GitHub Issues (no repositório) |

---

## 📈 Métricas do Projeto

| Métrica | Valor |
|---------|-------|
| Número de Desafios | 4 |
| Commits Analisados | 5 |
| Documentos de Submissão | 3 principais |
| Formatos de Process Log | 6 aceitos |
| Autores | 1 (João Vitor Chaves Silva) |
| Branches Detectadas | 2 (main, submission/gscopetti) |
| Arquivos Rastreados | 20+ |
| Arquivos Não Rastreados | 9 |

---

## 🎓 Como Usar Este Documento

Este arquivo serve como **auditoria completa** do projeto:

1. **Para Entender a Estrutura** → Veja seção "Estrutura do Projeto"
2. **Para Entender o Processo** → Veja seções "Regras de Submissão" e "Formato de Submissão"
3. **Para Saber o Que Será Avaliado** → Veja seção "Critérios de Avaliação"
4. **Para Acompanhar Histórico** → Veja seção "Histórico de Commits"
5. **Para Submeter** → Use checklist "Checklist de Submissão"

---

## 📅 Informações de Auditoria

- **Data de Geração:** 2026-03-24 09:00 UTC
- **Agente Gerador:** Orion (aios-master)
- **Tipo de Auditoria:** Auditoria Completa de Projeto
- **Status:** Ativo
- **Próxima Revisão:** Recomendado a cada nova submissão

---

*Auditoria gerada automaticamente pelo AIOS Master Framework. Para atualizações, execute novamente o comando de auditoria.*
