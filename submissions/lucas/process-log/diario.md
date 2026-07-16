# Diário de processo — Lead Scorer

## Fase 1 — Auditoria dos dados

**O que a auditoria revelou** (detalhe técnico em 01_exploration_summary.md):
mismatch de grafia GTXPro/GTX Pro (1480 deals), 1425 contas nulas só em deals
abertos, win rate global 63%, e Won demora mais que Lost (57 vs 14 dias).

**Minhas decisões:**

1. Mismatch GTXPro → GTX Pro: normalizar em memória antes do join, sem
   sobrescrever o CSV original. Sem isso, 1480 deals ficariam órfãos no preço
   e o valor potencial sairia errado.

2. Vendedor NÃO entra no scorer individual. Claude apontou vendedor como maior
   preditor (55–70%) — é real, mas inerte na visão de um vendedor: dentro do
   pipeline dele o vendedor é constante, não muda ranking nenhum. Movi essa
   feature pra visão do manager. Scorer individual = produto + valor + idade.

3. "Esfriando" não é tempo parado absoluto. Won leva mais tempo que Lost, então
   parado ≠ ruim. Vou relativizar ao ciclo de vitória do produto (só alerta
   acima do típico de um deal vencedor).

4. Conta nula em ~2/3 dos deals abertos → não posso apoiar o scorer em
   setor/tamanho. Features-espinha = produto + valor + idade; conta entra só
   como bônus quando existe, com fallback global quando não.

## Fase 2 — Disponibilidade de features + desenho do modelo

**O que os dados forçaram:**

- Firmografia (setor/receita/funcionários) só existe em 31,8% dos deals
  abertos. A base "natural" de scoring falharia em 2/3 do pipeline. Decisão:
  inverti a prioridade — espinha = produto + valor + estágio + idade (100%
  disponíveis); conta entra só como ajuste, com fallback global.

- Descobri que deal_stage é estado único (Won não guarda que passou por
  Engaging). Logo, NÃO dá pra tirar win rate de estágio empiricamente.
  Decisão: P(fechar) sai de produto (+ setor quando existe); estágio entra
  como prior heurístico documentado, não como taxa empírica. Vou deixar
  explícito no código o que é empírico vs heurístico.

- "Esfriando" ≠ tempo parado absoluto (Won leva 57d, Lost 14d). Só marco como
  frio quando passa do ciclo típico de um deal VENCEDOR daquele produto
  (percentil alto). Antes disso, tempo aberto é normal.

**Decisão de produto (não-técnica):**

- Ferramenta = matriz 2×2 (Valor Esperado × esfriando), não um ranking cru.
  Mapeia direto as 2 dores da Head de RevOps: "perde tempo em deal ruim" e
  "deixa deal bom esfriar". Ranking sozinho não diz o que FAZER.

**Limitação que assumo de propósito:**

- Produto é preditor fraco (win rate 55–70%), então o lift do P(fechar) vai ser
  modesto. A força vem do Valor Esperado + da matriz, não de previsão mágica.
  Vou provar o lift real no backtest, sem inflar.

## Fase 3 — Scoring: validação expôs 3 coisas que decidi tratar

**Realização central:** win rate é quase plano (produto 60–65%, setor ±1,9pp).
Probabilidade quase não separa deal. Decisão de narrativa: a ferramenta NÃO é
preditiva — é priorizador por valor em jogo + detector de abandono, com
contexto. Vou provar o lift real (modesto) no backtest em vez de fingir modelo.

1. Flag "esfriando" pegava 93% dos Engaging. Não é erro de cálculo — é viés de
   censura temporal (retrato estático: quem segue aberto é quem demorou). Um
   flag verdadeiro pra 93% não prioriza. Troquei de limiar ABSOLUTO (vs ciclo
   de vitória) para RELATIVO (top 25% mais velhos entre os abertos do mesmo
   produto). A definição absoluta fica documentada como a de um CRM ao vivo.

2. GTK 500 (n=25, preço 5x) dominava o EV. Não suprimi — deal caro merece foco.
   Adicionei INDICADOR DE CONFIANÇA por deal (produto n + conta presente) pro
   vendedor saber quando o score se apoia em dado fino.

3. Ajuste por setor move <2pp e só existe em 1/3 dos deals. Mantive por ser
   barato e explicável, mas assumo: o modelo se apoia em produto + valor.

## Fase 4 — Backtest: a prova que redefiniu a ferramenta

**Resultado, sem maquiagem:** AUC 0,485 (produto+setor não discrimina quem
fecha). EV captura 46,8% do valor no top-20% — mas "ordenar por preço puro"
captura 47,9%. Rankings 98,5% correlacionados. O componente empírico NÃO
supera simplesmente perseguir o deal mais caro.

**O que decidi com isso (não escondi, reposicionei):**
- A tese "EV refina a priorização por probabilidade" está morta neste
  dataset — e provei isso em vez de assumir. Reporto o 0,98x como é.
- Mas o valor da ferramenta nunca foi prever fechamento. É: (1) visibilidade
  + explicabilidade sobre pipeline priorizado no feeling; (2) estágio
  (engajado > prospect); (3) flag de deal de alto valor sendo negligenciado.
  Nenhuma dessas é backtestável no universo fechado — mas são o que muda a
  ação olhando pra frente.
- Reposicionei o app: de "score preditivo" para "organizador de ação"
  (matriz Valor × Abandono + corte por estágio). Abraço o achado em vez de
  fingir um lift que não existe.

**Crédito à IA (honestidade):** o agente pegou sozinho que usar deal_stage
como baseline seria vazamento (estágio = rótulo no universo fechado) e
flagrou a inversão no decil de topo. Bons calls, não fui eu.

**Limitação que fica:** o backtest só valida o ramo "com conta" (100% dos
fechados têm conta); o fallback "só produto" (~68% do pipeline aberto) fica
sem validação empírica possível neste dataset.

## Fase 5 — App: decisão de "esfriando" relativo ao filtro
- Na visão individual, "esfriando" no nível da empresa zerava a coluna pra
  vendedores cujos deals não estão entre os mais velhos globais — escondia
  justo a pergunta "quais dos MEUS deals estou deixando esfriar". Tornei o
  "esfriando" relativo ao filtro ativo; mantive "alto valor" fixo na empresa
  (um deal caro é caro independente de quem o trabalha). Prioriza o uso real
  sobre a pureza estatística — a ferramenta é pro vendedor, não pro analista.
