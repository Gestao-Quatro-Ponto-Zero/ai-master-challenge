# O que eu acrescentei que a IA sozinha não faria

> Este é o arquivo que separa quem conduz de quem cola o brief. Não é sobre ter pedido bem:
> é sobre o que foi rejeitado, e com qual razão.

## Contexto que não está no dado

- **Os 500 deals em Prospecting valem US$ 1,07 mi de tabela, 4,5 vezes todo o pipeline vivo** (US$ 235.930). Não estava no plano como argumento central; foi a leitura de que a recomendação honesta para a primeira segunda-feira do trimestre é começá-los, não resgatar os velhos. Isso virou o argumento central do resumo executivo.
- **A carga de um vendedor sai do histórico, não de um teto arbitrário.** Escolhi a mediana de deals abertos que depois fecharam, por trimestre análogo, como carga de referência. Um teto escrito à mão (como "79 oportunidades" ou "5 por vendedor") não diria nada sobre o que o vendedor realmente carrega.
- **Vendedor sem nenhum deal no export não é vendedor com carga zero.** Na tela, a diferença aparece como "Sem histórico" e não como "0", porque 0 pareceria medição.

## O que eu rejeitei

- **Ordenar por atributos (conta, vendedor, setor, porte).** Testei cada um contra o resultado real com 1.000 repetições: nenhum ficou abaixo de 0,05. Por isso o produto não tenta prever quem ganha. A alternativa de ordenar por probabilidade de ganho foi descartada antes mesmo do backtest.
- **Sorteio do aleatório por posição na lista.** A primeira versão dava 334.520 de valor e mudava quando a ordem das linhas mudava. Troquei por sorteio por deal, em 200 rodadas, que é independente da ordem.
- **A frase "esta semana não há nada seu para fechar".** A Embaixadora da Cultura, nas personas, mostrou que ela pode ser lida como sentença de carteira ruim. O estado vazio da tela diz o que não foi visto e o que fazer, em vez de parar na frase.
- **A conta de horas como número único.** Sem o custo-hora real da operação, convertemos o ganho de US$ 1.416 por vendedor em três cenários de horas, em vez de inventar uma taxa.

## A pergunta que eu mudei

- **De "quem vai ganhar" para "quando este deal costuma decidir".** O dado não sustenta a primeira; a segunda se responde com o histórico. A ferramenta mostra uma janela, não uma chance de fechar.
- **De "o relógio é o melhor modelo" para "o relógio rende mais que a melhor alternativa honesta, e o intervalo não cruza 1".** A pergunta que importa para a operação é se a ordem muda o resultado, não se a ordem é a mais sofisticada.
- **De "a taxa de acerto mostra o efeito" para "o valor ganho, com intervalo, mostra o efeito".** A taxa de acerto muda com a taxa-base do negócio, então a razão entre taxas exagera o efeito.

## Decisões de não automatizar

- **Encerrar um negócio no CRM não é automático.** A fila de encerrar vira "confirmar ou reativar", porque o vendedor tem informação que o export não tem (Caio, na transcrição: "sem data não significa morto").
- **Marcar "não está vivo" não mexe no número do gerente sem o motivo registrado** (P7), e a visibilidade para o gestor fica como decisão de piloto, não de produto.
- **A chave da API fica fora do site publicado.** Os briefings são gerados no computador de quem roda o `run.py`, e a Vercel recebe só o resultado. Um site estático com chave no código ficaria exposto a qualquer um que abrisse o navegador. Decisão tomada pelo Diego (opção A), depois de eu explicar a alternativa de chamada a cada abertura.
- **Limite de tokens e teto de chamadas no código, não só no console.** Cada resposta tem limite de saída, cada item tem no máximo duas tentativas, e a execução para em 60 chamadas. O validador recusa o que sai do marcador, e o template cobre o restante.
- **Nenhuma troca de modelo foi automática.** O Diego trocou o modelo entre etapas, por custo e qualidade; a atribuição por tarefa está em `MODELOS.md`.
