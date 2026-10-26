# Model card — Lead Scorer

Data de referência ("hoje"): 31/12/2017. As tabelas entre marcadores `AUTO` são geradas por `python -m scorer.docs` a partir de `solution/data/processed/backtest_metrics.json`; os números da prosa são conferidos contra os mesmos arquivos por `tests/test_docs_numbers.py`. Detalhes e provas: [SCORING.md](SCORING.md), [DATA_QUALITY.md](DATA_QUALITY.md) e [SCOPE.md](SCOPE.md).

## 1. Propósito e uso pretendido

Ajudar o vendedor, na segunda de manhã, a decidir onde pôr a próxima hora: quais deals abertos **focar**, quais **reativar** e quais **limpar** do CRM (mais a lista Qualifique, para o Prospecting, que não tem score). O manager usa a mesma tela, filtrada, no 1:1 semanal. Quem responde pelo uso é a Head de RevOps.

O score é uma ordenação de prioridade. Ele não prevê "este deal vai fechar": ele diz que, entre deals abertos, os do topo concentram mais da receita que costuma ser ganha em seguida.

**Correção após revisão do Rafael.** A primeira versão do modelo (v1) dava a mesma chance de 0 a 95 dias, o que o Rafael viu na página como vendedor e contradizia o briefing. A versão atual (v2) tem uma chance que cai com a idade desde o primeiro dia e é treinada só com as fotos do mesmo ponto do trimestre. É uma mudança feita depois do backtest, a pedido dele; o histórico está no [SCORING](SCORING.md), seções 0 e 9.

## 2. Uso NÃO pretendido

- **Avaliar ou ranquear vendedores.** O vendedor está fora do score de propósito, e a diferença de win rate entre vendedores é compatível com ruído (p=0,26). A "Carteira do time" mostra só contagens.
- **Forecast financeiro.** O valor esperado serve para ordenar, não para somar. O valor do deal é o preço de tabela, e a chance é a taxa de fotos passadas do mesmo ponto do trimestre, não uma calibração por deal.
- **Encerrar deals automaticamente.** Limpe quer dizer confirmar com o cliente e encerrar ou atualizar. O deal parado pode ser CRM desatualizado, e uma ferramenta que fecha sozinha transforma o erro do score em perda real.

## 3. Dados e período

- **Origem:** dataset público "CRM Sales Predictive Analytics" (Kaggle, CC0), **sintético**: 8.800 deals, 85 contas, 7 produtos e 35 vendedores no cadastro, dos quais só 30 têm deals.
- **Período:** engajamentos de out/2016 a dez/2017; fechamentos de mar/2017 a dez/2017 (o primeiro é de 01/03/2017; a investigação 2a mostra que o início é um recorte da amostra, não o começo do negócio).
- **Fotos de treino:** o modelo aprende com fotos mensais do pipeline, de 31/03/2017 em diante, **só as do mesmo mês do trimestre que a data do modelo** (hoje, que é um último mês de trimestre: as fotos de 31/03, 30/06 e 30/09, com 5.425 linhas). Cada linha é um deal aberto naquele dia, com o desfecho nos 90 dias seguintes. O modelo de cada corte do backtest só vê o que o CRM sabia naquele dia (teste de mutação do futuro, SCORING seção 4).
- **O que entra no score:** a idade do deal (dias desde o engajamento) e o preço de tabela do produto. Mais nada. Produto, região, setor e porte foram testados (sobre a curva v1) e não entraram (SCORING seção 8).
- **Limiares das listas:** o Foque vai até a idade em que a chance cai à metade da de um deal novo; o Limpe começa quando a chance fica abaixo de 2% ou o deal passa do maior ciclo já ganho; o Reative é o que fica no meio.

## 4. Desempenho

Receita capturada pelos 20% de deals no topo da ordenação, como fração da receita realmente ganha depois do corte (métrica primária, fixada antes do backtest), para a curva v2 e, ao lado, para a v1:

<!-- AUTO:mc-desempenho -->
|  | Receita no top 20%: score v2 | score v1 | valor | recência | aleatório | AUC do score v2 | AUC da recência |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Média dos 4 cortes | 62,5% | 61,1% | 48,1% | 29,7% | 20,0% | 0,66 | 0,70 |
| Pior corte (31/07/2017) | 57,4% | 57,9% | 48,7% | 12,8% | 20,1% | 0,63 | 0,58 |

Pior corte = o de menor margem do score v2 sobre o melhor baseline. Critério pré-registrado: **PASSOU** para a v2 e **PASSOU** para a v1. A v2 é uma mudança pós-backtest, pedida pelo Rafael depois de revisar a ferramenta.
<!-- /AUTO:mc-desempenho -->

Leitura honesta:

- O score v2 vence valor, recência e sorteio nos quatro cortes, como a v1. A v2 só se distancia da v1 no corte de fim de trimestre (30/09); nos outros três empata ou fica menos de um ponto percentual abaixo. O resultado depende do preço: a chance sozinha, sem o preço, captura bem menos receita.
- **O PASSOU da v2 não é um teste às cegas:** a curva foi trocada depois de ver o backtest da v1 e a pedido do Rafael (SCORING, seção 9).
- **Em AUC a recência ganha** em três dos quatro cortes, com 0,83 contra 0,65 do score em 30/09. Se a pergunta for só "quem vai ganhar", e não "onde está o dinheiro", ordenar pelos mais novos acerta mais, exceto em 31/07, onde a recência cai abaixo do sorteio.
- **Entre os deals já resolvidos (ganhos ou perdidos) o score empata com o valor.** A vantagem vem de tirar do topo os zumbis, não de escolher o melhor entre os vivos.
- **Ordem dentro do Foque** (deals de até 90 dias, mesma população para todos os métodos), média dos quatro cortes:

<!-- AUTO:mc-ordem-foque -->
| Método (deals de até 90 dias, média dos cortes) | AUC | Receita no top 20% |
| :--- | ---: | ---: |
| Score v2 (curva por faixas) | 0,52 | 52,5% |
| Score v1 (platô) | 0,51 | 49,7% |
| Ordenar por valor | 0,50 | 49,1% |
| Mais recentes primeiro | 0,56 | 23,5% |
| Aleatório (referência) | 0,50 | 20,1% |
<!-- /AUTO:mc-ordem-foque -->

  O score v2 só ordena melhor que o preço no corte de fim de trimestre; a AUC fica perto de um sorteio.
- A tabela completa, o bootstrap e a calibração estão no SCORING.

## 5. Limitações

- **Dataset sintético.** Em CRM real o decaimento seria mais suave. O que o gerador impõe e o score herda: a regra de fechar no trimestre do engajamento (Q) ou no seguinte (Q+1), o teto de 138 dias (nenhum deal foi ganho depois disso) e fechamentos rápidos no primeiro mês do trimestre. Estão documentados e não são explorados, mas o Limpe herda o teto de 138 dias.
- **Censura.** Deals ainda abertos em 31/12/2017 contam como "não ganho" no backtest. Em agosto e setembro uma parte deles ainda pode fechar, o que subestima o ganho desses cortes.
- **Contas faltantes.** 1.425 deals não têm conta, todos abertos. Por isso `has_account` é proibido como variável: sozinho ele tem AUC maior que a do score, e só porque identifica quem nunca fecha no dataset.
- **Prospecting sem score.** Os 500 deals em Prospecting não têm data de engajamento, então não há idade, chance, score nem backtest. Qualifique é uma lista sem prova.
- **Poucas fotos por fase.** Treinar só com a fase do corte deixa três dos quatro cortes com uma foto de treino (1.330 linhas no de 30/06). A forma da curva muda de um corte para outro em parte por isso, e a v2 ainda é otimista nos deals de 61 a 90 dias do corte de 30/09 (SCORING, seção 6). Hoje o modelo tem três fotos, todas de fim de trimestre.
- **A v2 foi desenhada depois do backtest.** Largura da faixa (15 dias), fase do trimestre e os limiares de 50% e 2% foram escolhidos sabendo do que o backtest da v1 mostrou. Só a pseudo-contagem teve sensibilidade medida.
- **Ordem fraca dentro do Foque.** A AUC média entre os deals de até 90 dias é perto de um sorteio; o ganho do v2 sobre o v1 está concentrado em um corte.
- **Atributos não retestados na v2.** Produto, região, setor e porte foram testados sobre a curva v1.
- **Regra de 31/03 escolhida depois de ver o protótipo.** A justificativa é a priori (DATA_QUALITY, seção 2), mas a escolha foi feita depois de o planejador ver o efeito em 28/02. Por isso 28/02 é reportado como sensibilidade.
- **Reative fraco em fim de trimestre.** A lista teve 4% (30/06) e 5% (30/09) de ganhos nos cortes de fim de trimestre.
- **Horizonte (90 dias) e largura da faixa** foram escolhidos sabendo do dataset e não tiveram sensibilidade medida.
- **Limitação de acesso.** A ferramenta separa a visão do vendedor da do manager só na tela (separação de experiência, não de segurança): o `data.js` publicado contém os deals de todos os vendedores, e quem baixa o arquivo vê tudo. Com dados sintéticos e públicos isso é aceitável; com dados reais de clientes, não. O controle de acesso por papel (vendedor, manager e RevOps) está desenhado em `ARQUITETURA_PRODUCAO.md`, com o SQL ainda não executado, e é pré-requisito para qualquer uso fora do desafio.

## 6. Riscos e mitigação

| Risco | Como aparece | Mitigação |
|---|---|---|
| **Profecia autorrealizável** | Deal em Limpe deixa de ser trabalhado e, por isso, nunca ganha, o que "confirma" o score | Limpe significa **confirmar com o cliente** e então encerrar ou atualizar, nunca descartar. O texto do card e o brief dizem isso. A recalibração (seção 7) usa os desfechos novos, inclusive dos deals que foram reativados |
| **Viés contra vendedores** | Um vendedor com muitos deals velhos parece "pior" e é cobrado por isso | O vendedor não entra no score. Há teste de permutação: trocar os vendedores de lugar não muda nenhum score (`test_permuting_sales_agent_changes_no_score`). Nenhuma tela mostra taxa de vitória por vendedor |
| **Valor estático** | O valor esperado usa o preço de tabela, não o valor negociado | Nos 4.238 ganhos, a razão `close_value` / preço de tabela tem média 0,996, e a média por produto fica entre 0,985 e 1,004 (DATA_QUALITY, seção 4). Em CRM real, rever com o valor da proposta |
| **Confiar numa ordem que errou na história** | O Foque de hoje parece mais seguro do que é | A interface mostra o modo teste, com o que o score teria dito em datas passadas e o que aconteceu (os resumos seguem os filtros); a ordem dentro do Foque é fraca e isso está nas Limitações |
| **Dado de outro time exposto** | Qualquer pessoa que abre o arquivo `data.js` lê a carteira de todos os vendedores | Em produção, o dado fora do escopo do usuário nunca chega ao navegador: login com SSO e acesso por linha no banco, descritos em `ARQUITETURA_PRODUCAO.md`. Nesta versão, o aviso está na tela de entrada, no "Como funciona" e no README |
| **Contagem por vendedor lida como desempenho** | O mapa do time mostra vivos, esfriando e zumbis por vendedor, e alguém usa isso para ranquear pessoas | O mapa é rotulado "higiene de carteira, não desempenho", não traz taxa de vitória nem ranking, e a ordem padrão é alfabética |
| **Corrigir o modelo olhando o teste** | A curva v2 foi desenhada depois de ver o backtest, e passar no critério não prova que generalize | O critério foi mantido e reportado para as duas curvas, a mudança está declarada como pós-backtest, e o próximo teste honesto é com cortes novos (seção 7) |

## 7. Quando recalibrar

Recalibrar (rodar `python -m scorer.validate` e `python -m scorer.build` com a base nova) em qualquer um destes casos:

1. **A cada trimestre**, porque o modelo aprende com fotos mensais e o padrão do trimestre pesa: a cada fim de trimestre entra uma foto nova da fase de fim de trimestre (SCORING, seção 0).
2. **Quando a taxa de ganho em 90 dias de alguma faixa de idade se mover mais que X pp** em relação à que o modelo usa. X é um parâmetro documentado:

<!-- AUTO:mc-recalibracao -->
X = 10 pp (`config.RECALIBRATION_SHIFT_PP`). Teste de bom senso no backtest: entre as 24 faixas de idade com pelo menos 100 deals (corte x faixa), 8 teriam acendido o alerta, isto é, a chance do modelo ficou a mais de 10 pp da taxa de ganho em 90 dias observada.
<!-- /AUTO:mc-recalibracao -->

3. **Ao migrar para um CRM real com histórico de estágios.** O modelo atual só vê a data de engajamento e o desfecho; com o histórico de estágios dá para medir tempo parado por etapa, que é uma idade melhor do que "dias desde o engajamento". O teto de 138 dias e a regra Q/Q+1 devem desaparecer ou mudar, e o critério pré-registrado precisa ser rodado de novo, com cortes novos.

## 8. Governança do desenvolvimento

O modelo foi construído com agentes de IA, sob controles definidos antes da execução:
- **Separação de funções:** um agente planeja, outros executam, e um revisor de contexto limpo avalia sem ter visto o processo.
- **Critério de sucesso pré-registrado:** um único ajuste permitido.
- **Proteção contra vazamento:** teste de mutação do futuro.
- **Justiça:** teste de permutação dos vendedores.
- **Números conferidos por teste:** todo número publicado é checado contra os arquivos gerados.
- **Trilha de decisões:** [DECISIONS.md](DECISIONS.md).
- **Publicação reservada ao responsável humano.**

Mudanças no modelo seguem a mesma regra: novo backtest com critério fixado antes, nunca ajuste depois de ver o resultado. **A troca para a curva v2 não seguiu a regra:** foi feita depois do backtest, a pedido do Rafael, depois de ele usar a ferramenta como vendedor; está declarada como mudança pós-backtest.

## 9. Dono e revisão

- **Dono:** RevOps (a Head de RevOps, como patrocinadora, designa a pessoa responsável pelo modelo).
- **Revisão:** trimestral, junto com a recalibração: conferir o critério pré-registrado nos cortes mais recentes, a lista de atributos testados e se os alertas da seção 7 dispararam.
- **O que o dono deve olhar primeiro:** se a receita capturada pelo score no top 20% continua acima da de ordenar só pelo valor, e se os deals do Limpe que foram confirmados e reabertos mudam o desfecho (um Limpe que ganha é evidência contra o teto de 138 dias).
