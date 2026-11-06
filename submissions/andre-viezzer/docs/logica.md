# Lógica do score

## Em uma frase

**Score 0 a 100 = Valor (até 60) + Momento (até 40).** A **ação** de cada deal (o que fazer hoje) vem só do momento e não depende do preço. O score decide a **ordem** dentro de cada ação.

É uma **política de priorização explícita**, não um preditor de ganho. O motivo está abaixo.

## Por que não há "probabilidade de fechar" no score

O caminho óbvio, que um LLM gera quando recebe o brief, é um score ponderado: taxa de ganho do vendedor, da conta, do setor, do produto, porte etc. Testei isso de três formas, sempre **fora da amostra**:

1. **Fechados antes x depois de jul/2017**: AUC de 0,49 a 0,52 para vendedor, produto, conta, vendedor x produto, setor, região, porte, preço, carga do vendedor e "conta já comprou o produto".
2. **Calibração**: o quintil que o modelo de atributos chamava de "74% de chance" fechou 64%; o de "59%" fechou 62%. Plano.
3. **Snapshot (simula o uso real)**: em 01/05, 01/07 e 01/09/2017, pego os deals que estavam em Engaging naquele dia, com a idade que tinham, e ordeno usando só o passado. Resultado ([validacao.md](validacao.md)):

| Fator | mai | jul | set |
|---|---|---|---|
| Idade do deal (curva de sobrevivência) | 0,512 | 0,517 | 0,553 |
| Vendedor x produto | 0,460 | 0,492 | 0,552 |
| Conta | 0,486 | 0,475 | 0,460 |
| Vendedor | 0,458 | 0,507 | 0,530 |
| Produto | 0,481 | 0,533 | 0,500 |

0,50 = cara ou coroa. Com ~1.000 deals por corte, o intervalo de 95% tem ±0,04: quase todos incluem 0,50. **Nada ordena ganhos de forma confiável neste dataset**, nem a idade do deal. A primeira versão deste projeto usava a idade como "Chance"; o crítico independente mostrou que ela também não passaria no meu próprio gate e eu a tirei do score.

Um score com "chance 78%" teria cara de inteligente e seria enfeite. O vendedor correria atrás de um número que no trimestre seguinte não se sustenta.

## O que é real e acionável

Previsão de ganho não é a única coisa que importa para priorizar. Três fatos se sustentam nos dados:

1. **Valor varia 500x** (R$ 300 a R$ 146.209). É conhecido, não estimado. Ganhos fecham entre 87% e 112% do preço de tabela (decis 10 a 90), então tabela é uma boa estimativa de valor.
2. **Metade das perdas acontece nos primeiros 14 dias** de Engaging (51%). Isso não diz *quem* vai perder, diz *quando* um contato tem mais chance de mudar o desfecho.
3. **Nenhum deal levou mais de 138 dias** para fechar, em 6.711 fechados (o teto já era 138 no corte de maio/2017). Um deal na reta final tem prazo; um deal além disso está fora de qualquer padrão histórico.

## As parcelas

### Valor (0 a 60)
Preço de tabela em **escala log**: R$ 300 = 0, R$ 146.209 = 60.

- Log porque o esforço por deal não escala 500x com o ticket. Em escala linear, metade do catálogo viraria zero.
- É o maior peso porque é o único fator que diferencia deals de forma comprovada.

### Momento (0 a 40)

| Estado | Regra | Pontos | Ação | Por quê |
|---|---|---|---|---|
| Janela de risco | Engaging ≤ 14 dias | 40 | **Contato urgente** | 51% das perdas acontecem aqui |
| Reta final | Engaging 90 a 138 dias | 35 | **Empurrar fechamento** | Todo deal histórico fechou até o dia 138. Mostra "faltam X dias" |
| Maduro | Engaging 15 a 89 dias | 25 | **Manter cadência** | Passou do risco, ainda tem tempo |
| Prospecção | sem `engage_date` | 10 | **Avançar para Engaging** | O histórico nunca mostra Prospecting → Won; não há chance a estimar |
| Zumbi | Engaging > 138 dias | 0 | **Verificar no CRM** | Fora de qualquer ciclo histórico. Vai para aba separada |

**A ação não depende do preço.** Um GTX Basic de R$ 3.004 aos 120 dias recebe "Empurrar fechamento", igual a um GTK 500. O score só define quem vem primeiro.

### Consequência assumida

Dentro da mesma ação, a ordem é por valor. É uma escolha deliberada: se nenhum atributo diferencia chance, o que sobra para desempatar é quanto o deal vale. O que torna isto diferente de "ordenar por valor":
- a ação vem do momento: o KPI "Contato urgente" ou "Empurrar fechamento" lista todos os deals naquele estado, de qualquer ticket, e o MG Special de R$ 300 aos 120 dias recebe a mesma ação do GTK 500;
- no mesmo ticket, o momento reordena: um GTX Pro em janela de risco (83) vem antes de um GTX Pro em cadência normal (68);
- 1.291 deals saem da lista principal (zumbis);
- prospecção fica atrás de qualquer Engaging de mesmo ticket.

## O que aparece mas não pontua

No detalhe do deal:
- "Deals nesta idade fecharam X%": informativo, com aviso de que é quase igual para todos.
- Histórico do vendedor no produto e da conta: contexto para a conversa, com aviso de que não previu resultado.
- Valor esperado (tabela x curva de sobrevivência) só para Engaging dentro do ciclo. Prospecção e zumbis mostram "desconhecido".

## Gate automático para dados reais

A cada `python scorer.py`, o backtest roda de novo. Se vendedor x produto ou conta tiverem AUC ≥ 0,55 **nos três cortes**, entram como ajuste em log-odds na chance, sem mudar código. Neste dataset, nenhum passa. Em CRM real, onde vendedor e conta costumam importar, podem passar.

## Parâmetros (topo de `solution/scorer.py`)

| Constante | Valor | Por quê |
|---|---|---|
| `REF_DATE` | 2017-12-31 | Último fechamento do dataset. Em produção: `date.today()` |
| `EARLY_WINDOW` | 14 | Onde a curva de perdas achata |
| `FINAL_STRETCH` | 90 | A partir daqui, menos de 50 dias até o teto |
| `GATE` | 0,55 em todos os cortes | Acima do ruído (IC ±0,04 com ~1.000 deals) |
| `PRIOR_K` | 40 | Shrinkage: grupo com 40 deals pesa metade a própria taxa |
| `PTS_VALOR`, `PTS_MOMENTO` | 60 / 40 | Valor é o único diferenciador comprovado; momento define a ação |
