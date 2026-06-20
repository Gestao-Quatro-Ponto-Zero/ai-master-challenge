# Decisões & Verificações — Lead Scorer 003

## D1 — Quais features entram na probabilidade de fechamento
- **Contexto:** EDA mediu win-rate por dimensão. Só `sales_agent` tem spread relevante (55–70%, 15pp). Produto/setor/regional/manager/valor: <5pp (ruído).
- **Decisão:** probabilidade baseada **exclusivamente no win-rate histórico do vendedor (com smoothing bayesiano)**. Produto, setor, região e manager **descartados** — spread <5pp não justifica entrar no modelo.
- **Alternativas descartadas:** (a) pesar todas as features igualmente (o que a IA faria) → adiciona ruído; (b) ML (XGBoost) → ganho marginal sobre 63% base, sem explainability, e o brief diz "não precisa de ML perfeito".
- **Custo/trade-off:** modelo "simples" — mas defensável célula a célula e explicável ao vendedor. É o que o challenge premia.

## D2 — Fórmula de score (implementada)
- Score = **(1) probabilidade** (agent win-rate smoothed, peso 45%) + **(2) tamanho do deal** (percentil do `sales_price`, peso 35%) + **(3) urgência/aging** (curva sino ancorada no ciclo dos Won 57→88d — sobe até a janela ideal, satura e decai após; **não** usa o p90 dos abertos, que era viés de sobrevivência; só Engaging, peso 20%).
- Ao revisar o scoring, vi que o componente de valor usava `P × sales_price` — isso fazia P contar **duas vezes** no score (no componente de probabilidade E dentro do valor), contrariando os pesos declarados. Corrigido: valor = tamanho puro; `expected_value` continua calculado como métrica **informativa** (monetização de "R$ em risco" nas views Time/Saúde), fora do score.
- Pesos em `scoring/config.py` (const com assert de soma=1). Breakdown por deal (feature/peso/pontos/porquê) — o score é **derivado da soma das parcelas do breakdown** (invariante auditável por construção).
- Prospecting (sem engage_date): renormalizar pesos removendo o componente de aging.

## D5 — Camada de ação: event sourcing simples em SQLite
- **Contexto:** numa revisão da UX, notei que o app mostrava o que fazer mas o vendedor não conseguia **agir** dentro da ferramenta.
- **Decisão:** tabela `deal_actions` append-only (migration 0003); o estado do deal é a **última ação** (contacted/discarded/reactivated). Descartar é reversível, tudo auditável (quem, quando, nota). Brief e listas respeitam as ações; o seed não limpa a tabela (decisões sobrevivem ao re-seed dos dados do CRM).
- **Alternativas descartadas:** (a) write-back real ao CRM — fora do escopo do challenge (sem CRM real para integrar; declarado como roadmap); (b) estado em `st.session_state` — se perderia ao recarregar, sem auditoria.
- **Custo/trade-off:** ações são locais ao app (não sincronizam com o CRM de origem) — mas o export CSV "CRM-ready" cobre o caminho de volta.

## D4 — Limiar de deal "provavelmente morto" (is_stale)
- **Contexto:** deal de 355d aparecia como #1 do Foco do Dia ("cadáver" no topo mina a confiança). Primeiro limiar testado (p90 do ciclo Won = 106d) marcava **69% do pipeline** como stale — inútil como ferramenta.
- **Decisão (vigente):** `STALE_DAYS = WON_MAX_DAYS = 138d` — o deal Won mais velho de toda a história fechou em 138 dias; **nenhum** fechou além disso. Logo, `days_open > 138` é "além de qualquer fechamento real" por definição dos dados, não por chute. Resultado: **61,8% dos abertos (1291/2089)** caem em "Revisar/Descartar" — **reportado como insight de saúde** (pipeline genuinamente inflado com deals mortos), não escondido. Stale é rebaixado a "Baixa Prioridade" por construção (tier efetivo), então some do "Foco Agora".
- **Iteração anterior (descartada):** `3× mediana do ciclo Won (171d)`. Marcava menos deals, mas o `3×` é arbitrário — não tem âncora no outcome real. Trocado por `WON_MAX_DAYS` após auditoria: o limite defensável é "mais velho que qualquer Won", não um múltiplo escolhido a dedo.
- **Alternativa descartada:** limiar fixo arbitrário (90d, 120d) — indefensável; `WON_MAX_DAYS` é derivado direto do ciclo real dos fechados.

## D3 — Smoothing bayesiano (justificativa de dados)
- Células agente×produto: 178 células, 10% com n<10. Win-rate cru em célula pequena é instável.
- **Decisão:** win-rate suavizado = (wins + k·prior) / (n + k), prior = win-rate global (0,632), k≈5–10. Documentar k escolhido.

---

## Log de verificação numérica
| # | Claim | Como verifiquei | Resultado |
|---|-------|-----------------|-----------|
| V1 | "stage diferencia win-rate" | win-rate por stage | parcial: closed são só Won/Lost; abertos (Prospecting/Engaging) é o universo a scorar |
| V2 | "produto/setor diferenciam" | groupby win-rate | **FALSO** (<5pp) → descartados |
| V3 | "vendedor diferencia" | groupby win-rate, n>=30 | **VERDADEIRO** (55–70%, 15pp) |
| V4 | ciclo de venda | (close-engage) dos Won | mediana 57d, p75 88d |
| V5 | join produtos | set diff pipeline×catálogo | GTXPro órfão → corrigido |
| V6 | contas faltantes | isna account | 1.425 nulos = **68% dos abertos** (2.089); 16% do total. Todos concentrados nos abertos (Won/Lost têm conta 100%) |
| V7 | idade do deal (days_open) | inspeção do top-3 do score | **bug**: view usava `now` (2026) num dataset de 2017 → 3199d; corrigido p/ `MAX(close_date)` → 9–423d (mediana 165) |
| V8 | distribuição de tiers | value_counts do score | bruta por score: 169 Foco / 927 Trabalhar / 993 Baixa; efetiva (stale fora): 124 Foco / 348 Trabalhar / 326 Baixa (não joga tudo num bucket) |
| V9 | breakdown audita o score | soma dos pontos vs score | soma == score em todos os deals (explainability auditável) |
