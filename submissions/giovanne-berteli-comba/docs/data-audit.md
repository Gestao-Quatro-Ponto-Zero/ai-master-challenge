# Auditoria dos datasets — D01

**A base permite explorar categorias e demonstrar classificação, mas não sustenta
um diagnóstico de tempo total de atendimento nem uma economia medida em horas.**
Os campos temporais não têm a unidade sugerida pelo briefing e quase metade dos
pares de tickets encerrados está em ordem cronológica incompatível com seus nomes.

Auditoria executada em 02/11/2026 nos dois arquivos oficiais, versão 1. Evidências:
[manifesto e hashes](../data/manifest.json), [resultado agregado](../data/audit.json),
[código](../solution/audit_data.py), [reprodução](../data/README.md) e
[execução em diretório limpo](review-evidence/data-reproduction.json).
O resultado descreve os arquivos; não comprova uma operação real nem avalia IA.

## Fontes, dimensões e schema

| Fonte oficial | Arquivo dentro do ZIP | Linhas | Colunas | Bytes do CSV |
| --- | --- | ---: | ---: | ---: |
| [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset) | `customer_support_tickets.csv` | 8.469 | 17 | 3.945.533 |
| [IT Service Ticket Classification Dataset](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset) | `all_tickets_processed_improved_v3.csv` | 47.837 | 2 | 14.568.920 |

O primeiro volume difere dos ~30 mil anunciados no briefing. Os metadados dos
publicadores declaram CC0: Public Domain para ambos; o manifesto registra a
declaração consultada, sem certificar a origem de cada ticket. As atualizações
informadas são de 02/06/2023 e 18/02/2024, respectivamente. O download anônimo usou
a versão fixada na URL; os ZIPs e seus CSVs têm hashes próprios.

O primeiro CSV contém identificador, nome/email/idade/gênero, produto e data de
compra, tipo, assunto, descrição, status, resolução, prioridade, canal, primeira
resposta, resolução temporal e satisfação. O segundo contém somente `Document`
e `Topic_group`. O JSON lista cada coluna, tipo observado, valores distintos,
ausências e falhas de parsing. Não há coluna compartilhada que estabeleça uma
chave de entidade entre os arquivos. Escolher seus papéis é a etapa D02.

## Cobertura e unidades do primeiro dataset

| Status | Tickets | Primeira resposta presente | Resolução temporal presente | Satisfação presente |
| --- | ---: | ---: | ---: | ---: |
| Closed | 2.769 | 2.769 | 2.769 | 2.769 |
| Open | 2.819 | 0 | 0 | 0 |
| Pending Customer Response | 2.881 | 2.881 | 0 | 0 |
| Total | 8.469 | 5.650 | 2.769 | 2.769 |

`Resolution` também está preenchido apenas nos 2.769 encerrados. Os demais campos
não têm células vazias. As 2.769 notas observadas são inteiros entre 1 e 5:
553 notas 1, 549 notas 2, 580 notas 3, 543 notas 4 e 544 notas 5.
A cobertura é **32,70% de todos os tickets e 100% dos encerrados**. Comparações
de satisfação descrevem esse subconjunto; não representam a satisfação dos 5.700
casos ainda não encerrados nem demonstram causalidade.

`First Response Time` e `Time to Resolution` são timestamps no formato
`YYYY-MM-DD HH:MM:SS`, sem fuso informado. Todos os valores presentes fizeram
parsing; isso não garante validade operacional. O primeiro campo vai de
31/05/2023 21:55:39 a 02/06/2023 00:54:21; o segundo, de 31/05/2023 21:53:30 a
02/06/2023 00:55:33. **Não há data/hora de abertura do ticket.** `Date of Purchase`
é data de compra, não início do atendimento.

Ao calcular exclusivamente `resolução − primeira resposta`, em horas:

- 2.769 pares estão presentes; **1.365 (49,30%) são negativos**, 2 são zero e
  1.402 positivos.
- Restam 1.404 pares não negativos. A mediana de 6,34 h e o P95 de 18,51 h
  descrevem apenas esse subconjunto, já selecionado pela condição cronológica.
- Esse intervalo é posterior à resposta, não o tempo até responder nem o tempo
  total de resolução. Não equivale a esforço ativo. Os negativos foram contados
  e preservados; não aplicamos valor absoluto, troca de datas ou preenchimento.

Consequência: não ranquear canais por suposta latência total, calcular SLA desde a
abertura ou converter esses intervalos em desperdício de trabalho. Para isso são
necessários eventos de abertura/fechamento com semântica confirmada e medição de
esforço. Na ausência deles, qualquer cenário de horas/custo precisa explicitar
premissas e ser identificado como simulação (A01), não economia observada.

## Texto, duplicatas e rótulos

Não há linhas integralmente duplicadas em nenhum arquivo. Os 8.469 IDs do primeiro
são únicos; isso não elimina duplicatas de conteúdo.

| Propriedade do texto | Descrição do primeiro dataset | Document do segundo |
| --- | ---: | ---: |
| Células não vazias | 8.469 | 47.837 |
| Textos distintos exatos | 8.077 | 47.837 |
| Textos distintos após normalização | 8.066 | 47.837 |
| Grupos normalizados repetidos | 54 | 0 |
| Linhas nesses grupos | 457 | 0 |
| Grupos com mais de um rótulo | 49 | 0 |
| Linhas nos grupos com rótulos conflitantes | 446 | 0 |

A normalização usa Unicode NFKC, casefold e redução de espaços, preservando
pontuação. No primeiro arquivo, o rótulo comparado foi `Ticket Type`; no segundo,
`Topic_group`. Os 403 registros excedentes nos grupos repetidos do primeiro não
foram removidos. D02/V00 devem impedir que o mesmo conteúdo atravesse conjuntos
de ajuste e avaliação e tratar os conflitos sem escolher um rótulo arbitrário.
Não foram pesquisadas todas as paráfrases ou variantes semanticamente próximas.

Todas as 8.469 descrições contêm trechos entre chaves ainda não preenchidos,
como `{product_purchased}`. Os 2.769 textos de resolução têm de 3 a 8 palavras,
mediana 5. São sinais de conteúdo baseado em modelos de texto e de baixa adequação imediata como
base de respostas; não provam, isoladamente, a origem sintética de todo o arquivo.
Não foi feita avaliação semântica de cada resolução. Os emails usam exclusivamente
os domínios `example.com`, `example.net` e `example.org`; isso não certifica que
todo texto dos dois arquivos esteja anonimizado.

## Suporte por classe no dataset IT

| Topic_group | Tickets |
| --- | ---: |
| Hardware | 13.617 |
| HR Support | 10.915 |
| Access | 7.125 |
| Miscellaneous | 7.060 |
| Storage | 2.777 |
| Purchase | 2.464 |
| Internal Project | 2.119 |
| Administrative rights | 1.760 |

Não há células vazias nas duas colunas. O texto tem de 2 a 981 palavras, mediana
26. O desbalanceamento requer métricas por classe e baseline comparável antes de
qualquer alegação de desempenho. Não há identificador de cliente, timestamps,
satisfação ou chave de ligação ao primeiro arquivo. A ausência de duplicatas
normalizadas não garante independência de entidades, templates ou paráfrases.

## Validação e consequência para a próxima etapa

Os testes verificam cálculos de quantis, populações, intervalos negativos,
conflitos de rótulos, parsing, integridade dos CSVs e preservação dos dados brutos.
A reprodução em diretório limpo baixou os dois ZIPs novamente e gerou JSON
idêntico byte a byte. A saída da suíte fica em
`docs/review-evidence/data-audit-tests.txt`; o recibo dependente das entradas fica
em `docs/review-evidence/data-audit-current.json`.

D01 está concluída como aquisição e auditoria. D02 deverá definir papéis
complementares para os datasets, limites das métricas operacionais e tratamento
dos rótulos conflitantes, sem criar um join artificial ou transferir a taxonomia IT
sem validação. A arquitetura da aplicação, os conjuntos de avaliação, as metas de
qualidade e qualquer ganho operacional continuam pendentes.
