# Diário de processo — Lead Scorer

## Fase 1 — Auditoria dos dados

**O que a auditoria revelou** (detalhe técnico em 01_exploration_summary.md):
mismatch de grafia GTXPro/GTX Pro (1480 deals), 1425 contas nulas só em
deals abertos, win rate global 63%, e Won demora mais que Lost (57 vs 14 dias).

**Minhas decisões:**

1. Mismatch GTXPro → GTX Pro: normalizar em memória antes do join, sem
   sobrescrever o CSV original. Sem isso, 1480 deals ficariam órfãos no
   preço e o valor potencial sairia errado.

2. Vendedor NÃO entra no scorer individual. Claude apontou vendedor como
   maior preditor (55–70%) — é real, mas inerte na visão de um vendedor:
   dentro do pipeline dele o vendedor é constante, não muda ranking nenhum.
   Movi essa feature pra visão do manager. Scorer individual = produto +
   valor + idade do deal.

3. "Esfriando" não é tempo parado absoluto. Won leva mais tempo que Lost,
   então parado ≠ ruim. Vou relativizar ao ciclo de vitória do produto
   (só alerta acima do típico de um deal vencedor).

4. Conta nula em ~2/3 dos deals abertos → não posso apoiar o scorer em
   setor/tamanho. Features-espinha = produto + valor + idade; conta entra
   só como bônus quando existe, com fallback global quando não.

## Fase 2 — Disponibilidade de features + desenho do modelo

**O que os dados forçaram:**
- Firmografia (setor/receita/funcionários) só existe em 31,8% dos deals
  abertos. A base "natural" de scoring falharia em 2/3 do pipeline.
  Decisão: inverti a prioridade — espinha = produto + valor + estágio +
  idade (100% disponíveis); conta entra só como ajuste, com fallback global.

- Descobri que deal_stage é estado único (Won não guarda que passou por
  Engaging). Logo, NÃO dá pra tirar win rate de estágio empiricamente.
  Decisão: P(fechar) sai de produto (+ setor quando existe); estágio entra
  como prior heurístico documentado, não como taxa empírica. Vou deixar
  explícito no código o que é empírico vs heurístico.

- "Esfriando" ≠ tempo parado absoluto (Won leva 57d, Lost 14d). Só marco
  como frio quando passa do ciclo típico de um deal VENCEDOR daquele
  produto (percentil alto). Antes disso, tempo aberto é normal.

**Decisão de produto (não-técnica):**
- Ferramenta = matriz 2×2 (Valor Esperado × esfriando), não um ranking cru.
  Mapeia direto as 2 dores da Head de RevOps: "perde tempo em deal ruim"
  e "deixa deal bom esfriar". Ranking sozinho não diz o que FAZER.

**Limitação que assumo de propósito:**
- Produto é preditor fraco (win rate 55–70%), então o lift do P(fechar)
  vai ser modesto. A força vem do Valor Esperado + da matriz, não de
  previsão mágica. Vou provar o lift real no backtest, sem inflar.

  