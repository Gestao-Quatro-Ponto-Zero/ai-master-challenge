# F11 — Report (Console refeito do zero)

Caminhos relativos à submissão (`ai-master-challenge/submissions/gustavo-covaleski/`).

**Commit:** `879ba98ad07e9a0c44bd037ad0299774ddd286da`, "F11: console refeito do zero — 4 telas guiadas, sistema de design, robustez como cenários". Sem push.

## 1. O que foi feito

1. **Passo 0, antes de qualquer código:**
   - rodei `/ui-ux-pro-max:ui-ux-pro-max` com o contexto da spec: `--design-system` com dials de variação 4, movimento 3 e densidade 6, mais buscas de tipografia e de gráfico;
   - rodei `/frontend-design` (direção estética e composição);
   - gravei `console/DESIGN.md` (31 linhas).
2. **Fontes:** Fira Sans (400/500/600) e Source Serif 4 (600), baixadas uma vez em woff2 para `console/fonts/` (licença OFL). `fonts/fontes.css` traz as mesmas woff2 em base64 (ver §4). Em tempo de execução, não há CDN.
3. **`index.html`, `styles.css` e `app.js` refeitos do zero:** 4 telas com navegação lateral (barra inferior no celular), roteamento por `#hash`, painel lateral na Governança e 5 cenários com botão na Robustez.
4. **Não mudaram:** `data.js` e `f10_console_dados.py` (conferido com `git diff --quiet`). Os testes da F10 continuam passando.
5. **Verificação no Playwright:** `file://` e `http.server` a 1440 × 900, 1024 × 768 e 390 × 844, passando pelas 4 telas, pelo painel e pelos cenários.
6. **Screenshots:** 6 telas + `antes_depois.png`; `c1`–`c4` removidos com `git rm`.
7. **Documentos:** README e process log atualizados (linha 14 e o erro da F10-spec).

## 2. Resultados

| Item | Valor | Origem |
|---|---|---|
| Tela 1, IA decide | **13,37%** | `data.js` → `governanca[19].faixas.F9` (lido na tela pelo Playwright) |
| Tela 1, precisão | **98,75%** (meta 96,8%, selo "acima da meta") | idem |
| Tela 1, trabalho evitado | **1.279 de 9.567** | idem |
| Frase gerada para Hardware no painel | "Hardware: 95,4% de precisão, mas o limite inferior (94,3%) não alcança a meta de sugestão (95,5%). Continua com humano." | `data.js` (dia 20) |
| Erros de JS e de console (6 combinações) | 0 (o 404 do favicon no `http.server` foi ignorado) | Playwright |
| Rolagem horizontal (4 telas × 3 larguras × 2 protocolos) | nenhuma | Playwright |
| Fontes carregadas por `file://` e `http` | sim (`document.fonts.check`) | Playwright |
| Testes | **76 passed** | `pytest solution/tests -q` |
| `f1_splits.csv` | SHA-256 `37703450…865ba0` (inalterado) | — |

### Teste de 5 segundos (Tela 1, 1440 × 900)

O que fica acima da dobra, de cima para baixo:
- o título-pergunta "O piloto está saudável?" em serifa e um subtítulo de 2 linhas;
- o bloco navy **"Comece aqui"**, com 3 botões brancos numerados ("1. Veja um ticket ser triado", "2. Veja por que a IA não decide tudo", "3. Tente quebrar o sistema") e "Dispensar";
- a faixa de alerta (Internal Project, com o link "ver");
- os 3 indicadores grandes;
- o início dos cartões "Para onde vai cada ticket?" e "Quais filas já estão automatizadas?".

O primeiro elemento clicável e dominante é o "Comece aqui". Na ordem do teclado, vêm antes só o link "Pular para o conteúdo" e a navegação lateral.

### Checklist de paridade (tela e caminho; no máximo 2 cliques a partir da Tela 1)

| Função da F10 | Onde está agora | Caminho |
|---|---|---|
| Fila com filtro | Fila | Nav "Fila" → controle segmentado (1 clique) |
| Confirmar e corrigir com teclado | Fila | Nav "Fila" → foco na lista: ↑/↓, Enter, 1–8 (1 clique) |
| "Por que" da decisão | Fila | Nav "Fila" → "Por que esta decisão" (2 cliques) |
| Duas mais prováveis e termos | Fila, dentro do "por que" | idem (2 cliques) |
| Governança com IC e metas | Governança | Nav "Governança" (1 clique) |
| Evolução por dia | Governança, painel lateral | chip da fila na Tela 1 (1 clique) ou Nav → linha da tabela (2) |
| Dia do piloto | Governança, painel lateral | idem (1–2 cliques); o estado vale para todas as telas |
| Modo sombra | Robustez, cenário 4 | Nav "Robustez" → chave (2 cliques) |
| Seletor de política | Robustez, cenário 5 | Nav "Robustez" → F9/F8/F4 (2 cliques); vale para todas as telas |
| Os 5 ataques | Robustez, cenário 1 | Nav "Robustez" → seletor de ataque → "Rodar ataque" (2–3 cliques; o padrão já é o ticket 10244 com "categoria repetida", então "Rodar" é o 2º clique) |
| Duplicado | Robustez, cenário 2 | Nav "Robustez" → "Reentregar o evento" (2 cliques) |
| Reembolso | Robustez, cenário 3 | Nav "Robustez" → "Marcar como reembolso" (2 cliques) |
| Alertas | Tela 1, faixa de alerta | visível ao abrir; "ver" leva ao painel (1 clique) |
| Log | Robustez, fim da tela | Nav "Robustez" → "Log da tela" (2 cliques) |
| Premissas de custo editáveis | Tela 1, indicador "Trabalho humano evitado" | "Ver economia e premissas" (1 clique) |
| Aviso de simulação | Fila (nota no cartão) e rodapé de todas as telas | visível |
| Rodapé de fontes | todas as telas | visível |

## 3. O que contraria a hipótese ou a expectativa

- **A sugestão de fontes da skill não serviu ao brief.** O `--design-system` devolveu EB Garamond + Lato ("legal, formal"), um tom de escritório de advocacia. Mantive a ideia de uma serifa de autoridade só nos títulos-pergunta, trocando por Source Serif 4, mais legível em tela, e usei Fira Sans, que a própria skill recomenda para dashboards de dados. A troca está registrada em `DESIGN.md`.
- **Fontes por `file://`:** o Chrome bloqueia `@font-face` por `file://` (CORS), o que quebraria o "abre com duplo clique". Ver §4.

## 4. Desvios da spec

- **`fonts/fontes.css` com as woff2 em base64** (126 KB), gerado dos próprios arquivos de `fonts/`. É a única forma de as fontes carregarem com duplo clique. As woff2 continuam em `fonts/` como fonte e licença. Sem CDN.
- **Política e modo sombra são estado global:** são trocados na Robustez e refletem nas outras telas. A navegação mostra o estado ("F9 implantada · modo ativo · dia 20 de 20"). A spec só pedia que estivessem na Tela 4.
- **"Os 5 ataques":** com o ticket padrão, o 1º ataque já sai em 2 cliques; os outros 4 precisam de 3 (escolher o ataque e rodar).
- **Barra de faixas e indicadores:** respeitam o modo sombra (tudo em humano). Isso é intencional, para que o efeito da chave apareça na Tela 1.
- **Sem biblioteca de gráfico:** todos os gráficos são SVG próprio.

## 5. Erros e correções durante a execução

1. A 1ª verificação mostrou o erro de CORS das fontes por `file://` (o `preload` e o `@font-face`). Corrigi com `fontes.css` em base64 e removi o `preload`.
2. Havia rolagem horizontal na Robustez (1024 e 390 px) e na Governança (390 px), por causa das linhas de log longas e da largura mínima da barra de IC. Corrigi com `word-break` no log, uma tabela com rolagem dentro do cartão e largura mínima menor no celular.
3. O script de screenshots falhou no `antes_depois.png` (`require` indisponível no Playwright). Refiz com uma página HTML temporária no scratchpad, aberta por `file://`.
4. Removi do `app.js` uma linha redundante no `irPara` (atributo `aria-current` aplicado duas vezes).

## 6. Pendências e decisões que dependem do Gustavo

1. **Redeploy:** na pasta `console`, rode `npx vercel --prod` para publicar a versão nova em https://console-piloto-triagem.vercel.app.
2. "Decisão minha" da F11 no process log.
3. Push e PR.

## 7. Tempo gasto × orçado

Orçado: 75 min (teto 90). Relógio: 14:03 → ~14:12, cerca de 10 min de execução.
