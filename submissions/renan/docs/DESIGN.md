# Direção de design

> A direção visual final é escolhida **por mim (humano)** a partir de propostas geradas com a skill `bencium-innovative-ux-designer`. Este arquivo registra o briefing, a escolha e o sistema resultante.

## 1. Briefing

- **Usuário:** vendedor B2B, não técnico, abre a ferramenta na segunda de manhã ou no celular entre reuniões.
- **Tarefa principal:** escolher os próximos 3–5 deals para trabalhar e entender o motivo em segundos.
- **Tom:** confiante, direto, de "sala de guerra comercial" — não de painel de BI.
- **O que evitar:** cara de template (cards cinza arredondados, gradiente roxo, shadcn padrão, KPI genérico no topo), tabelas sem hierarquia, score sem contexto.
- **Elemento memorável (um só):** _a definir na escolha da direção_ — candidatos: o "termômetro" de esfriamento do deal; a lista do dia tratada como uma pauta editorial; a decomposição do score como um recibo.

## 2. Processo

1. Gerar direções tipográficas isoladas (só tipo, cor e espaço) com `bencium-innovative-ux-designer`.
2. Escolher uma e registrar o motivo aqui.
3. Formalizar tokens no `@theme` do Tailwind v4 (cor, tipo, espaçamento, raio, movimento).
4. Construir as telas com `frontend-design` + `ui-typography`.
5. Auditar com `design-audit` e `web-design-guidelines` antes de entregar.

## 3. Direção escolhida

**E2**, fixada em 27/10/2026. Gerei 10 direções só tipográficas (A–J) com a skill `bencium-innovative-ux-designer`. Escolhi E e G como finalistas e pedi a E com a G: a régua de dias da E como linguagem e a ficha campo/valor da G como voz de registro e paleta do modo escuro. Antes de fixar, resolvi o tema claro/escuro/sistema e o comportamento da régua no celular.

- **Elemento memorável:** a página é uma régua de 0 a 138 dias. Cada deal fica posicionado no dia em que está, e os parados ficam além do limite.
- **Arquivos:** `design/round-1/` (A–J, E2 e as fichas de cada direção) e `design/ROUND-2-CONTEXT.md` (regras que governam as telas).

### 3.1 Reabertura: de página para sistema

A pedido meu, a interface virou um sistema com app shell, no padrão de produtos como o Kaggle: menu lateral, busca, cards e indicadores. A régua passou a ser um componente visual em cada deal. Detalhes em `design/ROUND-2-CONTEXT.md`, seção "Reabertura".

## 4. Tokens

Fonte da verdade: `solution/src/app/globals.css`. Resumo:

| Papel | Claro | Escuro |
|---|---|---|
| Fundo da página | #F4F5F7 | #0B2135 |
| Superfície (cards, menu) | #FFFFFF | #10283F |
| Primária | #12151A | #E4ECF3 |
| Secundária | #5A6372 | #7FA2C2 |
| Momento | #00736C | #5FD4C4 |
| Parado | #C2410C | #F2C14E |

Tipografia: Space Grotesk (decisão) e Martian Mono (registro do CRM), auto-hospedadas via Fontsource (OFL).

## 5. Requisitos não negociáveis

- Contraste WCAG AA, foco visível, teclado em tudo.
- Funciona em 375 px de largura sem rolagem horizontal.
- Modo claro e escuro com tokens próprios (não inversão automática).
- `prefers-reduced-motion` respeitado.
- Tipografia correta em pt-BR (aspas curvas, travessão, números tabulares em colunas de valor).
