# Process Log — Challenge 002 (Redesign de Suporte)

**Candidato:** Pedro Henrique
**Vaga:** AI Master — G4 Educação
**Data:** 27–28 de maio de 2026
**Solução escolhida:** Challenge 002 — Redesign de Suporte (Operações / CX)

> Este documento é a evidência de como usei IA para chegar à solução: quais ferramentas usei e por quê, como decompus o problema antes de promptar, onde a IA errou e como corrigi, o que adicionei que a IA sozinha não faria, e quantas iterações foram necessárias. As afirmações abaixo são rastreáveis nos arquivos de `chat-exports/` (Codex, Manus AI e Perplexity) anexados nesta mesma pasta.

---

## 1. Resumo executivo

Tratei o desafio como um produto, não como um script. Em vez de delegar tudo a um único prompt, montei uma **pipeline de IAs especializadas**, cada uma fazendo a parte em que é melhor:

- **Claude Cowork (modelom Opus 4.7)** — discovery, leitura macro do repositório, planejamento estratégico e curadoria de escopo.
- **Perplexity** — pesquisa técnica para nomear e validar uma ideia que tive (um insight).
- **Manus AI** — construção da base de conhecimento real do G4, fiz um scrapper do site completo para usar como modelo de fonte de embeddings.
- **Codex (GPT-5.3-Codex) + GitHub Spec Kit** — desenvolvimento bruto do MVP (Next.js + Supabase + OpenAI), onde precisava de assertividade e economia de tokens.

O resultado foi um MVP funcional deployado na Vercel, com diagnóstico de dados dos dois datasets do Kaggle.

---

## 2. Quais ferramentas de IA usei e por quê

| Ferramenta | Papel | Por que esta e não outra |
|---|---|---|
| **Claude Cowork (Opus 4.x)** | Planejamento, discovery, decisão de escopo, gestão do projeto via ClickUp | Subi todo o repositório do desafio como projeto. Troquei de Sonnet para Opus de propósito para gerar respostas mais assertivas na análise estratégica dos datasets e decisões mais difíceis. |
| **Perplexity** | Pesquisa: "essa técnica tem nome?" | Eu já tinha o insight do produto (resolver a dor antes de virar ticket). Precisava confirmar que existia um padrão estabelecido e o nome dele para não reinventar a roda nem soar genérico. |
| **Manus AI** | Crawl do site do G4 + montagem da base de conhecimento | Para o RAG ser honesto, a base precisava ter conteúdo real do G4 (cursos, FAQ operacional, G4 Tools), não lorem ipsum. Manus navega e extrai conteúdo de site de forma autônoma. |
| **Codex (GPT-5.3-Codex) + Spec Kit** | Build do MVP | Já usei Codex + Spec Kit para aplicações reais de clientes e ele se sai muito bem com fluxo `specify → plan → tasks`. Mais assertividade no código bruto e economia de tokens vs. fazer tudo no chat de planejamento. |

**Insight de método (registrado no ClickUp):** usar Claude Cowork para *planejamento e esboço da solução* e Codex + Spec Kit para *desenvolvimento bruto*. Separar "pensar" de "construir" rendeu mais qualidade nas duas pontas.

---

## 3. Como decompus o problema antes de promptar

Não comecei indo direto ao Codex ou Claude. Comecei lendo com calma cada instrução, desde o e-mail a cada arquivo do repo. A sequência real (registrada como checklist nas tasks do ClickUp):

1. Li o e-mail do processo.
2. Revisitei os detalhes da vaga.
3. Abri meu ClickUp e criei uma pasta nova para o desafio.
4. Setei as tasks iniciais (cada passo virou uma atividade rastreável).
5. Li toda a documentação do desafio.
6. Subi todo o detalhamento e os arquivos do repositório em um projeto novo no Claude Cowork.
7. Fiz uma **leitura macro** do repositório com a IA.
8. Em paralelo, li **eu mesmo, com calma**, cada um dos quatro challenges.
9. **Escolhi o Redesign de Suporte** — porque na leitura macro já tinha tido insights (anotei na hora nas tasks) e porque tenho experiência prática com a lógica de RAG: já construí um fluxo no n8n usando embeddings (Supabase Vector Store) para montar um FAQ assertivo no WhatsApp. Eu sabia, na prática, o que é transformar texto em coordenadas vetoriais num espaço de N dimensões e gerar resposta a partir disso.
10. Esse Discovery levou ~1h30 (tempo cronometrado em task do ClickUp).

O insight de produto que orientou tudo (anotado antes de promptar qualquer build): *o valor real para o cliente não é abrir um ticket — é não precisar abrir, recebendo uma solução no instante da dor.* Gravação por áudio → transcrição (Whisper) → RAG sobre a base de resolução → solução sugerida antes do ticket existir.

---

## 4. Onde a IA errou e como corrigi

**4.1 Dashboard com números inventados (mock).**
O Codex entregou a primeira versão do dashboard admin com valores *mock*. Eu questionei diretamente: "os valores na dash são de fato fruto da análise dos datasets? como você fez essa análise?". A IA admitiu que eram mock. Forcei a construção de um script Python (`analyze_datasets.py`) que processa os CSVs reais do Kaggle e gera `insights.json` com um campo `data_source` explícito (análise real vs. fallback). **Sem essa correção, o diagnóstico seria desclassificável.**

**4.2 Pipeline caindo em fallback silencioso.**
Mesmo com o script pronto, ele caía em fallback por falta de `kagglehub` / token Kaggle, e depois por incompatibilidade `kagglehub + kagglesdk` no Python 3.14. A IA tentou: rodar sem auth, criar venv 3.12, pinar versões — várias tentativas. Eu desbloqueei fornecendo o **token real do Kaggle**, que organizamos num `.env.local`. Só então a análise real rodou.

**4.3 Vazamento de alvo (target leakage) na análise de CSAT.**
A IA gerou os "drivers de satisfação" usando o próprio `csat` como feature e incluindo colunas identificadoras — chegou a apontar **`Ticket ID` como driver de CSAT**, o que é estatisticamente sem sentido (não é causal). Sinalizei/validei e mandei remover colunas identificadoras e o vazamento. Isso é exatamente o tipo de erro que separa "diagnóstico com número concreto" de "número errado com cara de concreto".

**4.4 Parsing de tempo quebrado.**
`resolution_hours` vinha vazio porque os tempos estavam em formato textual no CSV. Corrigimos a extração (parsing de duração + fallback por diferença de timestamps) e regeneramos os números.

**4.5 Erros de engenharia que travariam a entrega.**
- Erro de **hidratação** no React (`typeof window` no render) → resolvido com hook `useSyncExternalStore`.
- Deploy na Vercel falhando com `npm ci` → causa real: **Root Directory** apontando para a raiz do repo em vez de `submissions/pedro-henrique-silva/solution`. Corrigido + Node fixado em 20.x.
- Erro 403 pós-deploy → era das **minhas próprias regras** de rate limiting / bloqueio de tráfego fora do Brasil / anti-bot que eu havia ativado; instruí a IA a **não desativá-las** e resolver em volta.
- `.gitignore` da raiz ignorava `submissions/` — a IA me alertou que `git status` ficaria limpo e que eu precisaria de `git add -f`. Detalhe que teria feito o PR sair vazio.
- Cards de "respostas rápidas" continuavam exibindo conteúdo antigo/fictício mesmo após eu pedir a troca — precisei reapontar a base de conhecimento real (PDF do G4) **mais de uma vez** até alinhar.

---

## 5. O que eu adicionei que a IA sozinha não faria

- **A escolha do desafio e a tese de produto.** A IA não teria decidido que "o melhor ticket é o que não precisa existir". Isso veio da minha experiência com RAG/embeddings no n8n e basicamente de um insight que tive na hora que estava lendo os challenge.
- **A arquitetura de múltiplas IAs.** Orquestrar Cowork (planejar) + Perplexity (pesquisar) + Manus (base de conhecimento) + Codex/Spec Kit (build) foi decisão minha, para extrair o melhor de cada uma.
- **O ceticismo com os dados.** Foi a minha pergunta ("esses números são reais?") que transformou um dashboard bonito-porém-falso em análise real dos datasets.
- **Saber onde parar a automação.** Com a ideia de ter uma análise via embeddings de tickets já resolvidos, FAQs previamnete cadastrados, conseguimos, de antemão, já dar uma resposta imediata ao usuário. Se necessário, aí sim escalamos para um humano.
- **A base de conhecimento real do G4.** Em vez de FAQ genérico, usei conteúdo verdadeiro do site (cursos, G4 Tools, casos operacionais hipotéticos plausíveis) para o RAG ser honesto.
- **Gestão e rastreabilidade.** Cada passo virou task com tempo cronometrado no ClickUp — a evidência deste process log existe porque eu instrumentei o processo. Depois de um tempo parei de "trackear" pois fiquei bem ocupado.

---

## 6. Quantas iterações foram necessárias

| Frente | IA | Iterações (turnos do usuário) | O que aconteceu |
|---|---|---|---|
| Discovery + planejamento | Claude Cowork | ~1h30 de leitura + planejamento contínuo | Escolha de escopo, troca Sonnet→Opus, definição do MVP |
| Pesquisa da técnica | Perplexity | **3** | Confirmou nome (RAG + ASR + NLU / smart triage / post-call analytics) |
| Base de conhecimento | Manus AI | **5** | Crawl do G4, FAQ operacional, G4 Tools, ajustes, export |
| Build do MVP | Codex + Spec Kit | **~47 turnos / 264 mensagens** | Scaffold → análise real → redesign visual (tema ATS) → tradução PT-BR → correções → deploy Vercel |

No Codex, a curva foi: 1 turno de planejamento (Spec Kit gerando `spec/plan/tasks`), 1 de scaffold, e o restante quase todo de **refinamento iterativo** — dados reais, identidade visual fiel ao site de carreiras do G4, responsividade, português em toda a UI, correções de build/deploy e ajustes finos de layout pedidos por mim um a um. Ou seja: a primeira versão funcional veio rápido, mas a **versão correta** exigiu dezenas de correções minhas. Foi exatamente aí que entrou o valor de AI Master — não em gerar, mas em **julgar, corrigir e direcionar**.

---

## 7. Conclusão

A IA acelerou drasticamente a execução, mas sozinha entregaria um produto bonito com dados falsos, com target leakage e com FAQ genérico. O diferencial foi humano: escolha estratégica do desafio, ceticismo com os números, detecção de erros analíticos, orquestração de quatro IAs para os fins certos e disciplina de rastrear cada passo. O baseline de "IA crua" não chega a um diagnóstico com dados reais dos dois datasets, um MVP deployado e um critério explícito de onde a automação deve parar.

---

### Anexos rastreáveis (nesta pasta)
- `chat-exports/chat-export-2026-05-28-CODEX.md` — log literal do build (264 mensagens / 47 turnos)
- `chat-exports/chat-export-2026-05-28-MANUS_AI.md` — construção da base de conhecimento do G4
- `chat-exports/chat-export-2026-05-28-PERPLEXITY.md` — pesquisa e validação da técnica (RAG + ASR + NLU)
