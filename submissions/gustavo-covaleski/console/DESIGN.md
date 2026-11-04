# Sistema de design do console (F11)

Origem: skill `ui-ux-pro-max` (`--design-system`, estilo "Accessible & Ethical", padrão "Trust & Authority", paleta "navy + azul de ação") e skill `frontend-design` (direção estética e composição). Ajustes meus estão marcados com *.

**Estilo.** Ferramenta de operação sóbria e confiável: navegação navy fixa, conteúdo em fundo suave, cartões brancos com sombra leve. Uma pergunta por tela, escrita como título. O elemento memorável é a tipografia dos títulos-pergunta (serifa); todo o resto é quieto.

**Paleta** (papel de cada cor):
- `#0F172A` navy: navegação lateral e texto de título. Transmite autoridade sem ser "tela escura".
- `#0369A1` azul de ação: só a ação principal de cada tela, links e foco. Nenhum outro uso.
- `#EEF2F6` fundo da área de conteúdo* (a skill sugeriu #F8FAFC; escureci um tom para separar os cartões sem borda pesada).
- `#FFFFFF` cartões; `#E2E8F0` bordas; `#475569` texto secundário; `#0F172A` texto principal.
- Faixas (semânticas, seguras para daltonismo pela diferença de luminância e sempre com ícone + rótulo)*:
  - IA decide `#0F766E` (verde-azulado), ícone de check;
  - IA sugere `#B45309` (âmbar), ícone de olho (o humano confere);
  - humano decide `#9F1239` (carmim), ícone de pessoa.
  Fundos claros correspondentes: `#E6F4F1`, `#FDF3E1`, `#FBE9EE`. Nenhuma cor decorativa além dessas.

**Fontes** (auto-hospedadas em `fonts/`, woff2, `font-display: swap`, licença OFL):
- títulos-pergunta: Source Serif 4, 600*. A skill sugeriu EB Garamond, de tom jurídico; troquei por uma serifa mais legível em tela, que mantém o tom de autoridade.
- interface e números: Fira Sans 400/500/600 (sugestão da skill para dashboards), com números tabulares.

**Escala tipográfica** (razão ~1,25): 12 / 14 / 16 (corpo) / 20 / 25 / 32 (título-pergunta) / 40 (indicador grande).
**Espaçamento:** base 4 px; escala 4, 8, 12, 16, 24, 32, 48 (densidade 6/10).
**Raio:** 10 px em cartões, 999 px em selos e chips, 6 px em botões e campos (hierarquia, não um raio único).
**Sombra:** `0 1px 2px rgba(15,23,42,.06), 0 4px 12px rgba(15,23,42,.05)` só em cartões; o painel lateral tem sombra mais forte.

**Gráficos:** SVG próprio. Barra empilhada horizontal para as faixas; barra de precisão com o IC como faixa clara, o ponto da precisão e duas marcas verticais rotuladas para as metas; linha diária com as metas tracejadas e rotuladas diretamente. Todo gráfico tem um título-pergunta e uma frase de leitura, e não depende de legenda (rótulos diretos).

**Movimento:** ≤ 200 ms, só em resposta à ação (troca de tela, abrir o painel). Desligado com `prefers-reduced-motion`.

**Evitado de propósito:** página escura com manchete em gradiente (o padrão dos concorrentes); tudo branco com fonte do sistema (o padrão da F10); rótulos em caixa alta; emojis como ícones (só SVG inline); mais de 2 colunas de conteúdo.
