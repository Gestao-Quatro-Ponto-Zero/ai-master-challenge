# Submissao — Pedro Lima — Challenge 003

## Sobre mim

- **Nome:** Pedro Lima
- **LinkedIn:** pedrolima11
- **Challenge escolhido:** Build 003 — Lead Scorer

---

## Executive Summary

Construi uma ferramenta funcional de priorizacao de deals para vendedores. O motor analisa 8.800 deals historicos e prioriza os 2.089 ativos usando 5 sinais com cascata de confianca, atingindo 63.6% de precisao no ranking (top 10% fecha 82% vs bottom 10% fecha 39%). 
O vendedor faz 'login', recebe um plano de acao numerado ("1. Ligue agora para 2 deals. Comece por Green-Plus."), e trabalha um kanban com drag & drop onde cada deal explica em linguagem simples por que esta ali. Recomendacao principal: rodar um piloto de 60 dias com um escritorio, comparando win rate dos vendedores que usam a ferramenta vs os que nao usam.

---

## Solucao

### Como rodar

```bash
# 1. Instalar dependencias
pip install pandas numpy kagglehub

# 2. Gerar os scores (opcional, scored_deals.json ja esta incluso)
cd submissions/pedro-lima/solution
python3 scoring_engine.py

# 3. Servir o dashboard
npx http-server . -p 8000 -c-1

# 4. Abrir no navegador
open http://localhost:8000
```

O motor consome dados da API do Kaggle via `kagglehub`. Se indisponivel, usa CSVs locais em `data/` como fallback.

### Abordagem

Comecei pelos dados, nao pela interface. Primeira descoberta: 68% dos deals ativos nao tem conta vinculada no CRM. Qualquer motor que dependa de setor/porte da conta falha para a maioria do pipeline. Isso redirecionou tudo.

**Decomposicao do problema:**

1. **Dados** — O que existe de verdade nos 8.800 deals? Quais campos estao preenchidos para todos?
2. **Sinais** — O que diferencia deals que fecham dos que nao fecham, usando apenas dados disponiveis?
3. **Confianca** — Como evitar que um vendedor com 2 wins em 2 deals pareca melhor que um com 80 em 100?
4. **Acao** — Como transformar um score numerico em algo que o vendedor entenda e use?

**Priorizacao:** Fiz o motor funcionar primeiro, dashboard depois. Iterei o motor 5 vezes antes de tocar no frontend.

| Versao | Mudanca | Precisao |
|--------|---------|----------|
| v1 | Pesos estaticos (produto, setor, porte) | 50.7% |
| v2 | Sinais derivados + suavizacao bayesiana | 57.2% |
| v3 | 11 sinais + cascata de proxies | 62.7% |
| v4 | Simplificacao para 5 sinais core | 57.3% |
| v5 | Cascata hierarquica com taxas raw | 63.6% |

A v3 tinha 11 sinais mas varios redundantes. A v4 simplificou demais. A v5 encontrou o equilibrio: 5 sinais com cascata de confianca que blenda taxa especifica com fallback conforme o volume de dados.

**O motor v5:**

Prioridade = 55% Chance + 25% Urgencia + 20% Valor

| Sinal de Chance | Peso | Fallback quando poucos dados |
|-----------------|------|------------------------------|
| Taxa do vendedor | 30% | Blend com media global se <20 deals |
| Vendedor x Produto | 25% | Blend com taxa_vendedor + taxa_produto se <10 deals |
| Relacionamento (conta) | 25% | Vendedor-Conta > Gestor-Conta > Vendedor-Setor > Global |
| Taxa do produto | 10% | Estavel, todos os 7 produtos tem >500 deals |
| Sazonalidade (mes) | 10% | Recua para media global se mes tem <100 deals |

Urgencia calibrada no historico (mediana Won = 57 dias): 0-30d = 0.3, 31-60d = 0.5, 61-90d = 0.7, 91-120d = 0.9, >120d = 1.0.

6 baldes de acao: Atacar Agora, Resgatar Hoje, Avancar Qualificacao, Trabalhar Esta Semana, Nutrir, Limpar Pipeline.

### Resultados / Findings

**Motor (backtest em 6.711 deals fechados):**

- Precisao do ranking: 63.6%
- Decis monotonicas: D1=82%, D2=75%, D3=71%, D4=67%, D5=67%, D6=60%, D7=58%, D8=58%, D9=55%, D10=39%
- Spread entre extremos: 43 pontos percentuais
- Distribuicao: 13 Atacar, 99 Resgatar, 83 Avancar, 1.303 Trabalhar, 589 Nutrir, 2 Limpar

**Dashboard:**

- **Login** — Vendedor seleciona seu nome, ve preview (escritorio, gestor, taxa, deals ativos)
- **Plano de acao numerado** — Passos concretos adaptados ao perfil: "1. Ligue agora para 1 deal pronto para fechar. Comece por Green-Plus. Total: R$ 550" / "2. Resgate 7 deals que estao esfriando (ate 172 dias). Sao R$ 11.1k em risco." / "3. Priorize as 16 contas que voce ja conhece (22% do pipeline)."
- **Kanban interativo com drag & drop** — 5 colunas (Fechar Agora, Resgatar, Avancar, Trabalhar, Nutrir). O vendedor arrasta cards entre colunas para sobrepor seu julgamento ao do motor. Ao soltar: cor da borda, barra de chance, contadores e resumos atualizam automaticamente. Exemplo: o motor classificou como "Trabalhar", mas o vendedor sabe que teve reuniao boa e move para "Fechar Agora".
- **Cards com explicacao** — Cada card mostra conta (ou "ID Oportunidade: XXXX" para deals sem cadastro), produto, barra de chance com cor da coluna, e explicacao em linguagem simples ("Ja vendeu para Cheers antes. Aberto ha 159 dias, risco alto."). Botoes "Ja contatei" (salva data em localStorage) e "Anotar" (expande com textarea persistente).
- **Modal "Resumo dos Deals"** — Botao no banner abre visao consolidada do pipeline. Cada bucket mostra quantidade, chance media, valor total e explicacao do motivo (ex: "Potencial real, mas passaram de 90 dias. Aja rapido."). Expande para listar cada deal com razao individual. Barra de total fixa no rodape.
- **Funil de vendas** — Prospeccao, Negociacao, Ganhos, Perdidos
- **Aba "Como Funciona"** — 6 secoes explicando o calculo sem termos tecnicos

**Findings dos dados:**

- 68% do pipeline ativo nao tem conta no CRM. Isso e um problema de processo, nao de dados.
- Vendedores variam de 38% a 72% de taxa de fechamento. A diferenca e enorme.
- A mediana de fechamento e 57 dias. Depois de 90 dias, a chance cai drasticamente.
- Apenas ~10 de 27 vendedores tem deals em Prospecting. A maioria opera so em Engaging.

### Recomendacoes

1. **Piloto de 60 dias** com um escritorio regional. Medir win rate antes/depois. Se os vendedores que seguem a priorizacao fecham mais, expandir.
2. **Resolver o problema de cadastro** — 68% dos deals sem conta e dado faltante, nao complexidade tecnica. Um campo obrigatorio no CRM resolve.
3. **Integrar com CRM** — Conectar ao Salesforce/HubSpot para dados em tempo real e feedback automatico.
4. **Feedback loop** — Usar sinais do vendedor (contatou, moveu coluna, anotou) para recalibrar o motor.

### Limitacoes

1. **Dados estaticos** — Snapshot do pipeline, nao atualiza em tempo real.
2. **68% sem conta** — O motor funciona (cascata preenche o gap), mas com menos sinais disponiveis para esses deals.
3. **Validacao in-sample** — 63.6% medido nos mesmos dados de calibracao. Cascata de confianca mitiga overfitting mas nao elimina.
4. **Sem ML** — Heuristicas calibradas, nao modelos. Para 8.800 deals e 7 produtos, heuristicas explicaveis competem com ML e o vendedor entende o resultado.
5. **Frontend single-file** — HTML/CSS/JS em um arquivo. Funciona, mas para escalar precisaria de framework e backend.

---

## Process Log — Como usei IA

> **Este bloco e obrigatorio.** Sem ele, a submissao e desclassificada.

### Ferramentas usadas

| Ferramenta | Para que usou |
|------------|--------------|
| Claude Code (Opus 4) | Desenvolvimento completo em sessao continua: analise exploratoria dos dados, design e iteracao do scoring engine (5 versoes), implementacao Python, construcao do dashboard HTML/JS/CSS, refinamento visual via preview integrado, download do logo oficial da G4, correcoes de ortografia |

Uma unica ferramenta. Uma sessao de trabalho. O preview integrado do Claude Code permitiu ver o dashboard rodando e corrigir em tempo real.

### Workflow

1. **Carreguei o dataset do Kaggle** via API (`kagglehub`). Pedi analise da estrutura. Descobri que `sales_pipeline.csv` e a tabela central com 8.800 deals, 4 stages, e que 1.425 deals ativos nao tem conta.

2. **Desenhei o motor v1** com pesos estaticos. 50.7% de precisao. Ruim. Pedi para adicionar sinais derivados dos dados.

3. **Iteracao v2-v3** — Adicionei suavizacao bayesiana e cascata de proxies. Precisao subiu para 62.7% com 11 sinais. Mas o motor ficou complexo.

4. **Iteracao v4-v5** — Simplifiquei para 5 sinais (v4: 57.3%, pior). Identifiquei o problema de dupla-suavizacao: confidence_blend sobre taxas bayesianas ja suavizadas converge tudo para a media. Forcei uso de taxas raw. v5: 63.6%.

5. **Dashboard v1 (index.html)** — 4 abas com visao de gestor, analytics, validacao. Funcional mas complexo demais para o vendedor.

6. **Dashboard v2 (index.html)** — Redesenhei do zero com foco no vendedor: login, plano de acao, kanban, explicacoes simples. Cada decisao de UX veio de pensar "o vendedor abre isso na segunda de manha, o que precisa ver?".

7. **Refinamentos finais** — Logo oficial G4 (baixei do site g4business.com), correcao ortografica, remocao de emojis, cores dinamicas no kanban, modal de resumo, rodada de polish para remover "cara de IA" (sombras excessivas, border-radius uniforme, textos verbosos).

### Onde a IA errou e como corrigi

1. **Dupla-suavizacao** — A IA aplicou confidence_blend em taxas bayesianas ja suavizadas. Tudo convergiu para a media, perdendo 6pp de precisao. Eu identifiquei comparando v3 vs v4 e forcei o uso de taxas raw na cascata.

2. **Scores comprimidos (0.42-0.59)** — Sem diferenciacao util. A IA nao percebeu. Eu olhei a distribuicao e pedi sinais multiplicativos mais fortes.

3. **88% dos deals em "Nutrir"** — Thresholds calibrados em valores teoricos, nao na distribuicao real. Eu recalibrei olhando os dados.

4. **Linguagem tecnica na interface** — "Agent-SectorTier", "AUC", "WR". Em cada iteracao eu forcei: "traduz isso para linguagem de vendedor".

5. **Banner generico** — A IA fez "13 para resgatar. 27 contas conhecidas." Eu pedi: "o vendedor precisa saber O QUE FAZER, nao ver metricas". Resultado: plano numerado com nome do deal e valor.

6. **Design "cara de IA"** — Border-radius 16px em tudo, sombras dramaticas, bold excessivo, backdrop blur. Rodada especifica para limpar.

### O que eu adicionei que a IA sozinha nao faria

1. **Identificar o problema dos 68%** — A IA nao questionou que a maioria dos deals nao tem conta. Eu vi nos dados e redirecionei todo o motor.

2. **Exigir direcionamento real** — A IA da resumos. Eu exigi acoes: "Ligue para X. Comece por Y. Vale Z." Vendedor nao quer dashboard, quer saber o que fazer.

3. **Fix de dupla-suavizacao** — A queda de v3 para v4 era contraintuitiva (menos sinais = pior). Eu investiguei a causa e encontrei o bug conceitual.

4. **Honestidade** — A v3 mostrou 70.3%. Provavelmente overfitting com 11 sinais. Nao aceitei. Simplifiquei e aceitei 63.6% como mais realista.

5. **UX de vendedor** — Login por nome, kanban com drag & drop, "ID Oportunidade" para deals sem conta, cores que mudam ao arrastar, modal de resumo. Cada decisao veio de pensar no uso, nao na tecnologia.

6. **Controle de qualidade visual** — Cada bug veio da minha inspecao no preview. A IA nao ve que cores estao inconsistentes ou que um texto parece generico.

---

## Evidencias

- [x] Git history mostrando evolucao do codigo
- [x] Codigo fonte completo (scoring_engine.py + index.html)
- [x] Dados de validacao: backtest com decis monotonicas embutido no motor
- [x] Motor consome dados via API Kaggle (kagglehub) com fallback local
- [x] Dashboard funcional: login, kanban, drag & drop, modal, persistencia local

### Estrutura de arquivos

```
submissions/pedro-lima/
├── README.md                          <- Este arquivo
├── process-log/
│   └── workflow-narrative.md          <- Narrativa detalhada do processo
├── docs/
│   ├── scoring-engine.md             <- Doc tecnica do motor (sinais, cascata, backtest)
│   ├── dashboard.md                  <- Doc do dashboard (fluxo, componentes, JS)
│   └── dados.md                      <- Doc dos dados (tabelas, campos, observacoes)
└── solution/
    ├── scoring_engine.py              <- Motor v5 (Python)
    ├── index.html                     <- Dashboard principal (login, kanban, modal)
    ├── assets/
    │   └── logo-g4.svg               <- Logo oficial G4
    └── data/
        ├── scored_deals.json          <- 2.089 deals scorados
        ├── sales_pipeline.csv         <- 8.800 deals
        ├── accounts.csv               <- ~85 contas
        ├── products.csv               <- 7 produtos
        └── sales_teams.csv            <- 35 vendedores
```

---

_Submissao enviada em: 2026-04-13_
