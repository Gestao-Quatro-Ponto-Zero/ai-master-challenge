# F12 — Console reimplementado a partir das pranchas aprovadas (spec para o Claude Code)

- **Teto:** 90 min. Ao chegar a 108 min (120%), pare e proponha o corte no report.
- **Ordem de corte, se estourar:** (1) as transições animadas; (2) a busca por texto na Fila (mantenha a busca por `#id`). **Nunca cortar:** a responsividade, os testes de corte de conteúdo, a paridade de funcionalidades e as checagens de números.
- **Fonte de verdade visual:** `planning/F12-design/`, as 7 pranchas aprovadas pelo Gustavo, feitas no Claude Design pelo chat do Projeto:

  | Prancha | Tela | Largura |
  |---|---|---|
  | `Main.dc.html` | Visão geral | desktop 1440 |
  | `Fila.dc.html` | Fila | desktop 1440 |
  | `Governanca.dc.html` | Governança, com o painel de Hardware aberto | desktop 1440 |
  | `Robustez.dc.html` | Robustez, com o cenário de injeção | desktop 1440 |
  | `Tablet.dc.html` | Visão geral | tablet 1024 |
  | `MobileVisao.dc.html` | Visão geral | celular 390 |
  | `MobileTicket.dc.html` | Ticket da fila | celular 390 |

- **Como ler as pranchas:** elas usam a marcação da ferramenta de design (`<x-dc>`, `<sc-for>`, `<sc-if>`, `{{...}}`, `renderVals()`), que **não roda fora dela**. Não copie esses arquivos para o console. Use-os como especificação exata: os estilos inline trazem as cores, tamanhos, espaçamentos, raios e pesos de fonte; os textos são a copy aprovada; `renderVals()` mostra os dados de exemplo e a lógica de estilo por item.
- **O que não muda:** `console/data.js` e `solution/f10_console_dados.py`. Todo número continua vindo do `data.js`; os números das pranchas são de referência e precisam bater com ele.
- **Antes de codar**, rode `/frontend-design` só para revisar a implementação (o design já está decidido; **não** proponha outro).

## 1. Sistema visual (extraído das pranchas — use exatamente)

- **Fontes:** IBM Plex Sans (400, 500, 600, 700) na interface e IBM Plex Mono (400, 500) em ids, contagens e código. Auto-hospedadas em `console/fonts/` (woff2), com a versão em base64 para `file://`, como na F11. Remova Source Serif 4 e Fira Sans. Números tabulares (`font-variant-numeric: tabular-nums`).
- **Cores:**
  - barra superior `#0B1B33`, texto inativo `#C7D2E3`, aba ativa `rgba(255,255,255,0.12)`, chips `#DDE5F0` com borda `rgba(255,255,255,0.18)`;
  - fundo `#F2F4F7`, cartão `#FFFFFF`, borda `#E3E7ED`, divisória `#EEF1F5`;
  - texto `#111827`, secundário `#5F6B7A`, terciário `#3D4A5C`;
  - ação primária `#2457D6` (hover `#1A43AA`), selecionado `#EEF3FE`;
  - faixas, sempre com rótulo de texto:
    - IA decide: barra `#0F7B6C`, selo `#E3F3EF` / `#0B6B5E`;
    - IA sugere: barra `#D98A1E`, selo `#FCEFD9` / `#8F4A00`;
    - Humano decide: barra `#7A8699`, selo `#EAEEF3` / `#3D4A5C`. Cinza, não vermelho: humano não é erro;
  - alerta `#FFF4E5` / borda `#F5C98B` / texto `#5C3300`; dano `#B42318`.
- **Forma:** raio de 12 px nos cartões, 8–10 px em controles e blocos internos, 999 px nos selos. Sombra só no painel lateral da Governança. Alvos de toque ≥ 44 px (48 px no celular).
- **Ícones:** SVG inline de traço, como nas pranchas. Nenhum emoji.
- Atualize `console/DESIGN.md` com este sistema e com a origem (Claude Design, aprovado pelo Gustavo).

## 2. Copy (regras obrigatórias)

- Use **literalmente** os textos das pranchas. Onde a prancha não cobre um estado, siga as mesmas regras:
  - títulos nominais ("Visão geral", "Fila", "Governança", "Robustez"), **nunca** em forma de pergunta;
  - legendas de uma linha; **nenhum** parágrafo explicativo do tipo "O que este gráfico diz";
  - tom técnico e direto, sem frases coloquiais ("tente quebrar", "veja por que").
- **Sem nomes de versão na interface.** Na Robustez, as políticas se chamam "Atual" (= F9), "Sem confirmação no teste" (= F8) e "Inicial" (= F4). O mapeamento para F9/F8/F4 aparece **só** no painel "Sobre os dados".
- **Nomes dos ataques em pt-BR:** "Repetição de categoria", "Ignorar instruções", "Falsa mensagem de sistema", "JSON pronto", "Ordem em português". Os ids internos continuam os de `ataques_v1.json`.
- Números em pt-BR (`Intl.NumberFormat('pt-BR')`), com 1 casa decimal em percentuais na interface, exceto onde a prancha mostra outra precisão.
- **Remover:** o bloco "Comece aqui"; o rodapé repetido em todas as telas (fica uma linha discreta só na Visão geral, como em `Main.dc.html`); o seletor com 300 tickets.

## 3. Telas e comportamento

**Estrutura geral:**
- Roteamento por hash: `#visao`, `#fila`, `#fila/<id>`, `#governanca`, `#governanca/<categoria>`, `#robustez`, `#robustez/<cenario>`.
- Estado global: modo (ativo / sombra), política (atual / sem confirmação / inicial), dia (1–20) e as premissas de custo.
- **Cabeçalho:** marca, as 4 abas, chips de status (modo e dia) e o botão (i) "Sobre os dados", que abre o painel descrito abaixo.

**Visão geral (`Main.dc.html`):**
- título, subtítulo e o botão "Abrir a fila";
- a faixa de alerta, só se houver alerta ativo;
- 4 indicadores: automação, precisão da automação, sugestão com revisão e injeções sem revisão;
- "Distribuição por faixa" (barra empilhada + tabela);
- "Precisão da automação por dia", com 20 pontos vindos de `governanca[d].faixas[politica]` e a linha da meta;
- "Filas por política";
- uma linha de fonte.

**Fila (`Fila.dc.html`):**
- filtro segmentado com contagens e busca por `#id` ou termo;
- lista com id, selo, 1 linha de texto, categoria e confiança;
- detalhe com:
  - selo grande da faixa;
  - texto;
  - categoria sugerida;
  - barra de confiança com os 2 limiares;
  - "Motivo da faixa" em 1 frase, gerada pelo caminho real da decisão;
  - botões **Confirmar `<categoria>`** e **Corrigir categoria**;
  - atalhos Enter e 1–8;
  - "Detalhes do modelo" recolhido: 2ª opção, termos e rótulo histórico, com o texto "correção simulada".
- Reentregar, simular reembolso e injetar **não ficam aqui**: estão na Robustez.

**Governança (`Governanca.dc.html`):**
- frase da regra no subtítulo;
- tabela com fila, política, barra do IC com ponto da precisão e as 2 metas (legenda **uma vez**, no cabeçalho), n e ação (Manter / Revisar / Promover / Rebaixar), calculadas pela regra da F4 no dia escolhido;
- ao clicar numa categoria, abre o painel lateral com:
  - 3 números;
  - o veredito em 1 frase;
  - a curva do limite inferior por dia com as metas;
  - o controle "Dia do piloto", que só existe aqui.

**Robustez (`Robustez.dc.html`):** menu de 5 cenários e o painel do cenário ativo.
- **Injeção:**
  - seletor de ataque;
  - seletor de ticket com **até 8 ids**: o 10244 como padrão e os tickets da fila em que a política "Sem confirmação no teste" deixa o ataque passar, calculados do `data.js`;
  - o texto do ticket com o trecho injetado destacado;
  - os 2 cartões lado a lado (sem confirmação × atual);
  - a tabela agregada das 3 políticas.
- **Evento duplicado:** reentrega o mesmo `event_id` e mostra "Duplicado: nenhuma nova decisão" e a linha `tipo: duplicado` no log.
- **Regra de reembolso:** o ticket 22129 marcado como reembolso vai para humano.
- **Modo sombra:** chave com o efeito na cobertura e o alerta.
- **Troca de política:** seletor das 3 políticas com o efeito na cobertura e no dano. Voltar para "Atual" é o rollback.
- O log da sessão fica recolhido no fim desta tela.

**Painel "Sobre os dados"** (decisão do Gustavo: as premissas de custo ficam aqui):
- origem dos dados (holdout do DS2, TI interna);
- a correção do atendente simulada pelo rótulo original;
- a transferência para a operação como premissa;
- o mapeamento Atual = F9, Sem confirmação no teste = F8, Inicial = F4;
- premissas editáveis (R$/h, min/ticket, tickets/ano), com a economia do cenário A recalculada e a linha "Cenário B: zero";
- link para o README.

## 4. Responsividade (obrigatória; é o principal motivo desta fase)

| Faixa | Layout |
|---|---|
| ≥ 1200 px | como as pranchas de desktop |
| 768–1199 px | como `Tablet.dc.html`: barra superior com as abas numa segunda linha; indicadores 2 × 2; seções empilhadas. Na Fila, a lista vira coluna estreita até 1024 px e, abaixo disso, a lista e o detalhe empilham. Na Governança, o painel lateral vira bloco abaixo da tabela. Na Robustez, o menu de cenários vira abas roláveis no topo |
| < 768 px | como `MobileVisao.dc.html` e `MobileTicket.dc.html`: cabeçalho compacto e **barra de navegação inferior fixa** com 4 ícones e rótulos (safe-area). Na Fila: tela de lista → toque abre a tela do ticket (`#fila/<id>`), com voltar e **barra de ação fixa** (Confirmar 2/3 + Corrigir 1/3). Na Governança: cada fila vira um cartão empilhado (nome + selo, barra do IC e ação), e o painel abre em tela cheia. Na Robustez: um seletor de cenário no topo, e os cartões de comparação empilham |

- Use `min-width: 0` em todo filho de flex/grid com texto e `overflow-wrap: anywhere` no texto de tickets. Tabelas largas (só a agregada da Robustez) ficam em caixa com `overflow-x: auto`.

## 5. Verificação (Playwright, por `file://` e por `http.server`)

1. **Larguras:** 1440 × 900, 1280 × 800, 1024 × 768, 820 × 1180, 768 × 1024, 390 × 844 e 360 × 740. Em cada uma, percorra as 4 telas, mais `#fila/<id>` e `#governanca/Hardware`.
2. **Teste de corte** (o da F11 não pegava conteúdo cortado dentro de contêiner). Para cada elemento visível com texto:
   - `getBoundingClientRect()` precisa ficar entre −1 e `innerWidth + 1`;
   - nenhum ancestral com `overflow: hidden` pode cortá-lo (compare o retângulo com o do ancestral);
   - `scrollWidth ≤ clientWidth + 1`, exceto elementos marcados como truncados (classe `.truncar`, com `text-overflow: ellipsis`) e o que estiver dentro de um contêiner `overflow-x: auto` permitido.
   Grave as violações em `planning/F12-cortes.json`. **Zero violações é critério de aceite.**
3. **Alvos de toque:** abaixo de 768 px, todo botão e link interativo com pelo menos 44 × 44 px.
4. **Números:** os 4 indicadores da Visão geral e o último ponto do gráfico conferem com `data.js` (13,37%; 98,75%; 32,12%; 0 de 6.395; dia 20 = 98,75%).
5. **Paridade:** a checklist da F11, item a item, com o novo caminho de cada função.
6. `pytest solution/tests -q` passa; sem erro de JavaScript no console em nenhuma largura.

## 6. Screenshots, docs, commit

- Screenshots (deviceScaleFactor 2) em `process-log/screenshots/`, **substituindo** `v1`–`v6` e `antes_depois.png` (use `git rm`):
  - `d1_visao.png`, `d2_fila.png`, `d3_governanca.png`, `d4_robustez.png` (1440 × 900);
  - `t1_visao.png` (1024 × 768);
  - `m1_visao.png`, `m2_ticket.png`, `m3_governanca.png` (390 × 844, página inteira);
  - `antes_depois.png`, com a F11 ao lado da F12 na Visão geral.
- **README:** a imagem embutida passa a ser a `d1_visao.png`, e a lista de capturas é atualizada.
- **Process log:**
  - linha da F12 com "Decisão minha" vazia;
  - em "O que a IA sugeriu", a entrada: "design refeito pelo chat do Projeto no Claude Design, com análise crítica do console publicado: celular cortado dentro do contêiner, copy em forma de pergunta e explicativa, jargão de versão, humano em vermelho. Aprovado pelo Gustavo, com 3 decisões: sem nomes de versão na interface, sem guia, premissas no painel 'Sobre os dados'";
  - na tabela de erros: "F11: o teste de responsividade só checava rolagem horizontal e não detectou conteúdo cortado dentro de contêiner a 375 px. Detectado pelo Gustavo e confirmado pelo chat no navegador."
- Checagens de commit da F11. Commit `F12: console reimplementado a partir das pranchas aprovadas; responsivo e copy técnica`. Sem push.
- `planning/F12-report.md` no formato da seção 8 do `CLAUDE.md`, com a tabela de cortes por largura (deve ser 0) e a checklist de paridade.
- **Lembrete para o Gustavo no fim do report:** `npx vercel --prod` na pasta `console`.
