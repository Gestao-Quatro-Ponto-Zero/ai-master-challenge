# F12 — Report (Console reimplementado a partir das pranchas aprovadas)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`).

**Commit:** `5bbd9f46a3a1898a05223a59b083615f8da15c08`, "F12: console reimplementado a partir das pranchas aprovadas; responsivo e copy técnica". Sem push.

## 1. O que foi feito

1. **Pranchas:** li as 7 pranchas de `planning/F12-design/` (estilos inline, copy e `renderVals()`). Nenhuma marcação foi copiada.
2. **`/frontend-design`:** usado só para revisar a implementação (especificidade de CSS, `min-width: 0`, foco, `prefers-reduced-motion`), sem propor outro design.
3. **Fontes:** IBM Plex Sans 400/500/600/700 e Mono 400/500 auto-hospedadas em `console/fonts/` + `fontes.css` em base64 para `file://`. Fira Sans e Source Serif 4 removidas com `git rm`.
4. **`index.html`, `styles.css` e `app.js` reescritos:**
   - rotas `#visao`, `#fila`, `#fila/<id>`, `#governanca`, `#governanca/<categoria>`, `#robustez` e `#robustez/<cenario>`;
   - estado global: modo, política, dia e premissas;
   - painel "Sobre os dados";
   - 3 layouts: desktop, tablet e celular (barra inferior, lista → ticket com barra de ação fixa, Governança em cartões com painel em tela cheia, seletor de cenário).
5. **`console/DESIGN.md`** reescrito com o sistema das pranchas (origem: Claude Design, aprovado pelo Gustavo).
6. **Teste de corte** (`planning/F12-testes/teste_corte.js`, Playwright): 7 larguras × 2 protocolos × 11 rotas. Resultado em `planning/F12-cortes.json`.
7. **Screenshots:** d1–d4, t1, m1–m3 e `antes_depois.png`. `v1`–`v6` removidos com `git rm`.
8. **Documentos:** README e process log atualizados (linha 15, "O que a IA sugeriu" e o erro da F11). `data.js` e o gerador não mudaram (`git diff --quiet`).

## 2. Resultados

### Teste de corte (critério de aceite: zero)

| Largura | `file://` | `http.server` |
|---|---|---|
| 1440 × 900 | 0 | 0 |
| 1280 × 800 | 0 | 0 |
| 1024 × 768 | 0 | 0 |
| 820 × 1180 | 0 | 0 |
| 768 × 1024 | 0 | 0 |
| 390 × 844 | 0 | 0 |
| 360 × 740 | 0 | 0 |

- Rotas testadas em cada largura: `#visao`, `#fila`, `#fila/21676`, `#governanca`, `#governanca/Hardware`, `#robustez` e os 4 cenários, mais o painel "Sobre os dados".
- Alvos de toque abaixo de 44 × 44 px (< 768 px): **0**.
- Erros de JavaScript: **0** (o 404 do favicon no `http.server` é filtrado).
- Fonte: `planning/F12-cortes.json`.

### Números (Visão geral, lidos da tela pelo Playwright)

| Indicador | Na tela | Valor exato (`data-exato`) | `data.js` |
|---|---|---|---|
| Automação | 13,4% | 13,37% | `governanca[19].faixas.F9["IA decide"].n` / `n_total` |
| Precisão da automação | 98,7% (IC 95% 98,0–99,2%) | 98,75% | `acertos` / `n` da faixa IA decide |
| Sugestão com revisão | 32,1% (3.073 tickets, precisão 96,2%) | 32,12% | faixa IA sugere |
| Injeções sem revisão | 0 | 0 de 6.395 | `kpis.dano_injecao.F9` |
| Gráfico, dia 20 | 98,7% | 98,75% | idem |

Todos batem com os valores das pranchas.

**Outros resultados:**
- **Copy:** nenhum "F9/F8/F4" nem "?" nas telas, fora do painel "Sobre os dados" (verificação por script em `#visao`, `#fila`, `#governanca`, `#robustez` e `#robustez/politica`).
- **`pytest`:** 76 passed.
- **`f1_splits.csv`:** mesmo hash (`37703450…865ba0`).

### Checklist de paridade (F11 → F12)

| Função | Onde fica na F12 | Caminho a partir da Visão geral |
|---|---|---|
| Fila com filtro | Fila | aba ou "Abrir a fila" → controle segmentado com contagens (1 clique) |
| Busca | Fila | campo "Buscar por #id ou termo" (1 clique) |
| Confirmar e corrigir com teclado | Fila | Enter confirma, 1–8 corrige, ↑/↓ navega; no celular, barra de ação fixa |
| Motivo da decisão | Fila, "Motivo da faixa" | visível no ticket (1 clique) |
| 2ª opção e termos | Fila, "Detalhes do modelo" | 2 cliques |
| Governança com IC e metas | Governança | aba (1 clique) |
| Evolução por dia | painel da categoria | "Revisar fila" no alerta (1 clique) ou aba → linha (2) |
| Dia do piloto | painel da categoria | idem; vale para todas as telas |
| Modo sombra | Robustez → Modo sombra | 2 cliques |
| Seletor de política | Robustez → Troca de política | 2 cliques |
| 5 ataques | Robustez → Injeção (padrão) → seletor → Executar | 1 clique para o padrão; 3 para outro ataque |
| Duplicado | Robustez → Evento duplicado → Reentregar evento | 3 cliques |
| Reembolso | Robustez → Regra de reembolso → Marcar como reembolso (ticket 22129) | 3 cliques |
| Alertas | Visão geral, faixa de alerta | visível ao abrir |
| Log | Robustez, "Log da sessão" (recolhido) | 2 cliques |
| Premissas de custo | painel "Sobre os dados" (botão i) | 1 clique |
| Aviso de simulação | "Detalhes do modelo" ("correção simulada"), painel "Sobre os dados" e linha de fonte da Visão geral | visível ou 1 clique |
| Rodapé de fontes | linha única na Visão geral, como na prancha | visível |

Duplicado e reembolso passaram de 2 para 3 cliques, porque o cenário agora é escolhido num menu antes do botão. É o arranjo da prancha `Robustez.dc.html`.

## 3. O que contraria a hipótese ou a expectativa

- **O teste de corte acusou falhas que um teste de rolagem não acusaria:**
  - o `label` escondido para leitor de tela (recortado de propósito);
  - o rótulo "100%" no topo dos gráficos SVG: primeiro a 1024/820/768 px e, depois de aumentar a fonte no celular para seguir a prancha `MobileVisao`, de novo a 390/360 px.

  São 4 rodadas registradas em `F12-cortes.json`; a final dá 0.
- **Número com 1 casa:** 98,75% aparece como "98,7%", e não "98,8%", porque o valor exato é 1.263/1.279 = 0,98749…; o arredondamento é do `Intl` sobre esse valor. Bate com a prancha.

## 4. Desvios da spec

- **Ação "Rebaixar" × "Revisar"** (a prancha só mostra "Revisar"): quando a regra fica abaixo da política vigente, uma fila em IA decide recebe "Rebaixar", porque não há revisão humana, e uma fila em IA sugere recebe "Revisar", porque o humano já confere. "Promover" quando a regra fica acima; "Manter" quando é igual.
- **Copy em estados que as pranchas não cobrem**, seguindo as regras da spec:
  - selos grandes "IA decide · sem revisão" e "Humano decide · triagem manual";
  - vereditos "Elegível para decisão" e "Elegível para sugestão";
  - textos dos cenários duplicado, reembolso, sombra e política;
  - alertas de modo sombra, injeção e duplicado.
- **Ticket no celular:** o id aparece só no cabeçalho, como na prancha `MobileTicket`, e o selo fica à esquerda da data.
- **Screenshots de celular:** feitos com o viewport na altura total da página, para que a barra inferior fixa apareça no rodapé e não no meio, como acontecia na captura de página inteira.
- **Texto de ticket nos screenshots:** `d2` e `m2` mostram o ticket 21676, que está na fila do `data.js` (exceção de texto já aprovada) e é o mesmo das pranchas.
- **Gráfico "Precisão da automação por dia":** o eixo y é 96–100% (como na prancha), mas desce automaticamente se a política escolhida tiver um ponto abaixo de 96%.

## 5. Erros e correções durante a execução

1. O Playwright não lia o script de teste no scratchpad (fora das raízes permitidas). Movi para `planning/F12-testes/`.
2. 1ª rodada do teste de corte: 30 violações (label escondido; "100%" cortado no SVG). Corrigi com `aria-label` e `viewBox` com margem.
3. A barra inferior fixa aparecia no meio das capturas de página inteira. Refiz com o viewport na altura da página.
4. 3ª rodada: 12 violações, depois de aumentar a fonte dos gráficos no celular. Corrigi com mais margem no `viewBox`.

## 6. Pendências e decisões que dependem do Gustavo

1. **Redeploy:** `npx vercel --prod` na pasta `console`.
2. **Regra de ação "Rebaixar" × "Revisar"** (§4): aprovar ou ajustar.
3. "Decisão minha" da F12 no process log.
4. Push e PR.

## 7. Tempo gasto × orçado

Orçado: 90 min (teto 108). Relógio: 14:42 → ~14:58, cerca de 16 min.

## F12b — Fechamento

**Commit:** `fa025efa77e5403e43824731d51e701830d93986`, "F12b: governança em cartões até 900 px, legenda das metas, decisão sobre Rebaixar/Revisar". Sem push.

1. **Pedido:** revisão do chat do Projeto no console publicado (0 cortes a 1440, 768 e 390 px) com 2 ajustes.
2. **Governança em cartões até 900 px** (antes, até 767 px): a coluna Ação nunca exige rolagem horizontal.
3. **Legenda das metas** acima da lista de cartões: tracejado laranja "95,5% sugere" e tracejado verde "96,8% decide". No layout de tabela (> 900 px), a legenda fica oculta.
4. **Teste de corte completo:** 7 larguras × 2 protocolos × 11 rotas, com 0 violações, 0 alvos < 44 px e 0 erros de JS.
5. **Checagem da Governança** em 901, 900, 820, 768, 390 e 360 px (`file://` e `http`):
   - 0 elementos em rolagem horizontal;
   - cartões ativos até 900 px;
   - coluna Ação visível em todas as larguras.

   Registro em `F12-cortes.json` (bloco `f12b`).
6. **Screenshot `m3_governanca.png`** refeito com a legenda.
7. **Process log:** "Decisão minha" da F12 preenchida com o texto do Gustavo (regra Rebaixar × Revisar aprovada) e revisão do console registrada.
8. **`pytest`:** 76 passed. `f1_splits.csv` mantém o mesmo hash; `data.js` e o gerador não mudaram.
9. **Tempo:**
   - relógio da F12/F12b de 14:19 a 15:09 (~50 min, inclui revisão), contra um orçamento de 90 min;
   - os ~16 min da §7 são só a execução da F12.
10. **Pendência:** redeploy na Vercel (Gustavo).
