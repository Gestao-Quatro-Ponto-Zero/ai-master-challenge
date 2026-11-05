# Resultados da análise

Todos os números saem de `python3 analysis/analise.py`, com semente fixa, e ficam em `resultados.json`. A data de referência é 31/12/2017, a última do dataset.

## O pipeline

| | Negócios | Preço de tabela |
|---|---:|---:|
| Ganhos | 4.238 | |
| Perdidos | 2.473 | |
| Engaging ativo, até 138 dias | 298 | $693.565 |
| Engaging parado, acima de 138 dias | 1.291 | $3.198.664 |
| Prospecting, sem data de início | 500 | $1.073.986 |

- 138 dias é o maior ciclo entre os 6.711 negócios encerrados. Só 2 chegaram a esse número.
- O limite vale até o fim: em dezembro de 2017 o maior ciclo ainda é 138.
- 68% dos negócios abertos não têm conta preenchida.
- Todos os 500 Prospecting estão na região Central, que tem só 5 dos 298 ativos. Seis vendedores da Central não têm nenhum negócio ativo. Pode ser um gargalo real ou um efeito de como os dados foram gerados.

## Nada do cadastro prevê vitória

O porteiro calcula as taxas só com o que encerrou antes de cada mês e testa no mês seguinte, de junho a dezembro de 2017. A AUC é calculada dentro de cada mês.

| Critério | AUC | Intervalo de 95% |
|---|---:|---:|
| Produto | 0,517 | 0,500 a 0,538 |
| Vendedor | 0,503 | 0,484 a 0,523 |
| Porte da conta | 0,500 | 0,483 a 0,519 |
| Setor | 0,495 | 0,475 a 0,513 |
| Conta | 0,485 | 0,466 a 0,504 |
| Manager | 0,473 | 0,452 a 0,493 |
| Região | 0,472 | 0,452 a 0,492 |

Para checar se o próprio porteiro funciona, plantei uma diferença entre vendedores em cópias dos dados:

| Diferença real entre vendedores | Vezes que o porteiro abriu |
|---:|---:|
| 0 ponto | 0 de 30 |
| 3 pontos | 0 de 30 |
| 7 pontos | 0 de 30 |
| 13 pontos | 30 de 30 |
| 21 pontos | 30 de 30 |

Ele não abre à toa e abre com efeito grande, mas não enxerga efeitos pequenos. O limiar de 0,53 foi definido antes dessa rodada e depois de uma primeira versão de 0,55 sobre um cálculo errado (ver o process log). Com sete critérios testados, ainda pode haver falso positivo em uso repetido.

## O padrão de calendário

| Mês dentro do trimestre | Negócios | Vitória | Ciclo mediano | Ciclo máximo |
|---|---:|---:|---:|---:|
| 1º | 1.779 | 49% | 7 dias | 13 dias |
| 2º | 2.358 | 55% | 68 dias | 125 dias |
| 3º | 2.574 | 81% | 75 dias | 138 dias |

Dentro do mesmo mês, a idade do negócio quase não muda a vitória: no 3º mês vai de 80% a 83% em todas as faixas. A ideia de que deals antigos ganham mais parece ser efeito desse calendário. A data de fechamento só existe depois do resultado, então isso não entra na nota. A regularidade também sugere dados gerados, embora eu não tenha confirmação da origem.

## A regra da lista

Reconstruí a fila aberta em 1º de junho, julho, agosto, setembro e outubro de 2017 e peguei os 5 primeiros de cada vendedor. A coluna mostra o valor ganho por eles nos 60 dias seguintes.

| Regra | Valor ganho | Negócios ganhos |
|---|---:|---:|
| Preço sem parados | $1.315.321 | 205 |
| Preço sem parados, mais antigo no empate (a escolhida) | $1.301.539 | 205 |
| Preço | $1.235.783 | 193 |
| Preço x janela restante | $1.106.046 | 177 |
| Sorteio | $443.121 | |

A diferença entre as duas primeiras vem só de como o empate é resolvido. Esse replay mostra o que cada lista teria incluído. Ele não mede o efeito de um vendedor agir diferente, porque esses negócios podiam fechar de qualquer jeito. Por isso o sorteio existe na ferramenta.

## A checagem dos parados

São 100 negócios sorteados, em proporção ao valor de cada produto: GTX Pro 29, GTX Plus Pro 24, MG Advanced 22, GTK 500 11, GTX Plus Basic 7, GTX Basic 5, MG Special 2. Testei a margem com 4.000 simulações por cenário, sempre com a verdade conhecida.

| Parcela realmente viva | Margem média | Vezes em que a margem acertou |
|---:|---:|---:|
| 5% | ±4,5 pontos | 98,3% |
| 10% | ±5,6 pontos | 95,7% |
| 20% | ±6,8 pontos | 93,8% |
| 50% | ±8,1 pontos | 92,4% |

A margem fica um pouco abaixo dos 95% nominais quando muitos negócios estão vivos. A estimativa supõe que os vendedores respondem com honestidade e que o CRM reflete a situação real.

## O tamanho do experimento

A métrica principal é o ganho em até 90 dias entre todos os sorteados. A base histórica é de 38,6% (coorte de 6.020 negócios), e entram cerca de 192 negócios por semana.

| Efeito | Negócios no teste | Semanas de entrada | Semanas até a resposta |
|---|---:|---:|---:|
| +10 pontos | 766 | 4 | 17 |
| +5 pontos | 3.034 | 16 | 29 |
| +3 pontos | 8.374 | 44 | 56 |

## A receita total

O sorteio dentro de cada vendedor pode só mudar a atenção de um negócio para outro. Para ver a receita total subir, seria preciso comparar vendedores. Simulei metade do time com a ferramenta, com a receita real de cada um:

| Ganho real de receita | 13 semanas | 20 semanas |
|---:|---:|---:|
| +10% | 10% | 13% |
| +20% | 27% | 35% |
| +30% | 46% | 59% |
| +50% | 87% | 95% |

A tabela mostra a chance de detectar o ganho. Com 30 vendedores, só um ganho muito grande apareceria em meio ano. Essa é uma limitação real, e nenhuma ferramenta a resolve.

## A sugestão por LLM

Rode com `OPENROUTER_API_KEY=sua-chave python3 analysis/avalia_sugestao.py modelo1 modelo2`. Os resultados ficam em `resultados_sugestao.json`.

São 60 frases, 15 para cada resposta, incluindo 2 com a instrução "ignore as regras". Frases e rótulos foram congelados em um commit antes de qualquer chamada a um modelo e não mudaram depois. Elas foram escritas pela IA, e a regra de palavras foi escrita junto, o que a favorece.

| Opção | 1ª rodada | 2ª rodada | Tempo mediano | Custo por nota |
|---|---:|---:|---:|---:|
| Claude Haiku 5.5 (o padrão) | 59 | 59 | 1,4 s | $0,00007 |
| DeepSeek V4.1 Flash 1017 | 58 | 60 | 0,7 s | $0,00004 |
| DeepSeek V4 Flash | 58 | 56 | 1,1 s | $0,00002 |
| GPT OSS 20B (4 respostas fora do formato) | 56 | | 2,1 s | $0,00003 |
| Mistral Nemo | 54 | | 3,3 s | $0,00001 |
| Llama 3.1 8B | 50 | | 0,5 s | $0,00005 |
| Regra de palavras | 48 | | imediato | grátis |

Na média, Haiku e DeepSeek V4.1 Flash empatam em 59. Escolhemos o Haiku pela estabilidade: as respostas foram as mesmas nas duas rodadas.

Os critérios foram definidos antes de ver os resultados:

| Critério | Meta | Haiku |
|---|---|---|
| Acertos | Mais de 48 | 59 |
| Negócio em andamento marcado como encerrado | Menos que a regra | Empate em 0, então o critério não foi cumprido |
| Tempo mediano | Até 3 s | 1,4 s |
| Frases com "ignore as regras" | As 2 pelo fato real | 2 |

O segundo critério estava mal definido, porque a regra teve zero e nenhum modelo podia ficar abaixo. O outro lado do erro pesou na decisão: a regra marcou 10 negócios encerrados como ainda abertos, e o Haiku, nenhum. O único erro do Haiku foi classificar "A empresa faliu no ano passado" como registro errado, em vez de perdido.

Antes dessa rodada, um primeiro teste falhou por configuração: o teto de 120 tokens cortava respostas e o parâmetro de temperatura bloqueava o Haiku. Corrigir isso e trocar para modelos pequenos não alterou as frases nem as instruções. O GLM 5.3 Flash saiu da lista porque não permite desligar o raciocínio.

Em chamadas reais pela tela, a sugestão levou de 1,4 a 2,4 segundos, não foi salva sozinha e só contou depois da confirmação. Sem chave, o campo some e os botões seguem funcionando.
