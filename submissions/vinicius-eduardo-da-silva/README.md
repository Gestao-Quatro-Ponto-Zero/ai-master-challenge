# Submissão — Vinicius Eduardo da Silva — Challenge 003

> Esta submissão também inclui o [Challenge 002](challenge-002/README.md), em pasta própria.

## Sobre mim

- **Nome:** Vinicius Eduardo da Silva
- **LinkedIn:** https://www.linkedin.com/in/vinicius-silva-ai/
- **Challenge escolhido:** 003 — Lead Scorer

---

## Executive Summary

Construí com o Claude Code o **Foco da Semana**, uma ferramenta que abre com dois cliques e diz a cada vendedor o que fazer na segunda de manhã e por quê. A análise mudou o problema: **82% dos deals em Engaging já passaram de 138 dias, a maior duração entre todos os deals encerrados**, e características como vendedor, produto e setor quase não preveem o fechamento. Por isso, os deals parados vão para uma triagem rápida, e os vivos recebem um score de valor e momento. Em 22 segundas-feiras passadas, a lista trouxe **42% mais receita que ordenar por valor e 21% mais que o rival mais forte**, que ordena por valor e já ignora os parados. A principal recomendação é limpar o pipeline parado, confirmar com RevOps o que aconteceu na região Central e medir o ganho real em um piloto de um trimestre.

**Para testar:** abra [`solution/app/index.html`](solution/app/index.html) no navegador, com dois cliques, e siga este roteiro:

1. Escolha **Zane Levy** no filtro Vendedor e marque um deal como Feito.
2. Abra **Decidir** e use os atalhos `V`, `E`, `P` e `U`.
3. Abra **Máquina do tempo** e clique em **Revelar o que aconteceu**.
4. No filtro **Data do pipeline**, escolha 07/08/2017 para ver a semana daquela data.

![Minha semana de um vendedor](docs/screenshots/1-minha-semana.png)

| Pasta | O que tem |
|---|---|
| [`solution/`](solution/README.md) | Ferramenta, score, replay, testes e documentação técnica |
| [`docs/plano-piloto.md`](docs/plano-piloto.md) | Plano de teste para a Head de RevOps |
| [`docs/screenshots/`](docs/screenshots/) | Telas da ferramenta |
| [`process-log/`](process-log/PROCESS_LOG.md) | Como o trabalho aconteceu, prompt consolidado e scripts de cada etapa |

---

## Solução

### Abordagem

Trabalhei com o Claude Code, que fez a análise e o código enquanto eu tomava as decisões e avaliava o resultado. Primeiro, auditamos os dados. Depois, testamos cada critério em segundas-feiras reconstruídas, usando só o que se sabia em cada data, e um critério só entrava se melhorasse a lista. No fim, tentamos derrubar o próprio resultado, e isso mudou a mensagem principal.

### Resultados / Findings

**O pipeline é bem menor do que parece:**

| Fila | Deals | Valor de tabela |
|---|---:|---:|
| Foco: Engaging com até 138 dias | 288 | US$ 665.078 |
| Decidir: Engaging acima de 138 dias | 1.301 | US$ 3.227.151 |
| Prospecção: sem data | 500 | US$ 1.073.986 |

**O score no replay** (top 10 de cada vendedor, receita ganha em 30 dias, média por segunda):

| Estratégia | Jul–set | Out–nov | Ganhos em 30 dias | Parados na lista (de ~300) |
|---|---:|---:|---:|---:|
| **Score** | **US$ 354.201** | **US$ 268.350** | **21,9%** | **0** |
| Maior valor, sem os parados | US$ 275.462 | US$ 248.386 | 16,3% | 0 |
| Maior valor | US$ 248.243 | US$ 191.465 | 13,4% | 53 |
| Mais novo primeiro | US$ 111.280 | US$ 187.248 | 19,8% | 0 |
| Aleatório | US$ 100.257 | US$ 84.045 | 13,1% | 52 |

**De onde vem o ganho:**

- **Tirar os deals parados** rende +17,5% sobre ordenar por valor. É o ganho mais sólido.
- **O momento do deal** acrescenta +21%: à frente em 19 de 22 segundas e para 26 dos 30 vendedores. Mas é desigual: +29% em jul–set e **só +8% em out–nov**.
- **Não depende de deals gigantes:** sem o produto mais caro, a vantagem fica em +23,5%.
- **A lista curta rende mais:** contra o mesmo rival, o ganho é de +32% no top 5 e +11% no top 20.

**Outros achados:**

- **Região Central:** 0 deals vivos, 408 parados e todos os 500 em Prospecting. Seus vendedores seguem fechando negócios, e há um pico de deals engajados em julho de 2017. Isso pode ser processo ou importação de dados.
- **Trimestre:** o win rate é de cerca de 80% no último mês e 50% no primeiro. Na primeira segunda do trimestre, deals com até 14 dias têm 15–19% de vitória em 30 dias, e os mais velhos, 0–2,6%.
- **Valor:** o preço fechado fica com mediana de 99,8% da tabela, então a tabela é uma boa estimativa.

### Recomendações

1. **Esta semana, RevOps:** perguntar à Central o que ocorreu em julho de 2017 e se o efeito de trimestre é processo comercial, como metas e revisão de pipeline.
2. **Nas próximas duas semanas, vendedores:** passar pela fila Decidir, começando pelos deals de maior valor. É o ganho mais sólido e o que deixa o pipeline real claro.
3. **Depois, RevOps:** tornar a conta obrigatória em Engaging, pois ela falta em 68% dos deals abertos.
4. **Antes de escalar:** rodar um teste com grupo de controle por um trimestre completo. Com 30 vendedores, um mês só detectaria ganhos acima de 42% em deals ganhos; um trimestre detecta cerca de 17%. Detalhes em [`docs/plano-piloto.md`](docs/plano-piloto.md).

### Limitações

- O replay mostra que a lista aponta os deals que iam fechar, não que a atenção muda o resultado.
- O ganho do momento é incerto e caiu para +8% em out–nov. Ele também se apoia em poucos trimestres e pode ser efeito do dataset.
- Ordenar pelo mais novo ganhou mais deals em out–nov (26% contra 19%). O score otimiza receita, não contagem de vitórias.
- O modelo superestima chances altas, por isso os cartões mostram a taxa observada.
- Passar de 138 dias não prova que o deal morreu, então a decisão fica com o vendedor.
- O CRM não registra atividade, e deals em Prospecting não têm data nem score.
- Os minutos da calculadora de tempo são premissas, não dados.
- As regras comerciais e as ações sugeridas não foram validadas com alguém da área de vendas.

---

## Process Log — Como usei IA

Registro completo em [`process-log/PROCESS_LOG.md`](process-log/PROCESS_LOG.md). O raciocínio também está resumido em [`process-log/prompt-consolidado.md`](process-log/prompt-consolidado.md) e [`process-log/sequencia-de-prompts.md`](process-log/sequencia-de-prompts.md), escritos depois do trabalho e identificados assim. A conversa original não está incluída.

### Ferramentas usadas

| Ferramenta | Para que usou |
|---|---|
| Claude Code (Claude Opus 5.5) | Leitura do desafio, análise dos dados, código, testes no navegador e primeira versão dos textos |

### Workflow

1. Leitura das regras e escolha do desafio
2. Auditoria dos dados, em busca de problemas e vieses
3. Teste de sinais com validação temporal, que derrubou o plano de score baseado em vendedor e produto
4. Replay de segundas passadas, para decidir cada critério com evidência
5. Interface, testes no navegador e correções
6. Extras e redesign, depois que usei a ferramenta e pedi algo mais fácil de entender e de usar
7. Auditoria final para tentar derrubar o resultado, que trouxe o rival mais forte para a mensagem principal
8. Documentação e submissão

### Onde a IA errou e como corrigi

Os erros estão detalhados no process log, com a forma como cada um apareceu. O próprio Claude Code os detectou nos testes e nas revisões, e o da referência fraca surgiu na auditoria que pedi. Dois exemplos:

- **Chance errada na tela:** a ferramenta mostrava cerca de 14% de chance para um deal de 67 dias em 1º de janeiro, quando o histórico indicava 0–2,6%. O ranking estava bom no replay, então os testes não acusaram; o problema apareceu na revisão da tela.
- **Referência fraca:** o "+42%" era apresentado como resultado principal. A auditoria final mostrou que, contra um rival que já ignora os deals parados, o ganho é de +21%, e de +8% em out–nov.

### O que eu adicionei que a IA sozinha não faria

Não conheço o negócio de vendas. Resolvi este problema junto com a IA, e minha contribuição foi de direção e de cobrança, não de conhecimento comercial:

- **Decidi o rumo:** escolhi o desafio, a fila separada para os deals parados, testar o efeito de trimestre antes de usá-lo, o formato sem deploy e quais extras entrariam.
- **Usei a ferramenta e disse o que estava ruim:** achei a página simples demais, e isso levou ao redesign. Notei que ela estava presa a uma data fixa, e isso levou ao filtro de data. Perguntei se dava para mostrar mais detalhes para o vendedor ver valor no deal, e isso levou aos detalhes do deal.
- **Cobrei resultado:** perguntei se estávamos atendendo ao enunciado e se dava para ir além. Depois, perguntei se tudo funcionava e se teríamos resultado. Essa última pergunta levou à auditoria que trocou o "+42%" pela comparação mais honesta, de +21%.

**Minha aposta:** se a ferramenta resolver a dor do vendedor, eles vão usar. A decisão sobre um deal parado precisa ser breve, para ele decidir e fazer acontecer. Isso é uma opinião, não um dado, e o piloto serve para testá-la.

**O que eu não fiz:** não encontrei os erros técnicos, que foram detectados pelo Claude Code, e não validei as regras comerciais com alguém da área. Também não tenho os minutos reais gastos em um deal parado, por isso a calculadora usa premissas ajustáveis.

---

## Evidências

- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow
- [ ] Chat exports
- [x] Git history
- [x] Narrativa escrita: [`process-log/PROCESS_LOG.md`](process-log/PROCESS_LOG.md)
- [x] Outro: scripts de cada etapa em `process-log/exploration/`, resultados em `solution/scoring/backtest_results.json` e telas em `docs/screenshots/`

---

_Submissão enviada em: 05/11/2026_
