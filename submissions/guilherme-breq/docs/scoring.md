# Scoring: lógica, evidências e limites

## A pergunta

A Head de RevOps disse: *"vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar"*. Por isso o score precisa responder três coisas, nesta ordem:

1. **Este deal ainda está vivo?** Se não está, ele não deveria ocupar o tempo de ninguém.
2. **Quanto ele vale?**
3. **É agora?** Ou seja, ele está perto de se decidir, a ponto de a ação do vendedor mudar o resultado? Ou está esfriando?

A pergunta óbvia, "qual a chance de ganhar?", ficou de fora, porque os dados não sabem respondê-la (ver abaixo).

## O que os dados mostraram

| Achado | Número | Consequência |
|---|---|---|
| Pipeline aberto | 2.089 deals (1.589 Engaging e 500 Prospecting) | É o universo a priorizar |
| Ciclo máximo histórico | Nenhum dos 6.711 deals fechados levou mais de **138 dias** | Define o corte de "vivo" |
| Engaging acima de 138 dias em 31/12/2017 | **1.291 de 1.589 (81%)** | A maior parte do pipeline é zumbi |
| Win rate global | 63,2% | — |
| Win rate por produto, setor, região e manager | Tudo entre 60% e 65% | Não diferencia |
| Win rate por vendedor | De 55% a 70%, mas correlação de **0,36** entre semestres | Instável |
| Win rate por conta e por vendedor × produto | Correlação de **−0,07** entre semestres | É ruído |
| `close_value` / preço de tabela nos ganhos | Mediana de 1,00 | O preço de tabela serve como valor do deal aberto |
| Deals abertos sem conta vinculada | 1.425 de 2.089 (68%) | Conta e setor não podem sustentar o score |
| Produto `GTXPro` no pipeline × `GTX Pro` no catálogo; setor `technolgy` | — | Normalizado no código |

## Como cada sinal foi testado

Para medir se um sinal **prevê o futuro**, e não só descreve o passado, "congelei" o CRM em datas passadas. Em cada data S:

- o modelo aprende só com o que se sabia em S;
- cada deal aberto em S é pontuado com a idade que tinha **naquele dia**;
- depois confiro o que aconteceu.

A métrica é a AUC: 0,5 = cara ou coroa, 1 = acerta sempre.

### Chance de ganhar (`analysis/04_backtest.py`), 5 snapshots

| Variante | AUC médio | Brier médio |
|---|---|---|
| Média global (referência) | 0,50 | **0,2215** |
| Curva de sobrevivência por idade | 0,519 | 0,2235 |
| + histórico do vendedor (shrinkage, k=50) | 0,505 | 0,2248 |
| + produto | 0,506 | 0,2252 |
| + setor da conta | 0,503 | 0,2252 |

**Nenhuma combinação de atributos prevê ganho ou perda**, e todas erram mais do que chutar 63% pra todo mundo (Brier maior). *Ressalva:* o teste só usa deals que acabaram fechando, porque só eles têm o rótulo ganho/perdido. A conclusão vale para "dado que vai fechar, ganha ou perde?".

### Momento (`analysis/06_momentum_km_backtest.py`), 3 snapshots

Alvo: o deal se decidiu (ganho ou perdido) em até 30 dias depois de S? Esse alvo é conhecido para **todo** deal aberto em S, então o teste usa todos os vivos, sem filtro.

| Snapshot | Vivos em S | Decidiram em 30d | AUC Kaplan-Meier | Previsto (média) |
|---|---|---|---|---|
| 01/05/2017 | 1.593 | 40,8% | 0,624 | 25,5% |
| 01/07/2017 | 1.533 | 9,7% | 0,526 | 24,6% |
| 01/09/2017 | 1.854 | 27,8% | 0,785 | 24,0% |
| **Média** | | **26,1%** | **0,645** | **24,7%** |

- **A curva é estimada por Kaplan-Meier.** Os deals fechados são eventos, e os que seguem abertos entram como *censurados*: estavam em risco e não se decidiram. Ignorá-los (minha primeira versão) superestimava a chance (previa 44% em média).
- **A calibração por faixa** é boa entre 10% e 50% de previsão e otimista acima de 50% (prevê 57%, acontece 29%). Por isso o app usa o momento **relativo ao pico** para ordenar, e mostra a porcentagem como contexto.
- **O sinal é real, mas modesto e instável.** Julho/2017 teve poucas decisões (10%) e ali a AUC ficou perto de 0,5. É o melhor sinal disponível, não um oráculo.

### Zumbis

Nos 3 snapshots, **411 deals únicos** estavam abertos há mais que o maior ciclo conhecido. **Nenhum fechou** até o fim dos dados (31/12/2017, de 4 a 8 meses depois). Isso não prova que a chance seja zero, e por isso 138 dias é tratado como um **corte heurístico** com forte evidência, não como lei.

### Descartado de propósito

- **Efeito fim de trimestre.** Deals fechados em mar, jun, set e dez têm 81% de win rate, contra 52% nos outros meses. Mas o efeito é idêntico nos dias 1–10, 11–20 e 21–31 desses meses, e um empurrão real de fim de trimestre se concentraria nos últimos dias. O padrão parece ter vindo do gerador do dataset. Além disso, a data de fechamento de um deal aberto ainda não existe, então usá-la seria vazar o futuro.
- **Setor e porte da conta.** Sem efeito, e 68% dos deals abertos nem têm conta.
- **ML (XGBoost etc.).** Se nenhum atributo individual separa ganho de perda fora da amostra, um modelo mais complexo só encontraria combinações de ruído. O brief pediu explicabilidade.

## A curva de momento

p(decidir nos próximos 30 dias | idade), com todo o histórico:

| Idade | 0 | 10 | 20 | 30 | 45 | 60 | 75 (pico) | 90 | 105 | 120 | 135 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| p | 38% | 16% | 7% | 11% | 23% | 36% | **44%** | 42% | 29% | 13% | 2% |

Três fases, que o app mostra ao vendedor:

- **Ainda cedo** (até 56 dias): pouca coisa se decide, exceto os deals resolvidos logo nos primeiros dias.
- **Fase de decisão** (57 a 101 dias): a faixa contínua ao redor do pico em que a curva fica em 75% do pico ou mais. É aqui que a ação do vendedor mais pesa.
- **Esfriando** (depois de 101 dias): a chance de decisão despenca, e a maioria dos deals nessa idade vira zumbi. É a "oportunidade esfriando" da Head de RevOps, agora medida.

A faixa precisa ser *contínua ao redor do pico* porque a curva também é alta nos primeiros dias (38% aos 0 dias). Um limiar simples juntaria os dois e rotularia um deal de 2 dias como "fase de decisão". Esse bug existiu e foi corrigido, com teste.

## A fórmula

```
se idade > 138 dias  → ZUMBI: sem score; vai para a pilha "Encerrar"
se não engajou       → PROSPECÇÃO: score = só Valor
senão                → score = Valor (0–60) + Momento (0–40)

Valor   = 60 × (ln preço − ln 55) / (ln 26.768 − ln 55)
Momento = 40 × p(decisão em 30 dias | idade) / p_pico
```

- **Por que log no valor:** os preços vão de US$ 55 a US$ 26.768 (486×). Em escala linear, só o GTK 500 apareceria. Em log, cada vez que o preço dobra, o deal ganha o mesmo tanto de pontos.
- **Por que 60/40:** é julgamento, não ajuste fino. O valor é o sinal mais forte e mais estável, e o momento diz *quando* agir. As constantes ficam no topo de `src/lib/scoring.ts`.
- **Momento relativo ao pico:** 40 pts = a idade em que mais deals se decidem. Como a calibração acima de 50% é otimista, ordenar pela posição relativa é mais robusto do que usar a porcentagem crua.
- **Desempate:** com o mesmo score, vem primeiro quem tem menos dias restantes no ciclo.
- **Próxima ação** (`src/lib/playbook.ts`, função pura `nextStep`): o motor decide *quem* vem primeiro; o playbook decide *o que fazer* com cada deal, usando só o que o motor já devolve (status, pontos de valor, idade, dias restantes) e a fase de decisão da curva (dias 57 a 101). A primeira regra que casar vale:

| # | Regra | Ação (verbo) | Texto |
|---|---|---|---|
| 1 | Zumbi | Encerrar | "Confirmar se está vivo ou marcar como perdido" |
| 2 | Prospecção | Abrir | "Agendar o primeiro contato" |
| 3 | Ticket baixo (valor < 10 pts, hoje só o MG Special, US$ 55) | Lote | "Resolver por e-mail, sem ligação"; a 20 dias ou menos do limite: "E-mail de sim ou não: faltam N dias" |
| 4 | 20 dias ou menos do limite | Decidir | "Forçar o sim ou o não: faltam N dias" |
| 5 | Fase de decisão, ticket alto (valor ≥ 40 pts) | Ligar | "Ligar hoje e propor data de fechamento" |
| 6 | Fase de decisão, ticket médio | Ligar | "Ligar esta semana: está na fase de decisão" |
| 7 | Antes da fase de decisão | Preparar | "Proposta pronta: entra na fase de decisão em N dias" |
| 8 | Depois da fase de decisão | Reengajar | "Reengajar: saiu da fase de decisão há N dias" |

  **Por que o ticket baixo vira lote:** a ação antiga ignorava o valor, então um deal de US$ 55 pedia a mesma ligação que um de US$ 26 mil. Para a Rosalina, 11 dos 16 deals vivos valem US$ 55 (US$ 605 somados): uma ligação custa mais que o deal.

  `scoring.ts` não mudou: o campo `action` do motor (cinco rótulos fixos) continua nele e nos testes, mas o app mostra o passo do playbook.

No estado atual (31/12/2017), os 298 deals vivos se dividem assim (conferido por teste contra os dados reais):

| Ação | Deals |
|---|---|
| Ligar | 72 |
| Forçar o sim ou o não (Decidir) | 76 |
| Reengajar | 53 |
| Preparar proposta | 35 |
| Em lote (e-mail) | 62 |

Antes, com a ação do motor, a divisão era 98 / 89 / 75 / 25 / 11, com dois rótulos dominando e sem distinguir o valor.

## Robustez do código

Depois da revisão independente, o motor também passou a:

- recusar histórico insuficiente em vez de produzir limites inventados (−∞, NaN);
- ignorar preços inválidos no catálogo e sinalizar produto sem preço;
- tratar data de engajamento futura (idade 0, com aviso) e inválida (vai para prospecção, com aviso).

Tudo isso coberto por testes (`src/lib/scoring.test.ts`).

## Limitações

1. **"Hoje" é 31/12/2017**, a última data do CRM. Em produção seria a data real, e a curva e o ciclo máximo seriam recalculados a cada carga (o código já faz isso).
2. **O corte de 138 dias vem deste histórico.** Com dados reais, eu usaria um percentil por produto, revisado periodicamente.
3. **O momento é um sinal modesto** (AUC média 0,65, instável entre períodos). Ele ordena melhor que o acaso, mas não deve ser lido como certeza.
4. **Valor é preço de tabela.** Não há desconto nem quantidade no CRM.
5. **Prospecção não tem data de início**, então não há como medir momento. Fica ordenada só por valor.
6. **Não há dados de atividade** (último contato, e-mails, reuniões). É o sinal que mais falta, porque "esfriar" se mede pelo tempo sem contato. Seria o primeiro dado a pedir.
7. **O CRM é só leitura.** O vendedor marca Feito, Adiar e Não está vivo no navegador (`localStorage`), mas nada é gravado no CRM: um zumbi não vira "perdido" lá.
8. **Dataset sintético.** As conclusões valem para estes dados. O que se transfere é o **método**: testar cada sinal fora da amostra, com a população certa e tratando a censura, antes de colocá-lo no score.
9. **Viewport testado: 390 a 1440 px, no Chrome.** Abaixo de 360 px o texto do mapa fica menor que 13 px (em 320 px, ~11,5 px). Firefox, Safari e leitor de tela real não foram testados.
10. **Ao reabrir com o vendedor lembrado**, a tela de entrada pode piscar antes de abrir a fila.
11. **Se outra aba apagar as marcações**, a fila da aba aberta se atualiza, mas o aviso para leitor de tela fica desatualizado até a próxima ação.

## Para escalar

- Ligar no CRM real (API ou export diário) em vez dos CSVs; a função `getPipeline` é o único ponto a trocar.
- Recalcular o modelo a cada carga (já é automático: nada está fixo no código, exceto pesos e limiares).
- Gravar a ação do vendedor no servidor (hoje Feito, Adiar e Não está vivo ficam só no navegador, em `localStorage`) para fechar o ciclo e medir se a priorização aumentou a receita.
- Coletar atividade (e-mail, reunião, ligação) e testar "dias sem contato" como terceiro componente, pelo mesmo backtest.
- Autenticação por vendedor, para cada um ver só a própria carteira, e alerta semanal por Slack ou e-mail com o Foco da semana.
