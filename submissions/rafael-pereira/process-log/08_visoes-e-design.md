# 08 — Visões por perfil e design

**Executor:** Claude Sonnet (subagente executor), a pedido do Rafael. **Data:** 26/10/2026. **Especificação:** `kit-lead-scorer/PROMPT_VISOES_E_DESIGN.md`, com as adaptações do orquestrador (sem git, sem Node, sem Postgres/Docker, fontes e axe já baixados). O orquestrador faz os commits, o push, a conferência do Pages e o comentário no PR.

Não toquei no motor (`scorer/`), no `build.py` nem nos testes do pytest. O `data.js` saiu byte a byte igual depois do build (mesmo hash antes e depois). Tudo o que as visões novas mostram (mapa do time, pauta, progresso, simulador) é derivado dos `deals` do `data.js` no navegador.

## O que foi entregue

| Parte | O que ficou |
|---|---|
| 1. Visões | Tela de entrada "Quem é você?"; visão do vendedor ("Minha semana"); visão do manager ("Meu time"); terceiro destino "Visão completa (RevOps e avaliação)" com a tela antiga e todos os filtros (desvio, ver DECISIONS) |
| 2. Arquitetura | `docs/ARQUITETURA_PRODUCAO.md` já existia (escrito por outro executor, SQL marcado "não executado — validar"); só ajustei uma frase. Acrescentei as linhas no DECISIONS, a limitação de acesso e dois riscos no MODEL_CARD e as limitações no README |
| 3. Design | `docs/DESIGN.md` escrito antes do CSS; `style.css` com tokens; fontes auto-hospedadas; tema claro e escuro com botão; loop visual de 3 rodadas; `tools/check_views.py` com axe-core |

Links diretos (README): `#perfil=vendedor&nome=Rosalina+Dieter` e `#perfil=manager&nome=Celia+Rouche`. Conferi no `data.js`: Celia Rouche é manager (região West, 6 vendedores) e Rosalina Dieter é vendedora do time dela (2 em Foque, 4 em Reative, 44 em Limpe).

## Ferramentas que não estavam disponíveis (registrado)

- **Skill `frontend-design`:** indisponível nesta sessão.
- **Figma:** não havia link de arquivo do Rafael no `docs/DESIGN.md`. Figma: referências usadas só como inspiração, arquivo não lido.
- **Lighthouse:** não executado (sem Node). Em seu lugar, axe-core 4.9.1 (`axe.min.js`, MPL-2.0, em `solution/tools/vendor/`) injetado pelo Playwright em Python.
- **Postgres e Docker:** não havia; o SQL da arquitetura de produção continua "não executado — validar".

## Loop visual (3 rodadas, matriz enxuta)

Matriz de cada rodada: 2 perfis x {entrada, aba principal, terceira tela} x {390, 1280} x {claro, escuro} = 24 PNGs, em `process-log/screenshots/design-r1/`, `design-r2/` e `design-r3/` (gerados por `solution/tools/design_shots.py`). A terceira tela do vendedor é o card aberto com ação e simulador; a do manager é a pauta do 1:1. Antes de cada rodada eu abri os PNGs e critiquei contra o checklist (hierarquia em 3 segundos, ação principal, dourado só para ação ou marca, status sem depender da cor, nada cortado, contraste, estados vazios, tokens, "premium e sóbria, não template").

**Referência "antes"** (a tela anterior, já com a correção da curva): `screenshots/depois-correcao-rosalina-1280.png` e `-390.png`. Era uma única tela com seletor "Quem é você?" no meio de filtros, paleta cinza e azul, fonte do sistema, sem tema escuro e sem ações por deal. (Os `final_*` antigos foram regravados por `check_app.py --prefix final`, como o README exige; não servem de "antes".)

### Rodada 1 — primeira versão renderizada

Visto: a estrutura funcionou na primeira passada (sem erro de console, tokens aplicados, tema escuro coerente). O status vem com ícone, cor e rótulo nos cards, abas e mapa.

| Problema visto | Tela | Correção na rodada 2 |
|---|---|---|
| Identidade repetida: nome do vendedor na barra de perfil e de novo no bloco de resumo | vendedor e manager, 390 e 1280 | Rótulo de escopo escondido fora da visão completa |
| Cabeçalho do celular estourava em três linhas, e o bloco de resumo ocupava a primeira tela inteira, com as abas fora da dobra | vendedor 390 | Botão do cabeçalho vira "Como funciona" no celular; progresso e valor da semana lado a lado; textos de apoio escondidos no celular (o do simulador aparece quando ligado) |
| Barra de perfil quebrava o botão "Trocar de perfil" para baixo | 390 | Barra em uma linha, nome em cima e time embaixo |
| Botão "Pauta do 1:1" quebrado em três linhas ("Paut / a do / 1:1") | manager 1280 | `white-space: nowrap` e `overflow-wrap: normal` nas células de ação |
| Zeros com "sem deals" repetido em toda célula | manager | Traço no lugar |
| Manager sem dica do que fazer a seguir | manager | Linha de apoio no bloco de resumo: clicar no vendedor abre a carteira e a pauta |

### Rodada 2

Visto: o celular do vendedor ficou legível (abas na primeira tela); sobrou texto duplicado e desalinhamento.

| Problema visto | Correção na rodada 3 |
|---|---|
| No cabeçalho do celular o botão de tema caía numa segunda linha (faltavam poucos pixels) | Espaço entre itens de 16 para 8px e menos padding lateral nos botões do cabeçalho |
| O texto "Clique no nome..." aparecia no bloco de resumo e de novo no título do mapa | Título do mapa só diz o que a tabela contém |
| Nome do vendedor quebrando em duas linhas na coluna do mapa; rótulo "1:1" solto nos cartões do celular | Largura mínima da coluna do nome; rótulo da coluna de ação removido no celular |
| "Como funciona  o score" com espaço duplo no botão | Texto dentro de um único elemento |

### Rodada 3 e verificação final

Visto: o cabeçalho do celular, os cartões do mapa e a pauta ficaram corretos nos dois temas, mas **a rodada 3 mostrou um defeito grave no desktop do manager**, e o conjunto final mostrou um segundo, causado pela correção do primeiro. Como o limite é de 3 rodadas, não abri uma 4ª matriz: corrigi e conferi nos PNGs finais e nos testes.

| Problema visto | Correção |
|---|---|
| Mapa do manager em 1280 (rodada 3): a tabela rolava na horizontal por dentro e cortava o botão "Pauta do 1:1" (o teste de layout só olhava a rolagem da página, não a da tabela) | Padding menor nas células e colunas mais estreitas; `check_views.py` passou a medir a rolagem interna do mapa (0 px agora) |
| Conjunto final, mapa no celular: a primeira linha de cada cartão ficou recuada (a regra nova de padding da primeira coluna vencia a regra do celular) | Regra do celular com a mesma especificidade; conferido em `final-manager-390.png` e `final-escuro-manager-390.png` |

Antes e depois (resumo): de uma tela única de filtros em cinza e azul para entrada por perfil, bloco de resumo marinho com palavra editorial em itálico, abas e cards com ícone por status, mapa do time com higiene de carteira, e os mesmos tokens nos temas claro e escuro.

### Screenshots finais (`process-log/screenshots/`)

`final-entrada-{1280,390}.png`, `final-vendedor-{1280,390}.png`, `final-manager-{1280,390}.png`, `final-pauta-{1280,390}.png`, `final-escuro-vendedor-{1280,390}.png`, `final-escuro-manager-{1280,390}.png`, `final-escuro-pauta-{1280,390}.png`. Os `final_inicio_*`, `final_vendedor_*`, `final_card-aberto_*`, `final_modo-teste_*` e `final_como-funciona_*` são regravados por `tools/check_app.py --prefix final` (a vista "inicio" agora é a tela de entrada).

## Contraste (WCAG AA), gerado do `style.css`

Mínimos: 4,5:1 para texto, 3:1 para elementos gráficos. Fonte: `python tools/contrast_table.py` (a mesma lista de pares que o `check_app.py` usa para reprovar o build).

| Texto ou elemento | Sobre | Uso | Mínimo | Claro | Escuro | Resultado |
| :--- | :--- | :--- | ---: | ---: | ---: | :--- |
| `text` | `bg` | texto da página | 4,50:1 | 15,33:1 | 16,21:1 | passa |
| `text` | `surface` | texto em cards | 4,50:1 | 16,83:1 | 13,26:1 | passa |
| `text` | `soft` | texto em fundos suaves | 4,50:1 | 14,15:1 | 11,58:1 | passa |
| `muted` | `bg` | texto secundário | 4,50:1 | 6,30:1 | 8,77:1 | passa |
| `muted` | `surface` | texto secundário em cards | 4,50:1 | 6,92:1 | 7,17:1 | passa |
| `muted` | `soft` | texto secundário em fundos suaves | 4,50:1 | 5,82:1 | 6,26:1 | passa |
| `link` | `bg` | links | 4,50:1 | 9,98:1 | 10,51:1 | passa |
| `link` | `surface` | links em cards | 4,50:1 | 10,96:1 | 8,60:1 | passa |
| `focus` | `bg` | anel de foco na página | 3,00:1 | 5,00:1 | 6,16:1 | passa |
| `focus` | `surface` | anel de foco em cards | 3,00:1 | 5,50:1 | 5,04:1 | passa |
| `focus-hi` | `hero` | anel de foco na barra e no resumo | 3,00:1 | 8,26:1 | 8,26:1 | passa |
| `control` | `bg` | borda de campos | 3,00:1 | 3,80:1 | 5,60:1 | passa |
| `control` | `surface` | borda de campos e botões | 3,00:1 | 4,17:1 | 4,58:1 | passa |
| `gold-ink` | `gold` | texto do botão primário | 4,50:1 | 5,82:1 | 5,82:1 | passa |
| `gold` | `hero` | marca dourada na barra | 3,00:1 | 5,82:1 | 5,82:1 | passa |
| `hero-text` | `hero` | texto da barra e do resumo | 4,50:1 | 15,33:1 | 15,33:1 | passa |
| `hero-muted` | `hero` | texto secundário do resumo | 4,50:1 | 9,09:1 | 9,09:1 | passa |
| `hero-accent` | `hero` | palavra editorial em itálico | 4,50:1 | 8,26:1 | 8,26:1 | passa |
| `inv-text` | `inv-bg` | botão de ação marcado e etiqueta do perfil | 4,50:1 | 15,33:1 | 15,33:1 | passa |
| `note-text` | `note-bg` | faixa do modo teste e avisos | 4,50:1 | 9,25:1 | 10,48:1 | passa |
| `note-line` | `note-bg` | borda dos avisos | 3,00:1 | 4,33:1 | 4,60:1 | passa |
| `bad` | `surface` | alertas em cards | 4,50:1 | 7,53:1 | 7,15:1 | passa |
| `bad` | `bg` | alertas na página | 4,50:1 | 6,85:1 | 8,74:1 | passa |
| `limpe-c` | `border` | barra de higiene sobre a trilha | 3,00:1 | 4,97:1 | 5,48:1 | passa |
| `foque-c` | `surface` | foque: texto em cards | 4,50:1 | 6,78:1 | 8,18:1 | passa |
| `foque-c` | `bg` | foque: texto na página | 4,50:1 | 6,17:1 | 10,00:1 | passa |
| `foque-c` | `foque-t` | foque: texto no fundo suave | 4,50:1 | 5,70:1 | 7,32:1 | passa |
| `text` | `foque-t` | foque: texto principal no fundo suave | 4,50:1 | 14,15:1 | 11,85:1 | passa |
| `muted` | `foque-t` | foque: texto secundário no fundo suave | 4,50:1 | 5,82:1 | 6,41:1 | passa |
| `foque-l` | `surface` | foque: linha gráfica em cards | 3,00:1 | 4,23:1 | 5,47:1 | passa |
| `foque-l` | `bg` | foque: linha gráfica na página | 3,00:1 | 3,85:1 | 6,69:1 | passa |
| `foque-h` | `hero` | foque: número sobre o marinho | 4,50:1 | 9,46:1 | 9,46:1 | passa |
| `reative-c` | `surface` | reative: texto em cards | 4,50:1 | 6,59:1 | 7,34:1 | passa |
| `reative-c` | `bg` | reative: texto na página | 4,50:1 | 6,00:1 | 8,97:1 | passa |
| `reative-c` | `reative-t` | reative: texto no fundo suave | 4,50:1 | 5,42:1 | 7,32:1 | passa |
| `text` | `reative-t` | reative: texto principal no fundo suave | 4,50:1 | 13,83:1 | 13,23:1 | passa |
| `muted` | `reative-t` | reative: texto secundário no fundo suave | 4,50:1 | 5,68:1 | 7,16:1 | passa |
| `reative-l` | `surface` | reative: linha gráfica em cards | 3,00:1 | 4,58:1 | 5,02:1 | passa |
| `reative-l` | `bg` | reative: linha gráfica na página | 3,00:1 | 4,17:1 | 6,14:1 | passa |
| `reative-h` | `hero` | reative: número sobre o marinho | 4,50:1 | 8,48:1 | 8,48:1 | passa |
| `limpe-c` | `surface` | limpe: texto em cards | 4,50:1 | 7,34:1 | 8,07:1 | passa |
| `limpe-c` | `bg` | limpe: texto na página | 4,50:1 | 6,68:1 | 9,87:1 | passa |
| `limpe-c` | `limpe-t` | limpe: texto no fundo suave | 4,50:1 | 6,02:1 | 7,25:1 | passa |
| `text` | `limpe-t` | limpe: texto principal no fundo suave | 4,50:1 | 13,80:1 | 11,90:1 | passa |
| `muted` | `limpe-t` | limpe: texto secundário no fundo suave | 4,50:1 | 5,67:1 | 6,44:1 | passa |
| `limpe-l` | `surface` | limpe: linha gráfica em cards | 3,00:1 | 3,70:1 | 4,94:1 | passa |
| `limpe-l` | `bg` | limpe: linha gráfica na página | 3,00:1 | 3,37:1 | 6,04:1 | passa |
| `limpe-h` | `hero` | limpe: número sobre o marinho | 4,50:1 | 9,33:1 | 9,33:1 | passa |
| `qualifique-c` | `surface` | qualifique: texto em cards | 4,50:1 | 7,03:1 | 7,47:1 | passa |
| `qualifique-c` | `bg` | qualifique: texto na página | 4,50:1 | 6,40:1 | 9,13:1 | passa |
| `qualifique-c` | `qualifique-t` | qualifique: texto no fundo suave | 4,50:1 | 5,81:1 | 6,47:1 | passa |
| `text` | `qualifique-t` | qualifique: texto principal no fundo suave | 4,50:1 | 13,92:1 | 11,49:1 | passa |
| `muted` | `qualifique-t` | qualifique: texto secundário no fundo suave | 4,50:1 | 5,72:1 | 6,21:1 | passa |
| `qualifique-l` | `surface` | qualifique: linha gráfica em cards | 3,00:1 | 4,05:1 | 4,89:1 | passa |
| `qualifique-l` | `bg` | qualifique: linha gráfica na página | 3,00:1 | 3,69:1 | 5,97:1 | passa |
| `qualifique-h` | `hero` | qualifique: número sobre o marinho | 4,50:1 | 8,64:1 | 8,64:1 | passa |

56 pares, nos dois temas. Menor razão entre o medido e o mínimo exigido: claro 1,12x, escuro 1,29x (acima de 1,00x passa).

## Acessibilidade e testes

- **axe-core 4.9.1** (`tools/check_views.py`): 10 telas (entrada; vendedor; card aberto com ação e simulação; aba Limpe; vendedor sem deals; vendedor em modo teste; manager; carteira com pauta e cópia; visão completa; visão completa em modo teste) x 1280 e 390 px x claro e escuro = **40 execuções, zero violações serious ou critical, zero de impacto menor**. Na 1ª execução havia 8 avisos "moderate" (a faixa do modo teste fora de uma região); resolvido com `role="region"` e `aria-label`. Sanidade: com texto secundário forçado para cinza claro, o mesmo script acusa `color-contrast` serious (cinco nós), então o axe não está vazio.
- **Lighthouse:** não executado (sem Node).
- **`check_views.py`** (11 checagens, exit 0): entrada e hash; vendedor isolado (os 35 vendedores: abas = `data.js`, nenhum card ou nome de outro vendedor, sem filtros); ações no `localStorage`, progresso, simulador animado, teclado e armazenamento bloqueado; manager (só o time, mapa = `data.js`, ordenação, carteira em leitura, pauta 3+3+limpar, cópia, recarregar, endereço com vendedor de outro time não abre); 6 managers x 3 fotos e vendedor em modo teste = `data.js`, sem `%` por vendedor; visão completa preservada com a transparência no "Como funciona"; tema (botão, sistema, persistência, teclado); fontes e números tabulares; layout; axe; console.
- **`check_app.py --prefix final`** (27 checagens, exit 0): continua verificando contagens contra `backtest_metrics.json`, o SCORING e o CSV, filtros em cascata, modo teste, card, teclado, `file://` sem CDN e zero erros de console.
- **`pytest`** (exit 0), **`python -m scorer.build --reference-date 2017-12-31`** (exit 0, `data.js` idêntico) e **`python -m scorer.docs --check`** (exit 0, sem mudanças).

## Erros reais no caminho (para o log honesto)

1. **Ícones em JS reprovados pelo "sem número à mão".** O `check_app` acusou os dígitos dos `path` de SVG escritos em strings do `app.js`. Os ícones foram para um sprite `<symbol>` no `index.html` (o verificador só lê o texto visível), usados com `<use href>`.
2. **"1:1" também reprovado**, no HTML e no JS (`data-sim="1"` também). Passei `data-sim=""` e acrescentei uma exceção explícita e única para o nome do ritual "1:1" na checagem. Nenhuma outra checagem foi afrouxada.
3. **Meu teste de layout não pegava a rolagem interna da tabela** (o corte do botão visto na rodada 3); passou a medir. A correção desse corte criou o recuo no celular (também acima).
4. **Teste do axe com agente errado:** a cena da pauta usava um vendedor de outro time, a pauta não abria e o clique estourou o tempo (30 s). Era erro do teste; a cena passou a escolher vendedor do time da Celia. O axe em `file://` também gera erros de console falsos (XHR de folha de estilo); essas páginas rodam sem coleta de console, e o console das demais telas segue sendo exigido.
5. **Edição via PowerShell:** um `Replace` com `\n` literal quebrou o `check_views.py` (SyntaxError); corrigido com o Edit. Três asserts do teste falharam por detalhe, não por defeito da tela: `inner_text` devolve "MINHA SEMANA" por causa do `text-transform` (passei a ler `text_content`) e o anúncio para leitor de tela chega 30 ms depois do clique (espera de 120 ms).
6. **CSS dos tokens:** o `check_app` antigo lia só um bloco de tokens. Reescrevi a leitura para o tema claro, o escuro explícito e o escuro automático (`prefers-color-scheme`), e ele exige que os dois escuros sejam idênticos.

## Desvios em relação ao pedido

- Terceiro destino na entrada ("Visão completa"), para preservar a tela com filtros, os testes existentes e a visão de RevOps citada na arquitetura de produção.
- Sem Lighthouse, sem skill `frontend-design`, sem leitura de arquivo do Figma (ver acima).
- A 3ª tela do vendedor na matriz é "ação e simulador", porque a pauta do 1:1 é do manager.
- Duas correções pós-rodada 3 verificadas só nos PNGs finais e nos testes, sem 4ª matriz completa.
- `process-log/screenshots/final_*` antigos regravados pelo `check_app` (exigência do README e do `test_readme`).
- Não rodei git, push, gh nem mexi fora de `submissions/rafael-pereira/`.
