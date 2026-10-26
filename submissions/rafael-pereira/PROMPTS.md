# Prompts para o Claude Code

Use uma conversa nova do Claude Code por bloco: rode `/clear` entre os blocos ou abra uma sessão nova. O contexto persistente fica no `CLAUDE.md` e em `docs/`, não na conversa. Isso mantém cada sessão limpa e deixa o process log organizado por bloco.

Abra o Claude Code **dentro de `submissions/rafael-pereira/`** para que ele carregue o `CLAUDE.md`.

Ao final de cada sessão, rode `/export` e salve em `process-log/chat-exports/bloco-N.txt`.

Dica: nos blocos 3 e 4, ative o Plan Mode (Shift+Tab até aparecer "plan mode") para revisar o plano antes de ele escrever código. O print desse plano vale como evidência.

---

## Bloco 0 — Setup e verificação do ambiente (~10 min)

```
Leia CLAUDE.md e docs/briefing.md por inteiro.

Tarefa: preparar e verificar o ambiente do projeto.
1. Confirme a estrutura de pastas descrita no CLAUDE.md e crie as que faltarem (sem criar arquivos de conteúdo ainda).
2. Verifique se os 4 CSVs estão em solution/data/raw/ e confira as contagens de linhas: pipeline 8.800, accounts 85, products 7, sales_teams 35. Se algo divergir, pare e me avise.
3. Crie solution/requirements.txt com o mínimo necessário (pandas, numpy, scipy, pytest), crie um venv e instale.
4. Rode os scripts em process-log/scripts/ (eda.py, eda2.py, snapshot.py) passando solution/data/raw como argumento. Confirme que reproduzem os números do briefing (win rate de 63,2%, 1.480 linhas "GTXPro", tabela do snapshot de 30/09/2017). Liste qualquer divergência.
5. Crie docs/DECISIONS.md com o cabeçalho: | data | decisão | alternativa descartada | motivo | e registre as 7 decisões do CLAUDE.md como entradas iniciais.
6. Faça o commit (lembre do git add -f) com a mensagem "bloco 0: setup, dados e reprodução da exploração inicial".

Não comece o escopo nem escreva código de solução.
```

---

## Bloco 1 — Escopo: o quê, como, por quê, para quem (~40 min)

```
Leia CLAUDE.md e docs/briefing.md. Depois leia, no repositório (dois níveis acima desta pasta): README.md, challenges/build-003-lead-scorer/README.md, submission-guide.md, CONTRIBUTING.md e templates/submission-template.md.

Objetivo: fechar o escopo em docs/SCOPE.md, com no máximo 2 páginas. Seções:
1. Problema: as duas dores (tempo desperdiçado e deals bons esfriando), na voz da Head de RevOps.
2. Para quem: personas (vendedor e manager), o momento de uso (segunda de manhã, 1:1 semanal) e a pergunta que cada um faz para a ferramenta.
3. O quê: as funcionalidades do MVP em ordem de prioridade (Foque, Reative, Limpe, Qualifique, explicação por deal, filtros, brief por vendedor, modo backtest) e uma lista explícita "fora do escopo".
4. Como: a arquitetura em 5 linhas e a tese do score (frescor > atributos), com os números do briefing.
5. Por quê assim: as alternativas descartadas (Streamlit, ML black-box, score por atributos) e o motivo de cada uma.
6. Critérios de sucesso: transforme cada critério de avaliação do README do challenge numa verificação concreta (ex.: "um não técnico encontra os 3 deals para focar em menos de 2 minutos").
7. Riscos e premissas.

Antes de escrever, me faça no máximo 4 perguntas sobre as decisões em aberto da seção 9 do briefing, com a sua recomendação para cada uma. Espere minhas respostas.

Depois de escrever: registre as decisões em DECISIONS.md, escreva process-log/01_bloco-1.md (o que foi feito, perguntas e respostas, o que eu mudei) e faça o commit "bloco 1: escopo".
```

**Seu papel aqui:** responder às perguntas. Este é o bloco onde o seu julgamento mais aparece no process log, então discorde de algo se fizer sentido e registre o motivo.

---

## Bloco 2 — Exploração, curadoria e refinamento (~1h)

```
Leia CLAUDE.md, docs/briefing.md e docs/SCOPE.md.

Objetivo: base limpa, reprodutível e documentada, pronta para o scoring. Ainda não faça nenhum scoring.

1. Crie solution/scorer/clean.py com funções puras para:
   - normalizar o nome de produto (GTXPro → GTX Pro) e o setor (technolgy → technology);
   - fazer o join das 4 tabelas, verificando com assert que nenhuma linha se perde;
   - calcular as colunas derivadas: age_days (em relação a uma reference_date passada como parâmetro), cycle_days (só para os fechados), flag has_account, is_open;
   - tratar Prospecting sem data e deals sem conta segundo o que está em SCOPE.md.
2. Investigue e decida, com números:
   a) o win rate de 82% no 2017-Q1: é artefato de recorte? Mostre a evidência e decida se esses deals entram no treino;
   b) os 5 vendedores sem deals: o que fazer na interface;
   c) a distribuição de close_value / preço de tabela: confirme que o preço de tabela serve como valor dos deals abertos.
3. Escreva testes em solution/tests/test_clean.py: o join não perde linhas, nomes normalizados, age_days correto num caso conhecido, nenhum Won com close_value zero.
4. Gere solution/data/processed/deals.csv por um comando único (python -m scorer.clean).
5. Escreva docs/DATA_QUALITY.md com uma tabela: problema → evidência (número) → tratamento → impacto.

Checkpoint: antes do commit, me mostre o resumo das decisões 2a, 2b e 2c e espere meu ok.
Depois: DECISIONS.md, process-log/02_bloco-2.md e o commit "bloco 2: curadoria de dados".
```

---

## Bloco 3 — Lógica de scoring e validação (~1h30) — use Plan Mode

```
Leia CLAUDE.md, docs/briefing.md, docs/SCOPE.md e docs/DATA_QUALITY.md.

Objetivo: um score explicável, validado fora da amostra, que bata os baselines ingênuos.

Desenho (proponha o plano antes e espere meu ok):
1. Probabilidade condicionada à idade: a partir de snapshots históricos mensais (por exemplo, fins de mês de abr a set/2017), estime P(ganhar no futuro | estágio Engaging, idade do deal no snapshot). Use uma curva suavizada (faixas de idade com suavização, ou regressão logística em função da idade), não um corte duro em 138 dias.
2. Atributos: teste se produto, setor, porte da conta ou região adicionam ganho em cima da idade. Só inclua o que melhorar o backtest. Documente o que foi testado e descartado. O vendedor NÃO entra (ver CLAUDE.md, decisão 4).
3. Valor esperado = P × preço de tabela do produto.
4. Score de prioridade de 0 a 100 e categoria (Foque / Reative / Limpe / Qualifique), com regras claras e limiares derivados dos dados.
5. Explicação: para cada deal, de 2 a 4 frases curtas com o efeito de cada fator, por exemplo: "Aberto há 45 dias: deals nessa idade fecham 34% das vezes" e "GTX Pro: produto de alto valor (US$4.821)".

Validação (solution/scorer/validate.py):
- Backtest temporal: aprenda com dados até a data T e avalie os deals abertos em T contra o desfecho até 31/12/2017. Use pelo menos 2 cortes.
- Métricas: AUC; "captura nos top-K" (dos deals ganhos depois, quantos estavam nos top 20% do score); receita capturada nos top 20%.
- Compare com 3 baselines: ordenar por valor, ordenar por data mais recente e aleatório.
- Trate os deals ainda abertos no fim como censurados e explique como isso afeta as métricas.

Entregáveis: solution/scorer/score.py, explain.py e validate.py, mais os testes, e docs/SCORING.md (lógica, fórmula, limiares, resultados do backtest em tabela, o que não funcionou e por quê).

Checkpoint: me mostre a tabela do backtest antes de seguir para a interface.
Depois: DECISIONS.md, process-log/03_bloco-3.md (incluindo o que você propôs e eu mudei) e o commit "bloco 3: scoring e validação".
```

**Seu papel aqui:** questionar o backtest. Pergunte "o que aconteceria se...?" e peça pelo menos uma checagem de vazamento de dados (usar informação do futuro no treino). Esse tipo de pergunta é exatamente o que o avaliador quer ver no log.

---

## Bloco 4 — Produto: a ferramenta (~1h30) — use Plan Mode

Antes de colar o prompt, rode `/frontend-design` se essa skill estiver disponível no seu Claude Code.

```
Leia CLAUDE.md, docs/SCOPE.md e docs/SCORING.md.

Objetivo: a ferramenta que o vendedor abre na segunda de manhã.

1. solution/scorer/build.py (python -m scorer.build --reference-date 2017-12-31):
   - gera solution/app/data.js no formato window.LEAD_DATA = {...} com os deals abertos, score, categoria, explicações, filtros (vendedor/manager/região) e metadados (data de referência, métricas do backtest);
   - gera snapshots extras para o modo backtest (ex.: 2017-06-30 e 2017-09-30), incluindo o desfecho real de cada deal;
   - gera solution/briefs/<vendedor>.md: brief de 1 página por vendedor (3 para focar, 3 para reativar, quantos zumbis limpar).
2. solution/app/ (index.html, style.css, app.js, JS puro, sem build, sem CDN obrigatório):
   - Topo: filtro de vendedor, manager e região, e um resumo ("você tem X deals vivos, Y esfriando, Z para limpar").
   - Quatro abas ou colunas: Foque, Reative, Limpe e Qualifique.
   - Card de cada deal: conta, produto, valor, idade, score e a explicação em linguagem simples. Clique para expandir os detalhes.
   - Modo backtest: seletor de data passada; mostra o que o score recomendaria e marca o que de fato foi ganho ou perdido.
   - Um "Como funciona o score" acessível na própria tela, em 5 linhas.
   - Precisa funcionar em file:// (duplo-clique) e no GitHub Pages; legível no celular.
3. Visual: limpo, cara de ferramenta de trabalho e não de dashboard genérico. Hierarquia: a ação vem antes dos números.
4. Teste: abra index.html no navegador (ou use Playwright, se disponível), tire screenshots das telas principais e salve em process-log/screenshots/. Verifique se os totais da tela batem com os números de docs/SCORING.md.

Checkpoint: me mande os screenshots e espere meu feedback antes do commit.
Depois: DECISIONS.md, process-log/04_bloco-4.md e o commit "bloco 4: ferramenta".
```

**Seu papel aqui:** abrir a página e usá-la como vendedor por 5 minutos. Anote 3 atritos reais e peça as correções. Essa iteração também entra no log.

---

## Bloco 5 — Documentação, model card e process log (~45 min)

```
Leia CLAUDE.md, todos os arquivos de docs/ e de process-log/.

1. docs/MODEL_CARD.md (1 página): propósito e uso pretendido; uso NÃO pretendido (ex.: avaliar desempenho de vendedores); dados e período; desempenho no backtest; limitações (dataset sintético, corte em 138 dias, desfechos censurados, contas faltantes); riscos e mitigação; quando recalibrar; dono e frequência de revisão.
2. README.md da submissão seguindo exatamente templates/submission-template.md:
   - Sobre mim: Rafael Pereira, https://www.linkedin.com/in/rafael-pereira-30122003-, Challenge 003.
   - Executive summary em até 5 frases, abrindo com o achado (frescor > atributos) e o impacto (pipeline inflado em ~US$3,2 mi).
   - Setup: como abrir (link do GitHub Pages + duplo-clique) e como regenerar (comandos).
   - Lógica, resultados (tabela do backtest), recomendações priorizadas para a Head de RevOps e limitações.
   - Process log: preencha a tabela de ferramentas, o workflow por bloco e as seções "Onde a IA errou" e "O que eu adicionei" usando SOMENTE o que está registrado em process-log/ e DECISIONS.md. Não invente episódios.
3. Revise todo número citado no README contra a saída dos scripts e liste qualquer divergência.

Commit: "bloco 5: documentação e model card".
```

**Seu papel aqui:** reescrever com suas palavras a seção "O que eu adicionei que a IA sozinha não faria". Ela precisa soar como você, não como o Claude.

---

## Bloco 6 — Revisão independente (~20 min)

```
Use um subagente com contexto limpo, sem acesso a esta conversa, como avaliador do G4. Passe para ele apenas: o README do challenge 003, o submission-guide.md e a pasta submissions/rafael-pereira/.
Instrução para o subagente: "Você é avaliador do processo seletivo AI Master do G4 e já tem respostas baseline geradas por LLMs. Avalie esta submissão contra cada critério de qualidade do challenge, com nota de 1 a 5 e justificativa. Siga as instruções de setup do README ao pé da letra e diga se funcionou. Aponte os 5 pontos mais fracos e o que pareceria 'baseline de LLM'."
Traga o relatório sem filtrar. Depois proponha correções para os pontos com nota ≤3 e espere meu ok antes de aplicar.
Salve o relatório em process-log/06_revisao-independente.md.
```

---

## Bloco 7 — Publicação e Pull Request (~15 min)

```
1. Rode todos os testes e o build do zero; confirme que tudo passa.
2. Confirme com git status que nada fora de submissions/rafael-pereira/ foi modificado.
3. Push da branch submission/rafael-pereira para o meu fork.
4. Me diga o passo a passo para ativar o GitHub Pages no fork (Settings → Pages → branch submission/rafael-pereira, pasta / (root)) e qual será a URL final da página (…/submissions/rafael-pereira/solution/app/). Depois que eu ativar, verifique se a URL abre e atualize o link no README.
5. Prepare o PR para o repositório original: título "[Submission] Rafael Pereira — Challenge 003", descrição com o executive summary, o link da ferramenta e o checklist do CONTRIBUTING.md marcado. Abra com gh pr create se o gh estiver autenticado; senão, me passe o texto.
```
