# Sistema de design do console (F12)

**Origem:** pranchas feitas no Claude Design pelo chat do Projeto (`planning/F12-design/`, 7 pranchas: desktop 1440, tablet 1024, celular 390), aprovadas pelo Gustavo. Este arquivo transcreve o sistema das pranchas; a F11 (Source Serif 4 + Fira Sans, navegação lateral navy) foi substituída.

**Estilo:** ferramenta de operação, barra superior escura, conteúdo em cinza claro, cartões brancos com borda e sem sombra. Títulos nominais ("Visão geral", "Fila", "Governança", "Robustez"), legendas de uma linha, tom técnico.

**Fontes** (auto-hospedadas em `fonts/`, woff2 + `fontes.css` em base64 para `file://`; licença OFL):
- IBM Plex Sans 400/500/600/700: interface;
- IBM Plex Mono 400/500: ids, contagens e código;
- números tabulares em tudo.

**Cores:**
- barra superior `#0B1B33`; aba inativa `#C7D2E3`; aba ativa `rgba(255,255,255,.12)`; chips `#DDE5F0` com borda `rgba(255,255,255,.18)`;
- fundo `#F2F4F7`; cartão `#FFFFFF`; borda `#E3E7ED`; divisória `#EEF1F5`;
- texto `#111827`; secundário `#5F6B7A`; terciário `#3D4A5C`;
- ação primária `#2457D6` (hover `#1A43AA`); selecionado `#EEF3FE`;
- alerta `#FFF4E5` / borda `#F5C98B` / texto `#5C3300`; dano `#B42318`.

**Faixas** (sempre com rótulo de texto):
- IA decide: barra `#0F7B6C`, selo `#E3F3EF` / `#0B6B5E`;
- IA sugere: barra `#D98A1E`, selo `#FCEFD9` / `#8F4A00`;
- humano decide: barra `#7A8699`, selo `#EAEEF3` / `#3D4A5C`. É cinza, não vermelho: humano não é erro.

**Forma:** raio de 12 px nos cartões, 8–10 px em controles e blocos internos, 999 px nos selos. Sombra só no painel lateral da Governança. Alvos de toque ≥ 44 px (48 px na barra inferior do celular).

**Ícones:** SVG inline de traço. Nenhum emoji.

**Responsivo:**
- ≥ 1200 px: pranchas de desktop;
- 768–1199 px: abas numa segunda linha do cabeçalho, indicadores 2 × 2, seções empilhadas;
- < 768 px: cabeçalho compacto, barra de navegação inferior fixa e telas de lista → detalhe.

**Movimento:** transições ≤ 150 ms, só em resposta à ação; desligadas com `prefers-reduced-motion`.
