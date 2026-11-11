# Experimento

## Por que não um piloto por região

Um piloto com metade de uma região precisaria de **109 vendedores por braço** para detectar +10% de valor ganho, dado o coeficiente de variação de 0,59 entre vendedores — a empresa tem 30. Região também confunde tratamento com composição de carteira: regiões diferentes têm mix de produto e porte de conta diferentes.

## Desenho: sorteio por deal, dentro do vendedor

Cada deal aberto, dentro de cada vendedor, é sorteado para receber a ordem do relógio (tratamento) ou a ordem por preço e prazo (controle) — a melhor alternativa honesta medida em `docs/logica.md`. Cada vendedor vê as duas ordens misturadas na própria carteira e é seu próprio controle, o que neutraliza a maior fonte de ruído (CV de 0,59 entre vendedores).

## Poder estatístico

- **ICC (correlação intraclasse) de 0,031** entre deals do mesmo vendedor: baixo, porque o desfecho de um deal não informa muito sobre o desfecho do deal vizinho do mesmo vendedor.
- **Métrica primária: taxa de decisão em 28 dias** dos deals priorizados (decidiu = fechou, ganho ou perdido, no horizonte). Taxa-base medida: 22,7% (acerto do relógio no backtest).
- **Tamanho:** 1.100 deals por braço detectam +5 pontos percentuais sobre a base de 22%, com o ICC acima. Dado o pipeline do time (2.089 deals abertos na referência, Tarefa 6), isso corresponde a cerca de três semanas de pipeline do time inteiro.

## Métrica secundária

**Valor ganho** entra como secundária, nunca como critério de aceite: para detectar +10% nele seriam necessários **109 vendedores por braço**, e a empresa tem 30. A variância de valor entre vendedores (CV 0,59) é grande demais para um piloto deste tamanho medir isso com confiança. Reportamos o valor ganho do piloto, mas a decisão de continuar ou não não pode se apoiar nele.

## Regra de parada

- **Parar e expandir** se, ao fim do piloto, a taxa de decisão em 28 dias do braço tratamento for maior que a do controle com IC 95% que não cruza zero (mesmo método de bootstrap por vendedor de `docs/logica.md`).
- **Parar e não expandir** se o IC cruzar zero, ou se a taxa de "não está vivo" sem motivo registrado (P7) subir de forma que sugira que a marcação virou reação à cobrança, não decisão comercial.
- **Interromper antes do fim** se a fila de encerrar (P12) gerar reversões ou queixas documentadas acima de 1 em 5 encerramentos — o mesmo limite que `pendencias-produto.md` já usa para P3.

## O que invalida o teste

- Vendedor que descobre a ordem do colega e começa a imitar ou evitar o tratamento (contaminação dentro do time).
- Mudança de config (`config.json`) no meio do piloto: a janela aprendida muda, e os dois braços deixam de ser comparáveis entre si no tempo.
- Gestor usando a tela do time para cobrar indivíduo durante o piloto sem que isso esteja registrado (P8): se acontecer, o efeito pode vir da cobrança, não da priorização.
