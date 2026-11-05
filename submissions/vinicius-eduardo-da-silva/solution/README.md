# Foco da Semana: documentação técnica

## Setup

**Para usar:** abra `app/index.html` no navegador, com dois cliques. Não há instalação, servidor nem login.

**Para recalcular os dados, a partir desta pasta (`solution/`):**

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r scoring/requirements.txt   # Linux/Mac: .venv/bin/python
cd scoring
../.venv/Scripts/python -m pytest -q             # testes
../.venv/Scripts/python backtest.py              # gera backtest_results.json e ../app/replay.js
../.venv/Scripts/python pilot_plan.py            # gera pilot_plan.json
../.venv/Scripts/python build_app_data.py        # gera ../app/data.js
```

Testado com Python 3.12 no Windows e com o navegador Edge.

## Organização

| Caminho | O que é |
|---|---|
| `app/` | Interface em HTML, CSS e JS puros. `data.js` e `replay.js` são gerados, não edite à mão |
| `scoring/lead_scorer.py` | Limpeza, aprendizado das taxas e score |
| `scoring/backtest.py` | Replay de 22 segundas-feiras passadas e dados da Máquina do tempo |
| `scoring/pilot_plan.py` | Menor ganho que um teste com grupo de controle conseguiria detectar |
| `scoring/build_app_data.py` | Gera os dados da interface |
| `scoring/test_lead_scorer.py` | Testes, incluindo um contra vazamento de dados futuros |
| `data/` | CSVs originais do Kaggle (licença CC0) |

## Lógica do score

```
chance  = taxa histórica de vitória em 30 dias | faixa de idade (15 dias), semana do trimestre
receita esperada = chance × preço de tabela
score   = receita esperada em escala logarítmica, de 0 a 100
        = pontos de Valor + pontos de Momento
```

As duas partes usam os mesmos pontos por unidade logarítmica. Por isso, somá-las ordena os deals pela receita esperada, com a chance limitada à faixa de 1% a 45% para que diferenças mínimas na cauda não dominem. Essa divisão é o que permite ao vendedor ver o motivo do score.

**As filas:**

| Fila | Critério | Tratamento |
|---|---|---|
| Foco | Engaging com até 138 dias | Recebe score |
| Decidir | Engaging com mais de 138 dias, a maior duração entre deals encerrados | Sem score; o vendedor decide |
| Prospecção | Prospecting, sem data | Sem score; ordem por valor de tabela |

**Critérios e evidências:**

| Critério | Decisão | Evidência |
|---|---|---|
| Idade do deal | Entra | Maior ganho no replay; a chance tem picos, não uma linha reta |
| Semana do trimestre | Entra, como hipótese | Ganho no replay; repete-se nos trimestres observados |
| Preço de tabela | Entra | Preço fechado com mediana de 99,8% da tabela |
| Win rate do vendedor | Fora | Não melhorou o replay (diferença de −US$ 880, melhor em 11 de 22 segundas) |
| Win rate do produto | Fora | Não melhorou o replay (diferença de −US$ 1.390, melhor em 8 de 22 segundas) |
| Setor, porte, histórico da conta | Fora do ranking | AUC de cerca de 0,55 no conjunto; além disso, a conta falta em 68% dos deals abertos. O histórico aparece só como contexto |

**Como o futuro fica de fora:** cada taxa só usa segundas-feiras cuja janela de 30 dias terminou até a data analisada. Um teste reescreve tudo o que ocorreu depois de uma data e confirma que as taxas não mudam. Datas anteriores a 01/03/2017 não ensinam nada: nenhum deal fecha antes disso, então o resultado rápido daquele período está ausente dos dados.

**Empates no replay:** vários deals têm o mesmo preço, e o arquivo está ordenado por data, então a ordem dele poderia favorecer uma estratégia. O desempate é por ID, sem relação com o resultado, e o resultado com empates sorteados fica em `backtest_results.json`.

**Máquina do tempo:** a conta só aparece depois de revelar. Todo deal encerrado tem conta, então "Conta em branco" entregaria que o deal nunca fechou.

**Calculadora de tempo:** os minutos por deal são premissas, não dados do CRM, e aparecem assim na tela.

## Limpeza dos dados

- `GTXPro` no pipeline corrigido para `GTX Pro`, como no catálogo
- Setor `technolgy` corrigido para `technology`; `Philipines` corrigido para `Philippines`
- A data de análise é 01/01/2018, a primeira segunda após o fim dos dados, e não a data de hoje
- 5 vendedores sem nenhum deal continuam no filtro, com uma mensagem própria

## Limitações

- **Não prova aumento de vendas.** O replay mede se a lista aponta os deals que iam fechar, não se a atenção do vendedor muda o resultado. Isso exige um teste com grupo de controle.
- **O modelo superestima as chances altas** (previu cerca de 37%, ocorreu cerca de 29%). A ordem se mantém, e os cartões mostram a taxa observada no replay.
- **O efeito de trimestre tem pouca base:** no máximo três trimestres, e pode ser efeito do dataset. RevOps precisa confirmar.
- **Sem dados de atividade.** O CRM não registra e-mails, reuniões ou último contato, que seriam os melhores sinais de um deal esfriando.
- **Dados estáticos.** O score vem de um arquivo gerado, e as decisões da fila Decidir ficam no navegador até a exportação do CSV.

## O que seria preciso para escalar

1. Integração diária com o CRM, em vez de CSV
2. Registro das decisões direto no CRM, com login por vendedor
3. Dados de atividade e histórico de mudança de estágio
4. Teste com grupo de controle por um trimestre, conforme [`docs/plano-piloto.md`](../docs/plano-piloto.md)
5. Recalibração automática e acompanhamento da precisão ao longo do tempo
