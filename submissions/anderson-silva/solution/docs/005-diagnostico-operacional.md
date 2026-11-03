# Diagnóstico operacional do suporte (Dataset 1)

- **Status:** versão final da submissão, 2026-11-03.
- **Origem:** análises registradas no [audit trail](../../process-log/002-audit-trail.md), principalmente os itens 71, 91, 93, 95, 143, 145, 158 e 165. A proposta que parte deste diagnóstico está no [docs/004](004-proposta-automacao.md).
- **Autoria:**
  - Direção, decisões e ajustes da pessoa candidata: tratar os dados como reais, usar as colunas de tempo só como marcadores de status (item 95), medir o desperdício com uma única premissa, apresentar o limite da foto e o custo pela taxa do Diretor.
  - Cálculos, redação e estrutura: IA, com aprovação da pessoa candidata. Todos os números vêm de scripts do projeto.

## Resumo executivo

Dois terços dos tickets (67,3%) estão parados: 33,3% sem nenhuma resposta e 34,0% aguardando o cliente. O acúmulo é igual em todos os canais, prioridades e tipos, e também em todas as combinações entre eles. Há indício de que a fila não respeita a prioridade.

Nenhuma variável disponível explica o CSAT, nem sozinha nem em conjunto: um modelo com as 21 variáveis acerta 21,3% das notas, contra 20,9% do chute ingênuo. O tempo de resposta não pode ser testado, porque as colunas de tempo não medem duração (prova no Anexo A.1).

O desperdício que dá para quantificar é a triagem manual: **11,79 × m horas a cada 1.000 tickets**, em que m é o número de minutos de triagem por ticket (35,4 horas com m = 3). O custo é esse número de horas multiplicado pelo custo por hora da empresa. O maior desperdício em volume é o estoque parado, que sem tempo registrado não dá para converter em horas. Por isso, a primeira recomendação é registrar o tempo de cada etapa.

## 1. Onde o fluxo trava

Sem duração no dado, "travar" é o acúmulo num estágio que não é o final. O estágio vem do status, e as colunas de tempo confirmam: aberto não tem nenhuma marcação, aguardando tem só a primeira resposta, fechado tem as duas.

| Estágio | Tickets | % |
|---|---|---|
| Aberto, sem 1ª resposta | 2.819 | 33,3% |
| Aguardando o cliente | 2.881 | 34,0% |
| Fechado | 2.769 | 32,7% |

**Por canal, prioridade e tipo (% de cada linha: aberto / aguardando / fechado):**

| Canal | % | Prioridade | % | Tipo | % |
|---|---|---|---|---|---|
| Chat | 33,0 / 34,4 / 32,5 | Low | 33,7 / 35,0 / 31,2 | Billing inquiry | 33,0 / 33,7 / 33,3 |
| Email | 32,7 / 33,7 / 33,6 | Medium | 33,2 / 35,2 / 31,7 | Cancellation request | 34,3 / 35,2 / 30,4 |
| Phone | 34,5 / 33,1 / 32,4 | High | 33,8 / 32,4 / 33,8 | Product inquiry | 32,4 / 35,1 / 32,5 |
| Social media | 32,9 / 34,9 / 32,2 | Critical | 32,5 / 33,4 / 34,1 | Refund request | 32,2 / 33,8 / 34,0 |
| | | | | Technical issue | 34,5 / 32,3 / 33,2 |

Nenhuma variável se associa ao estágio: canal V = 0,014, prioridade V = 0,022, tipo V = 0,023, produto V = 0,067, com p de 0,908 a 1 depois da correção de Bonferroni.

**Combinações (parcela parada = aberto + aguardando):**

| Combinação | Grupos | V de Cramér | p | Parcela parada |
|---|---|---|---|---|
| Canal × prioridade | 16 | 0,047 | 0,240 | 63,4% a 72,3% |
| Canal × tipo | 20 | 0,058 | 0,081 | 62,4% a 73,8% |
| Prioridade × tipo | 20 | 0,049 | 0,355 | 64,3% a 74,6% |
| Canal × prioridade × tipo | 80 | 0,107 | 0,081 | 56,6% a 80,6% |

O pior grupo é telefone, prioridade baixa e cancelamento, com 80,6% parados em 108 tickets. Nenhum dos piores grupos passa do acaso depois da correção (p de 0,186 a 1). O cancelamento aparece várias vezes entre os piores, o que vale acompanhar quando houver tempo registrado.

**Indício sobre a prioridade:** 32,5% dos críticos seguem sem resposta, contra 33,7% dos de prioridade baixa. Nas redes sociais, onde há risco de exposição, são 32,9%.

**Resposta:** o fluxo trava por igual, logo na entrada e na espera pelo cliente. O gargalo é estrutural, de capacidade ou de processo, e não de um canal, tipo ou combinação. Os "piores tempos de resolução" não podem ser medidos, porque o dado não tem duração (Anexo A.1).

**Limite:** é uma foto de um momento. Sem data de abertura, não dá para saber há quanto tempo cada ticket está parado, e parte dos abertos pode ter acabado de chegar. Pelo mesmo motivo, a conclusão sobre a prioridade é um indício: parcelas iguais de abertos só significam espera igual se os tickets chegarem num ritmo estável.

## 2. O que impacta a satisfação

O CSAT existe só nos 2.769 tickets fechados, todos com nota, e nenhum ticket aberto ou aguardando tem nota. As notas de 1 a 5 têm cerca de 20% cada, com média 2,99.

| Variável | Teste | p (Bonferroni) | Menor e maior média |
|---|---|---|---|
| Canal | Kruskal-Wallis | 1 | Phone 2,95 a Chat 3,08 |
| Prioridade | Kruskal-Wallis | 1 | Critical 2,96 a Low 3,05 |
| Tipo | Kruskal-Wallis | 1 | Refund request 2,93 a Cancellation request 3,03 |
| Assunto | Kruskal-Wallis | 1 | Delivery problem 2,80 a Installation support 3,18 |
| Produto | Kruskal-Wallis | 1 | Fitbit Versa Smartwatch 2,54 a Dyson Vacuum Cleaner 3,22 |
| Gênero | Kruskal-Wallis | 1 | Female 2,97 a Male 3,03 |
| Idade | Spearman (ρ = −0,004) | 1 | Não se aplica |
| Problema descrito pelo cliente | Kruskal-Wallis (p = 0,530) | 1 | Hardware 2,84 a Falha de software 3,20 |
| 13 sinais do cliente (urgência, contato repetido etc.) | Mann-Whitney | 1 em todos | Por exemplo, vários aparelhos 2,65 contra 3,00 sem o sinal; nenhuma diferença significativa |

**Todas as variáveis juntas:** um modelo com as 21 variáveis, avaliado em validação cruzada, acerta 21,3% das notas. O chute ingênuo acerta 20,9%, e os mesmos dados com as notas embaralhadas chegam a 23,1% (p = 0,085). Uma floresta aleatória, que capta combinações entre variáveis, acerta 19,9%. Nenhuma variável reduz o acerto em mais de 0,3% quando embaralhada.

**É o tempo de resposta?** Não dá para medir: as colunas de tempo não são duração (Anexo A.1). Mesmo nas leituras possíveis, nada se relaciona com o CSAT. A diferença entre as duas colunas dá p = 0,322. As durações reconstruídas dão p = 0,046, que vira 0,368 com a correção para 8 testes.

**Resposta:** com os dados atuais, nada explica o CSAT: nem canal, nem tipo de problema, nem prioridade, nem o que o cliente escreve. Os prováveis motores, como tempo de espera, número de contatos e qualidade da solução, não são registrados. Há dois sinais de cuidado: a taxa de resposta de 100% é incomum, e os clientes que mais esperam, ainda sem resposta, não avaliam.

## 3. Quanto estamos desperdiçando

### Onde: contagens reais

| Tipo | Aberto, sem 1ª resposta | Aguardando o cliente | Fechado | Total |
|---|---|---|---|---|
| Billing inquiry | 539 (33,0%) | 551 (33,7%) | 544 (33,3%) | 1.634 |
| Cancellation request | 582 (34,3%) | 597 (35,2%) | 516 (30,4%) | 1.695 |
| Product inquiry | 532 (32,4%) | 576 (35,1%) | 533 (32,5%) | 1.641 |
| Refund request | 564 (32,2%) | 592 (33,8%) | 596 (34,0%) | 1.752 |
| Technical issue | 602 (34,5%) | 565 (32,3%) | 580 (33,2%) | 1.747 |
| **Total** | **2.819 (33,3%)** | **2.881 (34,0%)** | **2.769 (32,7%)** | **8.469** |

### Quanto: horas e custo a cada 1.000 tickets

> **Horas de triagem economizadas = 1.000 × 70,8% × m ÷ 60 = 11,79 × m**
>
> **Custo economizado = 11,79 × m × c**, em que c é o custo por hora do atendente, com encargos
>
> Para o volume da empresa: multiplique pelo volume mensal ÷ 1.000

Com m = 3 minutos, são 35,4 horas a cada 1.000 tickets, e o custo é 35,4 × c. *Os 3 minutos são só ilustrativos; o Diretor troca m e c pelos valores dele.*

Ressalvas:
1. **Os 70,8% são uma referência, não uma garantia.** Foram medidos no Dataset 2, com outro domínio e outras categorias. No Dataset 1, a taxa precisa ser medida de novo quando existir histórico rotulado.
2. **É economia bruta.** O tempo para corrigir os encaminhamentos errados não entra.
3. **O resto continua com triagem humana:** tickets de baixa confiança, curtos ou ambíguos.

### O maior desperdício recuperável

| Desperdício | Tamanho | Dá para converter em horas? | Como recuperar (docs/004) |
|---|---|---|---|
| **Estoque parado:** 2.819 sem resposta e 2.881 aguardando o cliente | 67,3% dos tickets, o maior em volume | Não, sem tempo registrado | Fila por prioridade, alertas de prazo, cobrança automática do cliente e encerramento por prazo |
| **Triagem manual** | Todos os tickets | Sim: 11,79 × m horas a cada 1.000 | Classificador supervisionado, depois que houver histórico |
| **O que o cliente informa e a operação ignora:** urgência (8,4%) e contato repetido (5,4%) não mudam a prioridade | 87,9% dos tickets trazem algum sinal | Não | Opções marcáveis no formulário e prioridade sugerida pelas frases |

**Resposta:** o maior desperdício que dá para quantificar hoje é a triagem manual. O maior em volume é o estoque parado, mas, sem tempo registrado, ele não vira horas nem reais. Medir o tempo de cada etapa (docs/003) é o que permite quantificá-lo.

## Anexo A: detalhes

### A.1 Por que as colunas de tempo não medem duração

"First Response Time" e "Time to Resolution" guardam data e hora, não duração. Três fatos:

1. **Mesmo segundo:** os dois horários têm os mesmos segundos em 100% dos 2.769 fechados. Ao acaso, seriam 1,7% (item 71).
2. **Ordem invertida:** a resolução vem antes da primeira resposta em 1.365 dos 2.769 fechados.
3. **Mecanismo reconstruído:** cada valor é um relógio, que avança de 0 a 5 segundos por ticket (3,25 horas no total), menos um sorteio dentro de 24 horas (item 93).

Por isso, as duas colunas são usadas só como marcadores de etapa (premissa do item 95). Numa situação real, o passo seria buscar o dado na origem.

### A.2 Métodos

| Pergunta | Método | Onde roda |
|---|---|---|
| Estágios por variável | V de Cramér com qui-quadrado; correção de Bonferroni | `scripts/001-ticket-stats.py director-questions` |
| Combinações | V de Cramér por combinação; teste binomial por grupo contra a parcela geral; Bonferroni sobre 136 grupos; grupos com pelo menos 30 tickets | `scripts/006-diagnosis-deepening.py stall-combinations` |
| CSAT por variável | Kruskal-Wallis com ε², Spearman para idade, Mann-Whitney para os sinais; Bonferroni | `scripts/001` e `scripts/005-ticket-text-signals.py` |
| CSAT com todas as variáveis | Regressão logística e floresta aleatória em validação cruzada de 5 partes; teste com as notas embaralhadas 200 vezes; importância por embaralhamento de cada variável | `scripts/006-diagnosis-deepening.py csat-model` |
| Desperdício | Contagens reais e fórmula com uma premissa (m) | `scripts/001-ticket-stats.py director-questions` |

### A.3 Limites

- **Foto de um momento:** os estágios mostram onde os tickets estão, não há quanto tempo.
- **Sem tempo nem custo no dado:** as horas dependem de m, e o custo, de c.
- **CSAT só dos fechados:** quem espera não avalia.
- **Rótulos que não batem com o texto:** tipo e assunto não correspondem à descrição, e a resolução não tem sentido (itens 100 e 158).
