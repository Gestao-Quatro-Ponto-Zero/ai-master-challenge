# Design — Lead Scorer

Escrito **antes** de mexer no CSS (a tabela de contraste foi regenerada a partir do `style.css` depois, por `tools/contrast_table.py`). Registro das rodadas: [`process-log/08_visoes-e-design.md`](../process-log/08_visoes-e-design.md).

## 1. Direção

Ferramenta de trabalho com cara de produto premium e sóbrio: marinho profundo, off-white quente, um único acento dourado, frases curtas. A hierarquia é: **a frase de ação** (o que fazer esta semana) primeiro, **as quatro listas** depois, **o deal** por último.

- **Inspirada, não copiada.** Os valores de referência foram extraídos dos estilos computados de g4business.com em 25/10/2026 (marinho `#001F35` e `#031A26`, dourado `#B9915B`, off-white `#F5F4F3`, Manrope, Libre Baskerville itálico, botão primário dourado com texto marinho, raio de 10px, peso 800). A interface **não usa o logotipo nem o nome "G4"**. O nome da ferramenta continua "Lead Scorer". A marca da barra é um losango dourado desenhado em CSS. Decisão registrada em [DECISIONS.md](DECISIONS.md).
- **Dourado só para ação primária e marca.** Botão primário, foco do teclado, marca da barra e a palavra editorial em itálico da frase de resumo (tipografia da marca). Nunca como cor de status.
- **Status = cor + ícone + rótulo.** Nenhuma lista depende só da cor.

## 2. Ferramentas e referências desta sessão

- **Skill `frontend-design`:** indisponível nesta sessão. Registrado; o loop visual (seção 9) e o checklist fizeram o papel.
- **Figma:** referências usadas só como inspiração, arquivo não lido (não há link de arquivo do Rafael neste documento, e os arquivos da Comunidade só ficam legíveis pelo conector depois de duplicados). Estrutura tomada das descrições: *Sales Pipeline CRM UI Kit* (cards de pipeline com faixa de estágio), *Lead & Sales Dashboard Design* (resumo no topo, tabela de time), *CosaFin Elite* (espaço em branco e hierarquia premium), *Dark CRM SaaS Dashboard UI Kit* (superfícies escuras em camadas). A paleta é sempre a dos tokens abaixo.
- **Lighthouse:** não executado (sem Node nesta máquina). Em seu lugar: axe-core 4.9.1 via Playwright (Python), nos dois temas ([`tools/check_views.py`](../solution/tools/check_views.py)).

## 3. Tokens (CSS custom properties em `solution/app/style.css`)

### Marca (iguais nos dois temas)

| Token | Valor | Uso |
|---|---|---|
| `--navy-950` | `#031A26` | Fundo do tema escuro |
| `--navy-900` | `#001F35` | Barra, bloco de resumo, superfícies escuras, texto do tema claro |
| `--navy-800` | `#0A2B44` | Superfície do tema escuro, hover sobre marinho |
| `--navy-700` | `#153F61` | Links no tema claro, bordas sobre marinho |
| `--gold-500` | `#B9915B` | Botão primário, marca, foco sobre marinho |
| `--gold-400` | `#D4B07C` | Hover do botão primário, palavra editorial sobre marinho |
| `--gold-700` | `#8A6128` | Foco sobre claro (3:1 contra off-white e branco) |
| `--offwhite` | `#F5F4F3` | Fundo do tema claro, texto sobre marinho |
| `--offwhite-200` | `#EDEBE8` | Fundos suaves, cabeçalhos de tabela |
| `--offwhite-300` | `#D8D4CE` | Bordas no tema claro |

### Semânticos (mudam com o tema)

`--bg`, `--surface`, `--soft`, `--text`, `--muted`, `--border`, `--control` (borda de campos, 3:1), `--link`, `--focus`, `--inv-bg` e `--inv-text` (estado "feito" dos botões de ação: invertido), `--note-bg` e `--note-text` (faixa do modo teste), `--bad`.

### Status das listas (cor + ícone + rótulo)

Cada lista tem três tokens: `-c` (tinta do texto), `-t` (fundo suave) e `-l` (linha gráfica, 3:1).

| Lista | Significado | Cor | Ícone | Rótulo na tela do manager |
|---|---|---|---|---|
| Foque | vivo, alto valor esperado | verde-sálvia | alvo | Vivos |
| Reative | bom, mas esfriando | cobre queimado | seta circular | Esfriando |
| Limpe | deal zumbi | cinza-azulado | lixeira | Zumbis |
| Qualifique | Prospecting, sem data | azul-aço | lupa | Qualifique |

Sobre o marinho do bloco de resumo, cada status usa uma variante clara (`--foque-h` etc.), validada contra `#001F35`.

## 4. Contraste (WCAG AA)

Regra: 4,5:1 para texto, 3:1 para elementos gráficos (linhas de status, borda de campos, foco). Os dois temas, todos os pares usados. A tabela abaixo é gerada do `style.css` por `python tools/contrast_table.py`, e `tools/check_app.py` reprova o build se algum par cair abaixo do mínimo.

<!-- CONTRASTE:inicio -->
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
<!-- CONTRASTE:fim -->

## 5. Tipografia

- `--font-ui: 'Manrope', system-ui, sans-serif` (variável 200 a 800), auto-hospedada em `app/fonts/` (OFL, licenças na pasta). Texto, botões, tabelas.
- `--font-accent: 'Libre Baskerville', Georgia, serif`, **só itálico, só em destaques** (uma palavra do título e da frase de resumo). Nunca em números ou tabelas.
- `font-variant-numeric: tabular-nums` em valores, scores, contagens e tabelas.
- Escala: 14, 16, 18, 20, 24 e 32px (fluida na frase de ação). Peso 800 em botões primários e números grandes.

## 6. Espaçamento, raio e sombra

- Espaçamento em múltiplos de 8px (`--s1` = 8px até `--s6` = 48px; 4px só em respiros internos de ícone).
- Raio: 10px em botões e campos (`--r-btn`), 16px em cards e blocos (`--r-card`).
- Sombras suaves de uma camada (`--shadow`), quase invisíveis no tema escuro, onde a separação vem da borda e da cor da superfície.

## 7. Temas, movimento e foco

- **Claro:** fundo off-white, texto marinho, barra marinho. **Escuro:** fundo marinho-950, superfícies marinho-800, texto off-white.
- Segue `prefers-color-scheme` e tem botão de alternância na barra (a escolha fica em `localStorage`, com `try/catch`; sem armazenamento, o tema do sistema vale).
- Transições de 150 a 200ms em cor, borda e sombra. `prefers-reduced-motion: reduce` desliga transições e a contagem animada dos números.
- Foco visível em dourado: anel de 3px com deslocamento de 2px (`--focus`; dourado escuro sobre claro, dourado de marca sobre marinho).

## 8. Layout

- **Vendedor: mobile first.** Uma coluna; cards empilhados; abas em 2×2 no celular e 4 colunas no desktop; no desktop o card vira uma linha (cabeçalho à esquerda, frases à direita).
- **Manager: desktop first.** Tabela "Meu time" larga, ordenável; no celular cada linha vira um cartão com rótulos.
- Alvos de toque de pelo menos 44×44px; sem rolagem horizontal da página.

## 9. Interatividade com propósito

| O quê | Para quê |
|---|---|
| Card expande com um clique e mostra o "porquê" | Ler a explicação só do deal que importa |
| "Contatei", "Agendei", "Encerrar no CRM" com feedback imediato (botão invertido, selo no card, anúncio por leitor de tela) | Fechar o ciclo da semana; o resumo no topo atualiza na hora; salvo só neste navegador |
| Simulador "E se eu fechar este?" com contagem animada do valor da semana | Ver o impacto de um deal no valor esperado |
| Mapa do time ordenável e clicável; pauta do 1:1 com "Copiar" | Preparar a conversa sem montar planilha |
| Teclado completo: abas com setas, botões nativos, link "pular para o conteúdo", foco movido para o título ao trocar de tela | Acessibilidade |

Nada de animação decorativa sem função.

## 10. Checklist usado em cada rodada

hierarquia clara em 3 segundos; ação principal óbvia; dourado só para ação ou marca; status legível sem a cor; nada cortado ou sobreposto; contraste AA; estados vazios úteis; consistência com os tokens; "parece uma ferramenta premium e sóbria, não um template genérico".

## 11. Decisões de design

- Bloco de resumo marinho nos dois temas (âncora visual da marca; no escuro vira uma superfície a mais).
- Estado "feito" dos botões é **invertido** (marinho com texto claro, e o inverso no escuro) com ícone de check, em vez de dourado ou verde, para não competir com os status das listas nem com a ação primária.
- Higiene de carteira usa o cinza-azulado do Limpe e o rótulo "zumbis"; nunca uma escala de bom/ruim, e nunca taxa de vitória por vendedor (decisão 4 do CLAUDE.md).
