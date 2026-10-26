# Briefing — Challenge 003 Lead Scorer

Insumo para o Bloco 1 (escopo). Este documento reúne o enunciado, os critérios do avaliador e os achados da exploração inicial (fase 0). Os números foram gerados pelos scripts em `process-log/scripts/`.

---

## 1. O problema, nas palavras da cliente
> "Nossos vendedores gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar. Preciso de algo funcional — não um modelo no Jupyter Notebook que ninguém vai usar. Quero uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar. Pode ser simples, mas precisa funcionar."
> — Head de Revenue Operations

**Duas dores distintas:**
1. **Tempo desperdiçado** em deals que não vão fechar → falta uma lista do que largar.
2. **Oportunidades boas esfriando** → falta um alerta de urgência.

A maioria das soluções vai atacar só a pergunta "qual deal tem mais chance". A dor real é de alocação de tempo.

## 2. Requisitos do enunciado → como vamos atender

| Requisito / critério do G4 | Como atendemos | Onde fica a evidência |
|---|---|---|
| Precisa **rodar** | Página estática que abre com duplo-clique e tem link público no GitHub Pages | README (setup) e link |
| Usa **dados reais** | Os 4 CSVs originais, limpos por script | `solution/data`, `DATA_QUALITY.md` |
| Lógica de scoring, **não só ordenar por valor** | Valor esperado = probabilidade condicionada à idade e ao estágio × valor, mais urgência | `SCORING.md` |
| Vendedor entende **por quê** | Explicação por deal em linguagem simples, com fatores que sobem e descem | Interface |
| Scoring faz sentido e **vai além do óbvio** | Mostra que os atributos não preveem e que o frescor prevê, com backtest temporal | `SCORING.md` (validação) |
| Interface **ajuda a decidir** | Quatro listas de ação (Foque, Reative, Limpe, Qualifique) | Interface |
| Código **limpo e mantível** | Motor separado da interface, funções puras, testes | `solution/scorer`, `tests` |
| Filtro vendedor/manager/região (bônus) | Filtros na interface e brief por vendedor | Interface, `briefs/` |
| Documentação: setup, lógica, limitações | README, `SCORING.md`, `MODEL_CARD.md` | `docs/` |
| Process log | Commits por bloco, log de decisões, exports de chat e "onde a IA errou" | `process-log/` |

## 3. Os dados

| Tabela | Linhas | Chave | Observação |
|---|---|---|---|
| sales_pipeline | 8.800 | opportunity_id | Tabela central |
| accounts | 85 | account | setor, receita, funcionários, país, empresa-mãe |
| products | 7 | product | série e preço de tabela |
| sales_teams | 35 | sales_agent | manager (6) e escritório (Central, East, West) |

**Estágios:** Won 4.238 · Lost 2.473 · Engaging 1.589 · Prospecting 500. Win rate dos fechados: **63,2%**.
**Período:** engajamentos de out/2016 a dez/2017; fechamentos de mar/2017 a 31/12/2017.

## 4. Problemas de qualidade encontrados

| Problema | Impacto | Tratamento sugerido |
|---|---|---|
| "GTXPro" no pipeline vs. "GTX Pro" no catálogo | O join perde **1.480 deals** (o produto inteiro) | Mapear nome → nome do catálogo |
| Setor "technolgy" | Cosmético, aparece na interface | Corrigir para "technology" |
| 1.425 deals sem `account` (1.088 Engaging, 337 Prospecting) | 68% dos abertos não têm atributos de conta | Mostrar "conta não informada" e não penalizar no score; virar alerta de higiene de CRM |
| Prospecting sem `engage_date` | Não dá para calcular frescor | Lista própria (Qualifique), ordenada por valor |
| 5 vendedores sem nenhum deal | Aparecem vazios nos filtros | Exibir com estado vazio ou excluir dos filtros (decidir) |
| Fechamentos de 2017-Q1 com win rate de 82% (vs. ~61% depois) | Provável recorte: o primeiro fechamento é em mar/2017 | Investigar no bloco 2; considerar excluir do treino |
| `close_value` dos Won varia de 66% a 134% do preço de tabela (média de 100%) | Pequeno | Usar o preço de tabela como valor do deal aberto |

## 5. O que (não) prevê vitória — deals fechados

- **Produto, setor, região, manager:** win rate entre 60% e 65%. Teste qui-quadrado para produto: p=0,37.
- **Vendedor:** de 55% a 70%, mas p=0,26, compatível com ruído para ~220 deals por pessoa. A correlação entre o primeiro e o segundo semestre é de 0,57, um sinal fraco e com amostra de apenas 30 pessoas.
- **Variáveis numéricas da conta** (receita, funcionários, ano de fundação) e o preço: AUC ≈ 0,50, sem poder de ordenação.
- **Ciclo do deal:** AUC 0,58. Os perdidos perdem rápido (mediana de 14 dias); os ganhos levam mais tempo (mediana de 57 dias). A distribuição dos perdidos é bimodal: 1.249 de 2.473 perderam em até 14 dias.

> Implicação: um score baseado em atributos produz um número quase igual para todos (perto de 63%). É exatamente o que o baseline deles deve entregar.

## 6. O sinal que funciona: frescor

**Teste de snapshot:** voltar a uma data passada, pegar os deals abertos naquele dia e olhar o que aconteceu com eles depois.

Corte em **30/09/2017** (desfecho observado até 31/12/2017):

| Idade do deal no corte | % ganhos depois | % ainda abertos no fim |
|---|---|---|
| até 30 dias | **50%** | 16% |
| 31–60 dias | 34% | 45% |
| 61–90 dias | 7% | 86% |
| 91–138 dias | **0%** | 99% |
| > 138 dias | **0%** | 100% |

O corte em 30/06/2017 mostra o mesmo padrão: 53% → 45% → 22% → 0%.

**Nenhum deal fechado teve ciclo acima de 138 dias**, em nenhuma coorte de engajamento.

## 7. O pipeline aberto hoje (31/12/2017)

| Faixa de idade (Engaging) | Deals | Leitura |
|---|---|---|
| até 90 dias | 110 | **Foque**: ainda vivos |
| 91–138 dias | 188 | **Reative**: janela fechando |
| > 138 dias | 1.291 (81%) | **Limpe**: zumbis, ~US$3,2 mi de US$3,9 mi em valor de tabela |
| Prospecting (sem data) | 500 | **Qualifique**: ~US$1,07 mi |

Concentração de receita ganha: GTX Pro 35%, GTX Plus Pro 26%, MG Advanced 22%, ou seja, **83% em 3 produtos**. MG Special tem o maior volume de deals e 0,4% da receita.

## 8. Ressalvas que precisam aparecer na entrega
- O dataset é sintético. O corte duro em 138 dias provavelmente é artefato do gerador. Em dados reais, a curva de decaimento seria suave. O score deve usar uma curva estimada, não um "if idade > 138".
- "Hoje" = 31/12/2017 por convenção, já que o dataset não tem data de extração.
- Como os desfechos dos deals ainda abertos são desconhecidos (dados censurados), um deal parado pode estar com o CRM desatualizado, não necessariamente morto. Por isso a lista se chama "Limpe" (confirmar e encerrar), não "Descarte".

## 9. Perguntas em aberto para o Bloco 1
1. As 4 listas fazem sentido, ou o vendedor precisa de uma lista única priorizada com etiquetas?
2. A tela padrão é a visão do vendedor ou a do manager?
3. O que vale mais no "Foque": maior valor esperado, ou menor idade com valor alto?
4. Vamos incluir o "modo backtest" na interface (escolher uma data passada e ver o que o score recomendaria e o que aconteceu de fato)? É o diferencial mais forte, a um custo de cerca de 30 minutos.
