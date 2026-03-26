# Process Log

## Ferramenta de IA principal

**GitHub Copilot (GPT-4.5 no modo Agent)** — utilizado dentro do VS Code durante toda a sessão de trabalho.

---

## Etapa 1 — Leitura do escopo antes de escrever qualquer linha

**O que fiz antes de promptar:** Li o README do challenge, o submission-guide e o CONTRIBUTING para entender exatamente o que seria avaliado. Só depois abri o Copilot.

**Por que essa ordem importa:** Promptar sem entender o problema gera saída genérica. Eu precisava saber que o deliverable era _software funcionando_, não análise, e que o process log era obrigatório e desclassificatório se ausente.

**Prompt inicial usado:**
```
me candidatei para um emprego de AI Master, e me deram um desafio a cumprir
[link do repositório]
o template de submissão é esse [link]
as instruções em CONTRIBUTING.md [link]
e o guia de submissão [link]
e o desafio q escolhi é [link do build-003-lead-scorer]
```

**O que o Copilot fez:** Buscou os 4 recursos do GitHub, revisou o challenge, e planejou a execução em 6 etapas começando pelo clone do repositório base. Isso está documentado no screenshot abaixo.

**Screenshot:** [`screenshots/01-copilot-challenge-briefing.png`](screenshots/01-copilot-challenge-briefing.png)

O print mostra o painel de chat do Copilot Agent com os links fornecidos, a resposta "Vou levantar o escopo do desafio e os critérios de submissão primeiro, para estruturar a entrega corretamente antes de escrever qualquer arquivo", e o início da execução ("Clonar repo base — 1/6"), com confirmação de que o Copilot buscou os 4 recursos e revisou a estrutura de memória do repositório.

---

## Etapa 2 — Exploração dos dados reais

**O que fiz antes de promptar:** Confirmei a estrutura das 4 tabelas lendo os cabeçalhos dos CSVs manualmente para ter contexto próprio.

**Prompt usado:**
```
explore os 4 CSVs e me dê: schema completo, distribuição de deal_stage,
win rate histórico, problemas de qualidade de dado que possam afetar joins
```

**O que o Copilot entregou:**
- Schema das 4 tabelas com tipos inferidos
- Win rate histórico de ~63,2% nos deals fechados
- 2.089 deals abertos no pipeline
- Identificação do mismatch de produto: `GTXPro` no pipeline vs `GTX Pro` no catálogo
- Contas ausentes em parte do pipeline (coluna `account` com NaN)

**Onde eu corrigi o Copilot:** A primeira sugestão dele foi fazer o join direto na coluna `product`. Eu rejeitei porque o mismatch identificado causaria perda de registros. Pedi explicitamente uma função de normalização por regex antes do join.

**Resultado no código:**
```python
def normalize_product_name(value: object) -> str:
    text = "" if pd.isna(value) else str(value)
    return re.sub(r"[^a-z0-9]+", "", text.lower())
```

---

## Etapa 3 — Decisão de arquitetura do score

**Julgamento humano que a IA não tomou sozinha:** O Copilot sugeriu começar com um modelo de classificação (Random Forest ou LogisticRegression). Eu recusei.

**Meu raciocínio:** O challenge pedia algo funcional e explicável em 4–6 horas. Um modelo supervisionado com CV e calibração tomaria o dobro do tempo e produziria um score opaco. A Head de RevOps no enunciado disse explicitamente que queria que o vendedor entendesse _por que_ o deal tem score alto.

**Prompt que usei para redirecionar:**
```
não quero modelo supervisionado. quero score heurístico com pesos explícitos,
smoothing bayesiano por grupo, e que eu consiga explicar cada componente
para um vendedor não-técnico. monte a estrutura de pesos
```

**O que o Copilot propôs e o que eu mudei:**
- Copilot propôs valor financeiro com peso 20%. Reduzi para 5% — o deal de maior valor não é necessariamente o mais provável de fechar.
- Copilot propôs peso igual para vendedor e região. Aumentei o peso de vendedor (18%) e reduzi região (8%) porque variância individual de conversão é maior que variância geográfica no dataset.
- O `min_weight=15` no smoothing foi minha decisão: com grupos pequenos (alguns vendedores têm menos de 10 deals fechados), o prior global precisa pesar mais para evitar overfitting em pequenas amostras.

---

## Etapa 4 — Implementação da aplicação Streamlit

**Prompt usado:**
```
cria app.py em Streamlit com: filtros por região/manager/vendedor/stage,
tabela ranqueada por priority_score, breakdown dos componentes do score
para cada deal selecionado, ação recomendada, e aba de visão por time
```

**O que o Copilot entregou de primeira:** Estrutura do app com sidebar, tabela e detalhe por deal. Funcionou, mas a lógica de `recommend_action` era binária (só "Follow up" ou "Qualify").

**O que eu adicionei:** Lógica contextual baseada em tier + age do deal + stage combinados — por exemplo, deals `Hot` em `Engaging` recebem "Agendar fechamento esta semana" enquanto deals `Hot` mas envelhecidos recebem "Renegociar ou qualificar urgente".

---

## Etapa 5 — Testes e ajustes finais

**Problema encontrado:** O app quebrava quando todos os deals de um filtro tinham o mesmo `deal_age_days` (edge case com `percentile_score` retornando divisão implícita por zero no ranking).

**Como corrigi:** Adicionei guarda na função `percentile_score`:
```python
if series.nunique(dropna=False) <= 1:
    return pd.Series(0.5, index=series.index)
```

**Segundo problema:** Deals sem `engage_date` recebiam `NaN` no freshness, quebrando o score final. Corrigi setando valor neutro-baixo (0.40) explicitamente para esses casos, em vez de confiar no `fillna` genérico downstream.

---

## Resumo das iterações

| # | O que a IA fez | O que eu corrigi ou adicionei |
|---|----------------|-------------------------------|
| 1 | Levantou escopo e planejou execução buscando os 4 recursos do repositório | Validei o plano antes de aprovar cada etapa |
| 2 | Identificou schema e anomalias dos CSVs | Rejeitei o join direto; exigi normalização de produto primeiro |
| 3 | Propôs modelo supervisionado e pesos iniciais | Reorientei para heurística explicável; ajustei pesos manualmente |
| 4 | Gerou estrutura do app Streamlit | Adicionei lógica contextual no `recommend_action` |
| 5 | Gerou primeira versão do scoring pipeline | Corrigi dois edge cases que quebravam o app com filtros específicos |

---

## O que a IA sozinha não teria feito

- A decisão de rejeitar ML supervisionado em favor de heurística explicável veio do entendimento do que o avaliador quer ver, não de análise técnica.
- Os pesos finais refletem julgamento sobre o negócio (stage domina porque maturidade comercial é o sinal mais confiável), não apenas o que o código produzia.
- A estrutura autocontida da submissão (CSVs dentro de `solution/data/`) foi uma decisão minha para facilitar a avaliação sem dependência de setup externo.

---

## Etapa 6 — Iteração após feedback do avaliador

**Feedback recebido:**
> "A evidência do processo de trabalho com IA está insuficiente — reveja o que o challenge pede nesse quesito. As decisões de modelagem precisam ter sua origem mais clara no repositório."

**Como usei IA para responder ao feedback:** Abri uma nova sessão do Copilot Agent com o feedback como contexto, e pedi que ele lesse os arquivos atuais da submissão e identificasse exatamente o que estava faltando em relação ao que o `submission-guide.md` pedia.

O Copilot leu o `narrative.md` original, o `scoring-logic.md`, o `submission-guide.md` e o README do challenge, e apontou os dois gaps:
1. O process log descrevia etapas em alto nível mas não mostrava prompts reais, correções feitas nem onde a IA errou
2. O scoring-logic listava os pesos mas não explicava a origem de cada decisão nos dados

Em seguida, usei o Copilot para reescrever os dois arquivos com base no código real (`lead_scoring.py`) e nos screenshots disponíveis — mantendo controle sobre o que afirmar, sem inventar iterações que não aconteceram.

**Screenshot:** [`screenshots/02-copilot-pr-update-iteration.png`](screenshots/02-copilot-pr-update-iteration.png)

O print mostra: o feedback do avaliador visível no painel de chat do Copilot, o terminal executando a reescrita do `narrative.md`, e o todo list com as tarefas de atualização do PR concluídas — evidência da sessão de trabalho com IA para responder ao feedback.

---

## Evidências adicionais (gravação + prints sequenciais)

Além dos dois screenshots anteriores, estão disponíveis uma gravação de tela completa e três prints sequenciais que documentam a sessão original de construção da solução no Windows com VS Code + Copilot Agent (GPT-4.5).

### Gravação de tela

**Arquivo:** [`screen-recording-full-session.mp4`](screen-recording-full-session.mp4)

Gravação da sessão completa de trabalho com o Copilot Agent, cobrindo todas as etapas: leitura do escopo, exploração dos dados, implementação do scoring e criação da submissão.

### Screenshots sequenciais

**[`screenshots/03-copilot-scope-todos-created.png`](screenshots/03-copilot-scope-todos-created.png)**

Etapa 1/6 — Copilot Agent após receber os 5 links do challenge. Mostra: o prompt inicial completo visível no chat, a resposta "Vou levantar o escopo do desafio e os critérios de submissão primeiro, para estruturar a entrega corretamente antes de escrever qualquer arquivo", a confirmação "Fetched 4 resources" e "Created 6 todos" com o plano de execução estruturado.

**[`screenshots/04-copilot-data-inspection-gtxpro-fix.png`](screenshots/04-copilot-data-inspection-gtxpro-fix.png)**

Etapa 2/6 — Copilot inspecionando os CSVs. Mostra: prompt "coloquei os arquivos necessários na pasta #file:data", o Copilot usando MCP server para ler os 4 arquivos ("Read data"), identificação do bug de dado crítico ("o pipeline usa GTXPro sem espaço, enquanto a tabela de produtos usa GTX Pro — vou incorporar normalização de chaves para não quebrar o join nem distorcer o score"), e o início da análise de distribuição de estágios e win rate.

**[`screenshots/05-copilot-readme-final-review.png`](screenshots/05-copilot-readme-final-review.png)**

Etapa final — Copilot recebendo os dados pessoais e fazendo a revisão final da submissão. Mostra: o LinkedIn e nome completo passados no chat, o Copilot executando "Updating project documentation", "Reviewed 2 files", "Updated README.md and applied patch", e a checagem final de "Searched for regex and reviewed solution file" antes de passar o passo a passo do PR.
