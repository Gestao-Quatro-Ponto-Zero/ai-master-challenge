# Decisões de projeto

As perguntas que a banca provavelmente vai fazer, com a resposta curta e o número que a sustenta.

## 1. Por que o score se baseia em tempo, e não no perfil do vendedor ou da conta?

Porque testamos o perfil, e ele não funciona neste histórico. Num backtest temporal (a taxa é
calculada no passado e conferida no futuro), estes atributos ficaram em cara ou coroa:

| Atributo | AUC |
|---|---|
| Taxa histórica do vendedor | 0,52 |
| Taxa histórica da conta | 0,51 |
| Taxa histórica do produto | 0,51 |
| Histórico da conta (já comprou / perdeu nos últimos 90 dias) | 0,49 |
| Afinidade do vendedor (produto e setor) | 0,49 |
| **Score composto com todos esses pilares (1ª versão)** | **0,50** |
| **Chance de ganhar até o fim do trimestre, dada a idade do deal** | **0,63** (deals vivos) · **0,72** (pipeline inteiro) |

Setor, região, manager e porte têm win rate entre 61% e 66% em todas as faixas.
Colocar esses atributos no score daria uma aparência de precisão sem nenhum poder de previsão.
O que separa ganho de perda é **o tempo**: os deals perdidos morrem cedo (mediana de 14 dias),
e quem sobrevive fecha mais.

## 2. Por que 138 dias?

É o maior ciclo de um deal fechado no histórico, e o número sai dos dados, não de uma escolha.
No backtest, **13.871 vezes** um deal estava aberto além desse limite, e **nenhum** ganhou
depois. Por isso:

- deals acima de 138 dias têm chance zero;
- saem do valor esperado e vão para **Encerrar** ou **Requalificar**;
- "Requalificar" significa perguntar ao cliente e, se o projeto continuar, **encerrar este e
  abrir uma oportunidade nova**, com o relógio zerado.

Hoje são 1.291 deals nessa situação (62% do pipeline aberto).

## 3. Por que existem duas métricas, score e valor esperado?

Elas respondem a perguntas diferentes:

- **Score (0–100):** para a leitura humana. Explica-se em três barras (chance, valor,
  engajamento/dado) e define a ação.
- **Valor esperado** (chance × preço × desconto histórico): para ordenar a lista e montar a
  lista de resgate. É a conta honesta de quanto o deal vale para o trimestre.

## 4. Por que os cortes de ação são percentis, e não números fixos?

Porque a calibração muda com a data: ela é rolling-origin e só usa o que se sabia naquele dia.
Com cortes fixos de 85/70, "Atacar agora" ia de 82 a 893 deals conforme a semana. Com o top
15% dos deals vivos, ficam de 7 a 8 por vendedor de maio a dezembro, uma lista que dá para
trabalhar na semana.

## 5. Por que a chance não passa de ~41%?

Porque é o que aconteceu de fato. O estimador bruto chegava a prever 80%, mas a taxa real
nessas faixas era de 30% a 40%. A recalibração isotônica força a chance a seguir o que
aconteceu. Neste dataset, nenhum perfil de deal ganha mais que isso dentro de um trimestre.

## 6. Como garantir que a simulação de datas passadas não "cola" do futuro?

Por três mecanismos:

- **Snapshot:** `snapshot(t)` reconstrói o pipeline como ele estava em *t*. Os deals que
  fecharam depois voltam a ficar abertos.
- **Benchmarks:** calculados só com os deals fechados até *t*.
- **Calibração rolling-origin:** a curva usada em *t* só conta observações cujo desfecho já era
  conhecido em *t*.

Há teste automatizado para cada um desses pontos.

## 7. Por que a IA não calcula o score?

Porque o motor é determinístico, calibrado e testado, e um LLM calculando probabilidade seria
pior e impossível de auditar. A IA só **escreve sobre números prontos**:

- todo número da resposta é conferido contra os fatos;
- frases que atribuem chance a vendedor ou conta (o que os dados mostram não funcionar) são
  bloqueadas;
- sem chave, entra o texto-template e a ferramenta funciona igual.

## 8. Por que o modo emergência liga no último mês do trimestre?

Porque é onde os ganhos se concentram. Deals fechados no último mês do trimestre ganharam
**81%** das vezes, contra **52%** nos outros meses. A janela tem base nos dados, não só no
calendário.

## 9. Por que a meta é a média trimestral?

Porque o dataset não tem meta real. A média dos trimestres completos anteriores é o padrão
mais defensável (o Q1/2017 só tem março e foi descartado). O `META_FATOR` permite usar média
+10%. Em produção, a meta seria cadastrada, e a média ficaria só como sugestão.

## 10. Por que Prospecting aparece sem chance?

Porque o CRM não tem data de engajamento para esses deals, então não existe histórico
comparável. Mostrar um número que sabemos ser otimista enfraqueceria a credibilidade do resto.
Eles seguem uma trilha própria (**Primeiro contato**) e ficam fora do valor esperado.
