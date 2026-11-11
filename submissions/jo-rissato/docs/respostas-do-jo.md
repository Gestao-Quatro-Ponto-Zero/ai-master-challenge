# Bloco 2: o que você precisa responder

Case 002, Redesign de Suporte. Cada pergunta traz os números do dado que se aplicam a ela, com a
base (n). Responda com as suas palavras, em áudio ou texto. A resposta vira o primeiro commit.

---

## 1. Qual é o problema real do diretor?

O que ele disse: time sobrecarregado, tempo de resolução subiu, satisfação caiu.

O que o dado mostra (n = 8.469):
- 33,3% dos tickets não têm nenhuma resposta (2.819).
- 34,0% foram respondidos e esperam o cliente (2.881).
- 32,7% foram fechados (2.769).
- Nenhuma das 8 variáveis registradas explica por que um ticket trava (menor p = 0,073).

O dado não registra: data de abertura do ticket, atendente, reabertura, esforço por ticket, custo.

**Sua resposta:**

---

## 2. Se você fosse o diretor, o que priorizaria: custo, capacidade ou satisfação? Por quê?

O que o dado permite medir:
- Custo: não existe no dado.
- Capacidade: só o status (1/3 sem resposta); sem atendente nem volume por dia.
- Satisfação: só nos 2.769 fechados; média 2,99, cada nota de 1 a 5 com cerca de 20%.

**Sua resposta:**

---

## 3. Se todo ticket fosse respondido na hora, mas o tempo de resolução continuasse igual, o problema estaria resolvido?

O que o dado mostra (n = 2.769 fechados):
- Horas até resolver não têm relação com a satisfação (rho = +0,022, p = 0,254).
- Canal, prioridade e tipo também não (p entre 0,278 e 0,699).

**Sua resposta:**

---

## 4. Com esses achados, o que você considera o ponto mais importante para a entrega?

Achados disponíveis:
- O Dataset 1 tem marcas de dado gerado: as 8.469 descrições trazem o marcador `{product_purchased}`;
  1.365 de 2.769 fechados têm resolução antes da 1ª resposta.
- O brief cita ~30.000 tickets; o arquivo tem 8.469.
- A prioridade não muda o status (p = 0,227): 692 tickets críticos sem resposta e 711 esperando o cliente.
- Nenhuma combinação de canal, prioridade e tipo é pior que o acaso (teste de permutação).
- O Dataset 2 tem 47.837 textos reais em 8 categorias, base para o classificador.

**Sua resposta:**

---

## 5. O que a IA nunca deve responder ou executar sozinha?

Volume de cada tipo de pedido (n = 8.469):

| Tipo | Tickets | % |
|---|---|---|
| Reembolso | 1.752 | 20,7% |
| Problema técnico | 1.747 | 20,6% |
| Cancelamento | 1.695 | 20,0% |
| Dúvida de produto | 1.641 | 19,4% |
| Cobrança | 1.634 | 19,3% |

Prioridade crítica: 2.129 tickets (25,1%).
O dado não registra o sistema de pagamento nem se existe API de integração.

**Sua resposta:**

---

## 6. Como você vai saber, em 30 dias, que a automação funcionou?

O que hoje dá para medir: status do ticket. O que não dá: reabertura, tempo desde a abertura,
satisfação de quem não fechou.

**Sua resposta:**

---

# Respostas do Jó às perguntas do brief

## Diagnóstico 1. Onde o fluxo trava (respondido às 19:53)

**Pergunta do brief:** Onde o fluxo trava? Gargalos por canal, prioridade, tipo de ticket. Quais combinações geram os piores tempos de resolução?

**Resposta adotada pelo Jó** (tabelas da rodada 16, coladas por ele como resposta):

1. Tempo até resolver (base: 1.404 fechados com registro coerente)

| Cruzamento | Pior combinação | Tickets | Limite do acaso (95%) | É real? |
|---|---|---|---|---|
| Canal × prioridade | Chat / Alta: 8,4 h | 101 | 8,8 h | não |
| Prioridade × tipo | Alta / Reembolso: 8,8 h | 83 | 9,2 h | não |
| Canal × tipo | Chat / Cancelamento: 7,3 h | 75 | 9,2 h | não |
| Canal × prioridade × tipo | Chat / Baixa / Problema técnico: 13,2 h | 15 | 14,3 h | não |

2. % sem resposta (base: 8.469 tickets, 100% do Dataset 1)

| Cruzamento | Pior combinação | Tickets | Limite do acaso (95%) | É real? |
|---|---|---|---|---|
| Canal × prioridade | Telefone / Baixa: 38,9% | 499 | 38,6% | passou por 0,3 ponto |
| Prioridade × tipo | Alta / Cancelamento: 37,9% | 398 | 39,8% | não |
| Canal × tipo | Redes sociais / Cancelamento: 36,3% | 413 | 39,6% | não |
| Canal × prioridade × tipo | Telefone / Alta / Cobrança: 44,7% | 103 | 48,4% | não |

**Conclusão (aprovada pelo Jó às 19:54):** Nenhuma combinação de canal, prioridade e tipo é pior que o acaso. Telefone / Baixa passou do limite simples por 0,3 ponto, mas não resiste à correção para 8 testes (limite de 40,1%). O fluxo trava igual em todos os recortes: 1/3 dos tickets fica sem resposta.

## Diagnóstico 2. O que impacta a satisfação (respondido às 23:49)

**Pergunta do brief:** O que impacta satisfação? É o tempo de resposta? O canal? O tipo de problema?

**Base:** 2.769 tickets fechados, 100% dos tickets com nota. Notas 1 a 5 com 19,6% a 20,9% cada (uniformidade p = 0,797).

| Pergunta | O dado mostra | p |
|---|---|---|
| Tempo de resposta | Tempo até a 1ª resposta não existe (sem data de abertura). Horas entre 1ª resposta e resolução (1.404 coerentes): rho +0,003; médias por quartil 2,99 / 3,01 / 3,13 / 2,97 | 0,921 e 0,426 |
| Canal | Médias de 2,95 (telefone) a 3,08 (chat) | 0,278 |
| Tipo de problema | Médias de 2,93 (reembolso) a 3,03 (cobrança e cancelamento) | 0,699 |
| Outras 12 variáveis e o texto | Nenhuma passa da correção para 15 testes; 0 de 395 células categoria × nota acima do limite | menor corrigido 0,502 |

**Resposta adotada pelo Jó:**
> Nenhum dos três. Nas 2.769 avaliações que existem, a nota é a mesma qualquer que seja o tempo até resolver, o canal ou o tipo de problema. Cada nota de 1 a 5 aparece em cerca de 20% dos casos, e testei 15 variáveis sem encontrar efeito. Há dois limites no dado. Primeiro, o tempo até a 1ª resposta não pode ser medido, porque falta a data de abertura do ticket. Segundo, 67% dos tickets (5.700) nunca foram avaliados, porque a nota só é coletada quando o ticket fecha. Hoje o dado não mostra o que causa a satisfação. Para descobrir, a operação precisa registrar a data de abertura do ticket, pedir a nota também para quem não teve o ticket fechado e coletar o motivo da nota.

Fontes: `docs/relatorio-satisfacao.md`, `docs/relatorio-categoria-vs-nota.md`, process log rodadas 17 a 21.

## Diagnóstico 3. Quanto estamos desperdiçando (respondido às 23:58)

**Pergunta do brief:** Quanto estamos desperdiçando? Quantifique em horas e, se possível, estime custo. Onde está o maior desperdício recuperável?

**Resposta adotada pelo Jó** (versão detalhada, com a sugestão de fechamento aceita):

**Horas.** Dos 8.469 tickets da base, só 1.404 (16,6%) têm tempo que dá para medir. São os tickets fechados em que a resolução vem depois da 1ª resposta. Neles:
- o total é de 10.639 horas;
- a mediana é de 6,3 h por ticket, a média de 7,6 h e o máximo de 23,5 h;
- um quarto desses tickets (os que passam de 11,4 h) fica com 51,7% das horas;
- nenhum recorte concentra essas horas. O tempo médio vai de 7,0 a 8,1 h por tipo (p = 0,160), de 7,3 a 7,9 h por canal (p = 0,791) e de 7,1 a 8,1 h por prioridade (p = 0,091), e nenhuma dessas diferenças passa do acaso.

Essas horas são tempo decorrido entre a 1ª resposta e a resolução, não tempo trabalhado pelo atendente.

**O resto da base não tem tempo medível:**
- 1.365 fechados (49,3% dos 2.769) registram a resolução antes da 1ª resposta;
- 2.819 tickets nunca receberam resposta e não têm data de abertura;
- 2.881 estão aguardando o cliente, sem data de abertura nem de fechamento.

**Custo.** Não pode ser estimado. O dado não tem custo por hora, número de atendentes nem tempo trabalhado por ticket, e qualquer valor em reais seria premissa, não dado.

**Maior desperdício recuperável.** É o terço dos tickets que nunca recebeu resposta: 2.819 (33,3% da base), dos quais 692 são de prioridade crítica. Esses tickets se espalham igualmente:
- por prioridade: de 692 a 727 cada;
- por tipo: de 532 a 602 cada;
- por canal e pelas combinações de canal, prioridade e tipo: nenhuma fica acima do que o acaso explicaria.

Não é um gargalo localizado. É a operação inteira deixando um terço da demanda sem resposta.

**Segundo desperdício: a própria medição.**
- Metade dos fechados tem registro de tempo impossível.
- Nenhum ticket tem data de abertura.
- 5.700 tickets (67,3%) nunca foram avaliados, porque a nota só é coletada no fechamento.

Sem a data de abertura e um registro de tempo confiável, a operação não consegue medir o próprio desperdício. O primeiro passo é criar essas métricas: data de abertura, tempo trabalhado por ticket e custo da hora do atendente.

Fontes: `docs/relatorio-desperdicio.md`, `docs/relatorio-combinacoes.md`, process log rodadas 23 a 25.

## Bloco 2, pergunta 1. Qual é o problema real do diretor? (respondido em 2026-11-11 às 09:42)

**Resposta adotada pelo Jó** (versão ajustada da rodada 30; a original está literal no process log):

> O diretor aponta três problemas: time sobrecarregado, tempo de resolução maior e satisfação em queda. Os dados não permitem confirmar nenhum dos três como tendência. Não há número de atendentes para medir sobrecarga, nem data de abertura ou série no tempo para dizer que o tempo subiu ou que a satisfação caiu. O que os dados mostram com clareza é falta de processo. Um terço dos tickets nunca recebeu resposta, igual em todos os canais, tipos e prioridades. A prioridade não muda nada: 692 tickets críticos estão sem resposta. Metade dos fechados registra a resolução antes da 1ª resposta. E a satisfação só é medida no fechamento, então dois terços dos clientes nunca foram ouvidos. Falta processo no atendimento e falta processo de medição. Tempo, satisfação e sobrecarga são consequências desse problema, não a causa. O problema real é a operação não ter processo nem métricas para enxergar e corrigir o próprio atendimento.

| Afirmação | Número | Base |
|---|---|---|
| Um terço sem resposta, igual em todos os recortes | 2.819 (33,3%); nenhuma combinação acima do acaso | 8.469 |
| Prioridade não muda nada | p = 0,227; 692 críticos sem resposta | 8.469 |
| Metade dos fechados com tempo impossível | 1.365 de 2.769 (49,3%) | 2.769 |
| Dois terços nunca avaliados | 5.700 (67,3%) | 8.469 |
| Sobrecarga, tendência de tempo e de satisfação não mensuráveis | lacunas 1, 2, 3 e 11 | `docs/lacunas-de-dado.md` |

## Bloco 2, pergunta 2. Custo, capacidade ou satisfação? (respondido em 2026-11-11 às 09:45)

**Resposta adotada pelo Jó** (versão ajustada da rodada 32; a original está literal no process log):

> Custo não entra como prioridade, porque não há dado de custo para medir nem para acompanhar. A expectativa é que a reestruturação e a automação reduzam custo, mas isso é hipótese a medir depois que o custo passar a ser registrado. Vou priorizar capacidade de resposta e satisfação juntas, porque os problemas estão pulverizados: os cinco tipos de ticket têm cerca de 20% cada, e nenhum canal, prioridade ou tipo concentra a falta de resposta, o tempo ou a nota baixa. Não existe um único ponto para atacar; o trabalho é no processo de atendimento como um todo. Em capacidade, o alvo é claro: 2.819 tickets (33,3%) nunca receberam resposta, 692 deles críticos. Em satisfação, o primeiro passo é medir: hoje 67,3% dos clientes nunca avaliaram o atendimento, e nada do que é registrado explica a nota de quem avaliou. Tempo, satisfação e sobrecarga melhoram como consequência de um processo que responda, priorize e meça.

| Afirmação | Número | Base |
|---|---|---|
| Sem dado de custo | lacuna 5 | `docs/lacunas-de-dado.md` |
| Tipos pulverizados | 19,3% a 20,7% por tipo | 8.469 |
| Nenhum recorte concentra falta de resposta, horas ou nota | combinações, horas por recorte e categoria × nota abaixo do acaso | 8.469 / 1.404 / 2.769 |
| Alvo de capacidade | 2.819 sem resposta (33,3%), 692 críticos | 8.469 |
| Satisfação a medir | 5.700 sem nota (67,3%); 15 variáveis sem efeito | 8.469 / 2.769 |

## Bloco 2, pergunta 3. Responder na hora resolveria? (respondido em 2026-11-11 às 09:49)

**Resposta adotada pelo Jó** (versão ajustada da rodada 34; a original está literal no process log):

> Não estaria resolvido. O problema não é a primeira resposta, é a finalização. Dos 5.650 tickets que já receberam resposta, só 2.769 (49,0%) foram fechados; os outros 2.881 seguem aguardando o cliente. Responder na hora atenderia os 2.819 tickets que nunca tiveram resposta, mas, se eles seguirem o mesmo padrão, metade continuaria sem fechamento. Responder rápido não fecha o ciclo. Isso confirma que o problema é de processo: o ticket precisa ser acompanhado da entrada até a resolução, com prioridade respeitada e medição em cada etapa. Só olhando o processo inteiro dá para tratar as três dores que o diretor trouxe: sobrecarga, tempo e satisfação.

| Afirmação | Número | Base |
|---|---|---|
| Respondidos que fecharam | 2.769 de 5.650 (49,0%) | 5.650 com 1ª resposta |
| Respondidos aguardando o cliente | 2.881 (51,0%) | 5.650 |
| Sem nenhuma resposta | 2.819 (33,3%) | 8.469 |
| "Metade continuaria sem fechamento" | projeção pelo padrão observado, não medida | 5.650 |
| Tempo até resolver não muda a nota | rho = +0,003, p = 0,921 | 1.404 |

## Bloco 2, pergunta 4. Ponto mais importante da entrega (respondido em 2026-11-11 às 10:05)

**Resposta adotada pelo Jó** (versão ajustada da rodada 36; a original está literal no process log):

> O ponto mais importante da entrega é a reestruturação do departamento de suporte como um todo, e não a otimização de um canal ou de um tipo de ticket, porque os dados mostram um problema de processo espalhado igualmente por toda a operação. Essa reestruturação cobre quatro frentes. A primeira é a entrada: uma automação que recebe o cliente e classifica o ticket por categoria, construída sobre os 47.837 tickets reais do Dataset 2 e com o acerto medido por categoria antes de entrar em uso. A segunda é o acompanhamento até a resolução de fato, porque hoje só 49% dos tickets respondidos chegam ao fechamento. A terceira é o limite da automação: definir por escrito o que a IA faz sozinha, o que ela só sugere e o que fica sempre com uma pessoa. A quarta é o time e a medição: treinar a equipe para operar nesse novo fluxo e passar a registrar o que hoje não existe (data de abertura, atendente, tempo trabalhado, custo e satisfação de todos os clientes), para que o resultado possa ser provado.

| Afirmação | Número | Base |
|---|---|---|
| Problema espalhado igualmente | nenhuma combinação acima do acaso | 8.469 |
| Base do classificador | 47.837 textos, 8 categorias (3,7% a 28,5%) | Dataset 2 |
| Acerto do classificador | ainda não medido; será medido por categoria | a construir |
| Respondidos que fecham | 2.769 de 5.650 (49,0%) | 5.650 |
| Treinamento do time | sem dado de equipe (lacunas 1 e 2); etapa do plano | `docs/lacunas-de-dado.md` |
| O que passar a registrar | lacunas 1, 3, 4, 5 e 7 | `docs/lacunas-de-dado.md` |

## Bloco 2, pergunta 5. O que a IA nunca faz sozinha (respondido em 2026-11-11 às 10:14)

**Resposta adotada pelo Jó** (versão ajustada da rodada 38; a original está literal no process log):

> Essa resposta completa depende de conhecer os sistemas que a empresa usa, se têm API e o que essas APIs permitem, e o dado não traz essa informação. Com o que já sei, a regra para o primeiro momento é separar conversar de executar. A IA pode receber, classificar, coletar informações e responder em todos os tipos de ticket. O que ela não faz sozinha é executar ações irreversíveis sobre dinheiro ou contrato: finalizar reembolso, efetivar cancelamento e alterar ou estornar cobrança. Reembolso e cancelamento somam 3.447 tickets (40,7%), 867 deles críticos e 1.146 hoje sem nenhuma resposta. Nesses casos, a IA deixa tudo pronto e uma pessoa decide. Esse critério é de julgamento, não um achado do dado, que não traz valores nem estornos. Problema técnico, dúvida de produto e dúvida de cobrança podem ser automatizados ao máximo dentro das ferramentas disponíveis. Como o dado não tem respostas corretas de referência, a qualidade da IA será medida na operação. Depois de 30 dias, com histórico e métricas, decidimos o que sai do manual.

| Afirmação | Número | Base |
|---|---|---|
| Sistemas e API desconhecidos | lacuna 10 | `docs/lacunas-de-dado.md` |
| Reembolso + cancelamento | 3.447 (40,7%); 867 críticos; 1.146 sem resposta | 8.469 |
| Critério de ação irreversível | julgamento, não achado do dado | sem valor nem estorno no dado |
| Sem resposta correta de referência | coluna `Resolution` é texto sem sentido | Dataset 1 |

## Bloco 2, pergunta 6. Como saber em 30 dias que funcionou (respondido em 2026-11-11 às 10:34)

**Resposta adotada pelo Jó** (versão ajustada da rodada 40; a original está literal no process log):

> Chamo de reestruturação, e não só de automação, porque o que muda é o processo inteiro. Para saber se funcionou, preciso de duas coisas: comparar com o que já dá para medir hoje e criar as métricas que não existem. O dado atual já dá a linha de base de cinco indicadores, e funcionou se eles se moverem na direção certa: tickets sem nenhuma resposta (hoje 33,3%), críticos sem resposta (hoje 692), respondidos que chegam ao fechamento (hoje 49,0%), tickets com nota (hoje 32,7%) e fechados com registro de tempo impossível (hoje 49,3%, que deve chegar a zero). Ao mesmo tempo, passo a registrar o que hoje não existe: data e hora de abertura, atendente, canal de entrada e forma de finalização, tempo trabalhado, custo do atendimento pelo custo da hora do atendente, reabertura, tempo sem resposta depois do encaminhamento para uma pessoa, tempo de espera dos críticos, tempo da abertura ao fechamento e satisfação na entrada e na saída. A nota de 1 a 5 continua, para manter a comparação com o histórico, e o NPS entra ao lado dela. Como essas métricas novas nunca foram medidas, os primeiros 30 dias são a linha de base delas, e a comparação começa no ciclo seguinte. O levantamento do processo com o time vai trazer outras métricas, e todas entram no mesmo dashboard.

| Indicador com linha de base | Hoje | Funcionou se | Base |
|---|---|---|---|
| Tickets sem nenhuma resposta | 33,3% (2.819) | cair | 8.469 |
| Críticos sem resposta | 692 | cair | 2.129 críticos |
| Respondidos que fecham | 49,0% (2.769) | subir | 5.650 |
| Tickets com nota | 32,7% (2.769) | subir | 8.469 |
| Fechados com tempo impossível | 49,3% (1.365) | chegar a zero | 2.769 |

Métricas novas cobrem as lacunas 1, 3, 4, 5, 7 e 9 de `docs/lacunas-de-dado.md`.
