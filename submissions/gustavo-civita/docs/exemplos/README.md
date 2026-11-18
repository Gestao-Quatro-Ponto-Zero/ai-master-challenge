# Exemplos de saída

Gerados por `gerar.py` a partir dos CSVs originais e do código em `solution/`, com a data do CRM em
31/12/2017. Servem para conferir se a lógica se comporta como descrito, sem precisar abrir a tela.

## Como as 2.089 negociações abertas foram classificadas

| Lista | Negociações | O que o vendedor faz |
|---|---|---|
| Ligar | 128 | Liga. na ordem de preço × chance |
| Primeiro contato | 500 | Primeiro contato. na ordem do preço (chance desconhecida) |
| Reativar por mensagem | 474 | Uma mensagem com condição especial |
| Encerrar | 987 | Encerra no CRM |

A lista completa, uma linha por negociação, está em `todas-as-negociacoes-abertas.csv`.

## A fila de três vendedores em situações diferentes

O que cada um vê em "Hoje", que tem duas partes: em cima a meta do dia (negociações com chance, na ordem
preço × chance) e, embaixo, "se sobrar tempo" (primeiro contato e reativação, com as que têm empresa
cadastrada primeiro). As quatro primeiras linhas de cada parte.

### Kary Hendrixson (West)

Carteira aberta: 103 negociações (13 ligar, 0 primeiro contato, 17 reativar por mensagem, 73 encerrar).

**Meta do dia: 13 prioridades.** As 4 primeiras:

| # | Empresa | Produto | Valor | Idade | O que fazer | Chance | Score |
|---|---|---|---|---|---|---|---|
| 1 | Conecom | GTX Pro | $4.821 | 14 dias | Ligar | Alta | 98 |
| 2 | Newex | GTX Pro | $4.821 | 37 dias | Ligar | Alta | 96 |
| 3 | Zencorporation | GTX Pro | $4.821 | 57 dias | Ligar | Média | 89 |
| 4 | Rangreen | GTX Plus Pro | $5.482 | 69 dias | Ligar | Baixa | 82 |

**Se sobrar tempo: 17 negociações.** As 4 primeiras:

| # | Empresa | Produto | Valor | Idade | O que fazer | Chance | Score |
|---|---|---|---|---|---|---|---|
| 14 | Kan-code | GTX Plus Pro | $5.482 | 140 dias | Reativar por mensagem | Nenhuma | – |
| 15 | Betasoloin | GTX Plus Pro | $5.482 | 148 dias | Reativar por mensagem | Nenhuma | – |
| 16 | Conecom | GTX Plus Pro | $5.482 | 177 dias | Reativar por mensagem | Nenhuma | – |
| 17 | Dalttechnology | GTX Plus Pro | $5.482 | 179 dias | Reativar por mensagem | Nenhuma | – |

### Cassey Cress (East)

Carteira aberta: 85 negociações (8 ligar, 0 primeiro contato, 26 reativar por mensagem, 51 encerrar).

**Meta do dia: 8 prioridades.** As 4 primeiras:

| # | Empresa | Produto | Valor | Idade | O que fazer | Chance | Score |
|---|---|---|---|---|---|---|---|
| 1 | Não informada | GTX Plus Pro | $5.482 | 10 dias | Ligar | Alta | 98 |
| 2 | Inity | GTX Pro | $4.821 | 57 dias | Ligar | Média | 89 |
| 3 | Toughzap | GTX Pro | $4.821 | 77 dias | Ligar | Baixa | 77 |
| 4 | Xx-holding | GTX Plus Basic | $1.096 | 18 dias | Ligar | Alta | 75 |

**Se sobrar tempo: 26 negociações.** As 4 primeiras:

| # | Empresa | Produto | Valor | Idade | O que fazer | Chance | Score |
|---|---|---|---|---|---|---|---|
| 9 | Scottech | GTX Plus Pro | $5.482 | 180 dias | Reativar por mensagem | Nenhuma | – |
| 10 | Zotware | GTX Pro | $4.821 | 121 dias | Reativar por mensagem | Nenhuma | – |
| 11 | Ontomedia | GTX Plus Basic | $1.096 | 116 dias | Reativar por mensagem | Nenhuma | – |
| 12 | Rantouch | GTX Plus Basic | $1.096 | 124 dias | Reativar por mensagem | Nenhuma | – |

### Darcel Schlecht (Central)

Carteira aberta: 194 negociações (0 ligar, 111 primeiro contato, 58 reativar por mensagem, 25 encerrar).

**Nenhuma prioridade hoje:** nenhuma negociação com chance de fechar.

**Para abrir conversa: 169 negociações.** As 4 primeiras:

| # | Empresa | Produto | Valor | Idade | O que fazer | Chance | Score |
|---|---|---|---|---|---|---|---|
| 1 | Hatfan | GTX Plus Pro | $5.482 | não iniciada | Primeiro contato | Desconhecida | – |
| 2 | Green-Plus | GTX Plus Pro | $5.482 | não iniciada | Primeiro contato | Desconhecida | – |
| 3 | Zathunicon | GTX Plus Pro | $5.482 | não iniciada | Primeiro contato | Desconhecida | – |
| 4 | Finjob | GTX Plus Pro | $5.482 | não iniciada | Primeiro contato | Desconhecida | – |

Darcel é do escritório Central, que não tem nenhuma negociação com chance de fechar: a tela dele mostra
só o bloco de baixo, e a ferramenta não consegue priorizar além de pôr primeiro as que têm empresa.

## O teste histórico

24 semanas, de 2017-07-01 a 2017-12-09. Receita gerada depois pelas 10 primeiras
negociações de cada vendedor, em cada método. As regras de comparação têm muitos empates de preço e são
desempatadas por sorteio. O detalhe por semana está em `teste-historico-por-semana.csv`.

| Período | Esta ferramenta | Preço, até 90 dias | Preço, até 90 dias, a mais nova primeiro | Preço, entre as que a ferramenta mantém | Só preço | Ao acaso |
|---|---|---|---|---|---|---|
| 3º trimestre | $9.965.786 | $9.161.400 | $9.297.948 | $8.775.762 | $7.862.471 | $3.232.719 |
| 4º trimestre | $6.406.468 | $6.246.645 | $6.589.073 | $5.336.580 | $3.993.120 | $1.759.021 |

Diferença da ferramenta para cada método:

| Período | Preço, até 90 dias | Semanas em que ganhou | A mais nova primeiro | Semanas | Entre as que mantém | Semanas | Sem recontagem (só os 7 dias seguintes) |
|---|---|---|---|---|---|---|---|
| 3º trimestre | +9% | 14 de 14 | +7% | 12 de 14 | +14% | 14 de 14 | +10% |
| 4º trimestre | +3% | 5 de 10 | −3% | 2 de 10 | +20% | 10 de 10 | −5% |

Trocando o corte de idade da regra simples (vantagem da ferramenta, em %):

| Corte | 3º trimestre | 4º trimestre |
|---|---|---|
| 45 dias | +27,3 | +34,8 |
| 60 dias | +18,4 | +11,1 |
| 75 dias | +11,7 | +2,7 |
| 90 dias | +9,0 | +2,8 |
| 100 dias | +9,5 | +5,5 |
| 120 dias | +12,6 | +14,3 |
| 138 dias | +16,3 | +22,2 |

Negociações tiradas da lista de ligação ao longo do teste: 801 diferentes. Ganhas depois: 0. Encerradas como perdidas: 2.

| Faixa de chance | Observações no teste (negociação × semana) | Ganhas depois |
|---|---|---|
| Alta | 29.628 | 42,5% |
| Média | 9.172 | 21,4% |
| Baixa | 2.468 | 2,4% |

"Pode fechar este mês": as marcadas foram ganhas em 30 dias em 20,3% dos casos; as não marcadas que ainda tinham chance, em 4,2%,

Para reproduzir: `python backtest.py` dentro de `solution/`.
