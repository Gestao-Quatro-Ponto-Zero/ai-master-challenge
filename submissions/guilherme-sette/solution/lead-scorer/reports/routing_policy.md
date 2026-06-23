# Politica de score, remanejamento e ultima tentativa

Data da analise: 2026-06-23

## Principio

O score nao deve responder apenas "qual deal e bom?". Ele deve responder "qual deal e melhor para este vendedor, agora, com estes dados e esta capacidade operacional?".

Por isso, o sistema deve separar quatro saidas:

- `priority_score`: prioridade do deal para a carteira atual.
- `routing_signal`: manter, consultar especialista, revisao gerente, remanejar ou ultima tentativa.
- `confidence_band`: confianca alta, media ou baixa.
- `reason_codes`: motivos legiveis para vendedor/manager.

## Corte para deals antigos

Base empirica nos CSVs:

- Oportunidades fechadas tem mediana de 45 dias ate fechamento.
- Oportunidades ganhas tem mediana de 57 dias.
- O p75 de oportunidades ganhas e 88 dias.
- O p90 de oportunidades ganhas e 106 dias.
- O pipeline aberto em `engaging` tem mediana de 165 dias, p75 de 263 dias e p90 de 319 dias.

Politica sugerida:

| Idade em `engaging` | Classificacao | Acao recomendada | Remanejar? |
|---:|---|---|---|
| 0-90 dias | Normal | Priorizar por score e fit | Sim, se fit gap for forte |
| 91-180 dias | Recovery | Revisao tática; pode remanejar com criterio | Sim, se passar nos gates |
| 181-270 dias | Intervention | Revisao gerente; plano de acao curto | Raro, apenas alto valor e alta confianca |
| >270 dias | Quarantine | Nutricao, close-lost operacional ou ultima tentativa | Nao, salvo excecao estrategica |

Gates para remanejamento:

- Conta conhecida.
- `recommended_differs_from_current = true`.
- Diferenca entre especialista e vendedor atual de pelo menos 12 pontos de match.
- Confianca do match >= 0,65.
- Preferencialmente idade entre 91 e 180 dias.
- Para 181-270 dias, exigir alto valor: `estimated_deal_value >= 4.821`.
- Para >270 dias, nao remanejar por padrao; usar ultima tentativa ou saneamento.

Aplicando esses gates aos dados atuais:

- 94 deals entram como candidatos estritos a remanejamento em janela de recovery, somando US$ 277.100.
- 13 deals entram como revisao gerente em janela de intervention, somando US$ 65.317.
- 6 deals muito antigos entram apenas como excecao de revisao, somando US$ 30.248.
- 384 deals de alto valor estao sem conta conhecida, somando US$ 2.128.634; estes devem ir para saneamento antes de qualquer remanejamento.

## Dados incompletos

Deal incompleto nao deve ser entregue automaticamente para top performer. Isso vicia a carteira do melhor vendedor com oportunidade mal qualificada.

Politica sugerida:

- Sem conta conhecida: capar `confidence_band` em baixa.
- Sem conta conhecida e alto valor: `manager_review` ou `corrigir_dados`, nao remanejamento.
- Sem `engage_date`: tratar como `prospecting`; nao calcular envelhecimento.
- Sem amostra historica suficiente de vendedor-segmento: fit neutro, nao punicao.
- Sem dados de conta, o fit empresa/setor/porte deve ser removido do calculo, nao imputado agressivamente.

## Distribuicao sem sobrecarregar especialistas

O roteamento irrestrito concentra recomendacoes em poucos vendedores:

| Vendedor recomendado | Deals recomendados | Valor recomendado | Open atual | Cap macio sugerido |
|---|---:|---:|---:|---:|
| Hayden Neloms | 1.153 | US$ 1.643.192 | 50 | 8 deals/ciclo |
| Maureen Marcano | 892 | US$ 3.298.823 | 72 | 11 deals/ciclo |
| Moses Frase | 44 | US$ 24.200 | 65 | 10 deals/ciclo |

Esse resultado prova que fit historico nao pode virar redistribuicao automatica.

Regras de balanceamento:

- Cap macio por ciclo: `max(5, 15% da carteira aberta atual)`.
- Cap duro por ciclo: `max(8, 25% da carteira aberta atual)`.
- Atingiu cap macio: novos deals viram `consultar_especialista`, nao transferencia.
- Atingiu cap duro: bloquear novas transferencias ate fechamento, perda ou devolucao.
- Se fit gap entre especialista e vendedor atual for < 8 pontos, manter com vendedor atual.
- Se fit gap for 8-12 pontos, sugerir playbook/consulta.
- Se fit gap for >= 12 pontos e passar nos gates, considerar remanejamento.
- Se o especialista estiver cheio, escolher o proximo melhor vendedor elegivel ou manter com apoio consultivo.

## Red-flag de vendedores

Red-flag nao significa excluir vendedor. Significa controlar exposicao a deals bons demais para serem desperdicados.

Tier 1 - baixa performance consolidada, nao receber demanda extra relevante:

| Vendedor | Manager | Win rate | Open deals | Open value | Observacao |
|---|---|---:|---:|---:|---|
| Lajuana Vencill | Dustin Brinkmann | 55,0% | 80 | US$ 116.039 | Conversao baixa consolidada |
| Markita Hansen | Celia Rouche | 57,3% | 79 | US$ 282.756 | Conversao baixa e carteira de alto valor |
| Gladys Colclough | Melvin Marxen | 58,2% | 85 | US$ 192.142 | Conversao baixa consolidada |

Tier 2 - controle forte / ultima tentativa assistida:

| Vendedor | Manager | Win rate | Open deals | Open value | Observacao |
|---|---|---:|---:|---:|---|
| Niesha Huffines | Melvin Marxen | 60,0% | 64 | US$ 107.745 | Abaixo do baseline global |
| Daniell Hammack | Rocco Neubert | 61,0% | 72 | US$ 209.320 | Alto valor com conversao moderada |
| Zane Levy | Summer Sewald | 61,7% | 88 | US$ 193.348 | Grande backlog envelhecido |

Tier 3 - nao e red-flag por conversao, mas nao deve receber mais carga:

| Vendedor | Manager | Win rate | Open deals | Open value | Motivo |
|---|---|---:|---:|---:|---|
| Darcel Schlecht | Melvin Marxen | 63,1% | 194 | US$ 656.040 | Carteira grande e stale |
| Kary Hendrixson | Summer Sewald | 62,4% | 103 | US$ 276.517 | Backlog velho |
| Vicki Laflamme | Celia Rouche | 63,7% | 104 | US$ 227.326 | Backlog velho |
| Cassey Cress | Rocco Neubert | 62,5% | 85 | US$ 220.860 | Backlog velho |

## Ultima tentativa

Ultima tentativa deve ser um programa controlado, nao um deposito de oportunidade ruim.

Regras:

- Dar poucos deals por ciclo: 5 a 8 por vendedor.
- Usar deals de risco moderado, nao os melhores deals estrategicos.
- Exigir fit minimo no produto ou ticket.
- Definir SLA curto: 7 a 14 dias para registrar acao, resposta ou proximo passo.
- Se nao houver movimento, retornar para nutricao/revisao gerente.
- Medir resultado separado do score principal para nao contaminar avaliacao do modelo.

## Racional final de roteamento

| Condicao | Saida |
|---|---|
| Bom score, bom fit atual, dados suficientes | Manter e priorizar |
| Bom score, fit atual fraco, especialista disponivel | Remanejar se passar nos gates |
| Bom score, fit atual fraco, especialista cheio | Consultar especialista / playbook |
| Alto valor, conta ausente | Corrigir dados / revisao gerente |
| Muito velho e baixo valor | Nutricao ou close-lost operacional |
| Muito velho e alto valor | Revisao gerente com ultima tentativa curta |
| Vendedor red-flag | Limitar novas atribuicoes; usar apenas ultima tentativa controlada |
| Vendedor sem historico | Fit neutro; baixa confianca; nao punir nem premiar forte |
