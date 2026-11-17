# Resumo executivo: Redesign de Suporte

**Para:** Diretor de Operações · **De:** Adson Valeriano · **Leitura:** 5 minutos

## A resposta curta
Hoje não dá para saber onde o suporte perde tempo, porque **os dados de tempo e satisfação não são confiáveis**. Mas dá para automatizar a triagem com segurança: a IA encaminha sozinha **cerca de 6 em cada 10 chamados com ~96% de acerto**, e o resto vai para uma pessoa.

## O que encontrei
1. **A operação não mede o que importa.** Em 49% dos chamados fechados, a resolução aparece antes da primeira resposta. A satisfação tem a mesma quantidade de notas 1, 2, 3, 4 e 5. Dois terços dos chamados não têm tempo nem nota. Com esse dado, qualquer "ranking de gargalos" seria chute.
2. **Um terço dos chamados está parado esperando o cliente** (2.881 de 8.469). É fila travada sem ninguém cobrar.
3. **A triagem automática funciona,** testada em 9.568 chamados reais de TI que o modelo nunca viu: com as regras de segurança ligadas, a IA decide sozinha **62,8%** e acerta **95,8%** deles.

## O que a IA faz e o que ela não faz
| A IA faz sozinha | Sempre vai para uma pessoa |
|---|---|
| Classificar e encaminhar quando tem ≥ 70% de certeza | Prioridade crítica |
| Mostrar chamados parecidos ao atendente | Dinheiro: reembolso, cobrança, cancelamento |
| | Segurança e permissões administrativas |
| | Qualquer caso em que a IA tenha dúvida |

## Recomendação, em ordem
| Quando | O quê | Por quê |
|---|---|---|
| Semana 1 | **Medir de verdade:** abertura, primeira resposta e resolução como duração; nota em todo chamado fechado | Sem isso, toda decisão de contratar ou automatizar é no escuro |
| Semana 1–2 | **Follow-up automático** para chamados aguardando o cliente (lembrete em 24 h e 72 h, fechamento com aviso em 7 dias) | Libera um terço da fila, com baixo risco |
| Semanas 2–6 | **Piloto de triagem** com os chamados da própria empresa, rodando em paralelo com a equipe por 2 semanas | O modelo foi provado em dados de TI; precisa ser confirmado no seu suporte antes de ligar |

## Quanto vale
- **Economia direta de triagem:** entre **~31 e ~79 horas por mês** (≈ **R$ 5.900 a R$ 14.700 por ano**), dependendo de a IA também encaminhar chamados de dinheiro para a fila do financeiro, sem decidir nada.
- **O ganho maior não é esse.** É velocidade: o chamado chega na fila certa na hora, sem esperar alguém ler, e cai menos na pessoa errada.
- Premissas: 30 mil chamados/ano, 3 min de triagem manual por chamado, R$ 15,64/hora (custo empresa de um operador de suporte técnico). A confirmar no piloto.

## Como vou provar o valor em 30 dias
| Indicador | Hoje | Meta do piloto (hipótese) | Como medir |
|---|---|---|---|
| Tempo do chamado até a fila certa | Não medido (depende de alguém ler) | Menos de 1 minuto em ~60% dos chamados | Hora de abertura x hora da triagem |
| Chamados encaminhados para a fila errada | Não medido | Reduzir pela metade | Contagem de reencaminhamentos |
| Chamados parados esperando o cliente | 34% | Abaixo de 20% | Status depois do follow-up automático |
| Tempo de resolução e satisfação | Não confiável | Linha de base nas 2 primeiras semanas; meta definida a partir dela | Novo registro de tempos e nota em todo chamado fechado |

## O que eu preciso para seguir
Acesso a 2.000 chamados reais da operação, rotulados com as categorias de vocês, e 2 semanas de piloto em paralelo com a equipe.

---
Detalhes, números e como reproduzir: [`README.md`](README.md)
