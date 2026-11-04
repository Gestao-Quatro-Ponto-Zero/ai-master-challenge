# F10 — Console do piloto (spec para o Claude Code)

- **Teto:** 90 min. Ao chegar a 108 min (120%), pare e proponha o corte no report.
- **Ordem de corte, se estourar:** (1) o seletor de política (rollback); (2) o painel de alertas. Fila, detalhe, governança, modo sombra, injeção e duplicado **não são cortados**.
- **Leia antes:** `CLAUDE.md`; `solution/triagem.py`; `solution/f8_oof.py`; `solution/f9_confirmacao.py`; `solution/outputs/f8_*`; `solution/outputs/f5_injecao.json`; `docs/producao.md`.
- **Objetivo:** um console **estático** (HTML + CSS + JS puros, sem framework, sem CDN, sem backend), que abre com um clique (Vercel) e com duplo clique local. Ele mostra **o piloto rodando**, não um ticket isolado: fila do atendente, correção, governança por categoria contra a meta, modo sombra, rollback de política, injeção e duplicado. Nenhum concorrente mostra isso; o padrão deles é "cole um ticket e veja o porquê".
- **Regra de ouro:** todo número da tela vem de `console/data.js`, gerado por um script a partir dos arquivos já existentes. **Nenhum número novo inventado.** O que é simulação é dito na própria tela.
- **Decisões do Gustavo:** console completo; publicação na Vercel; exceção aprovada para uma amostra de ~300 tickets do DS2 com texto no repositório (CC0).

## Passo 1 — `solution/f10_console_dados.py` → `console/data.js`

Gere `console/data.js` com `window.DADOS = {...}` (assim o `index.html` abre também por `file://`). O script usa `triagem.py` e o modelo da versão atual. Conteúdo:

1. **`meta`:**
   - *e*_Q2, 1 − *e*_inferior, 1 − *e*_superior;
   - limiares `t_decide` e `t_sugere` (F8);
   - versões do modelo e da política;
   - data de geração;
   - origem de cada bloco (nome do arquivo).
2. **`politicas`:** três versões por categoria:
   - `F9 implantada` (padrão);
   - `F8 seleção OOF`;
   - `F4 (escolhida no holdout)`.
   Cada uma vem dos CSV/JSON existentes.
3. **`fila`:** **300 tickets** do holdout por grupo, sorteados com seed 42, distribuídos em **20 dias** de 15 tickets (ordem aleatória, seed 42; o holdout não tem data). Para cada ticket:
   - `id`, `dia`;
   - `texto` (até 400 caracteres; se cortar, marque `truncado: true`);
   - `rotulo_original`, `pred`, `p_max`, `top2`, os termos do motivo (os mesmos de `triagem.classificar`);
   - a faixa em cada uma das 3 políticas, com o "por que" de cada uma (mesma lógica de `faixa_para`).
4. **`ataques`:** para os 300 tickets × os 5 ataques de `ataques_v1.json`, calcule com o clássico: categoria nova, `p_max` e faixa em cada política. São dados reais, não simulados.
5. **`governanca`:** para o **holdout inteiro** (9.567 tickets, sem texto), na mesma ordem aleatória, repartido em 20 dias. Por dia e categoria, **acumulado**:
   - n e acertos (contra o rótulo original) dos tickets com `p_max ≥ t_decide`, sem considerar a política (é a "precisão sombra", que diz se a categoria poderia subir);
   - o IC de Wilson;
   - a decisão que a regra da F4 daria com esse limite inferior;
   - a contagem por faixa em cada política.
   **Checagem obrigatória:** no dia 20, o limite inferior por categoria precisa bater com `li_ia_decide` do holdout em `f8_politica_por_categoria.csv` nas categorias implantadas em IA decide, e a cobertura total com 13,37%. Se não bater, pare e reporte.
6. **`kpis`:**
   - cobertura e precisão por faixa (`f8_faixas.json`, `implantada`);
   - dano da injeção (`f5_injecao.json`);
   - premissas de custo (R$ 35/h, 3 min, 30 mil tickets/ano), editáveis na tela.
7. **Testes** (`solution/tests/test_f10.py`):
   - `data.js` existe e o JSON interno é válido;
   - a fila tem 300 tickets e 20 dias;
   - a checagem do item 5 passa;
   - nenhum nome ou e-mail do DS1 aparece;
   - nenhuma sequência de 8 palavras de ticket fora dos 300 ids da fila.

## Passo 2 — `console/index.html` + `console/app.js` + `console/styles.css`

**Direção visual: ferramenta de operação, não página de apresentação.** Os concorrentes fazem páginas escuras com manchete e cartões de indicadores. O console precisa parecer o sistema que o atendente e o supervisor abrem de manhã:
- tema claro;
- fundo cinza neutro e painéis brancos;
- denso;
- tipografia do sistema;
- números tabulares (`font-variant-numeric: tabular-nums`), em **pt-BR** (`Intl.NumberFormat('pt-BR')`, vírgula decimal);
- uma única cor de acento;
- verde / âmbar / vermelho **só** para as faixas (IA decide / IA sugere / humano decide), sempre com texto junto da cor;
- contraste AA e navegação por teclado (↑/↓ na fila, Enter confirma, 1–8 corrige);
- abaixo de 900 px, as colunas empilham.

**Barra superior:**
- nome "Console do piloto — triagem de tickets";
- controle "dia do piloto" (1 a 20);
- chave **modo: ativo / sombra**;
- seletor **política: F9 implantada / F8 OOF / F4**;
- contador de alertas;
- link "como ler esta tela" (abre um painel curto).

**Três colunas:**

1. **Fila (esquerda):** os tickets até o dia escolhido. Cada linha traz o id, o início do texto, um selo de faixa e o estado (pendente / confirmado / corrigido). Filtros por faixa.
2. **Detalhe (centro):**
   - texto do ticket (com "… (trecho)" se truncado);
   - faixa com selo; categoria; confiança; as duas mais prováveis;
   - **"por que esta faixa"** em passos numerados: confiança × limiar, teto da política da categoria, regra de ação, modo sombra;
   - termos do motivo.
   Ações:
   - **Confirmar**;
   - **Corrigir para…**;
   - **Reentregar (webhook)**: o mesmo `event_id`; mostra "duplicado: nenhuma nova decisão" e acrescenta a linha `tipo: duplicado` ao log da tela. Implemente a mesma lógica de chave de `triagem.py` e cite `test_f8.py`;
   - **Simular tipo "Reembolso"**: a regra de ação manda para humano;
   - **Injetar ataque** (seletor com os 5): mostra a decisão pré-calculada do ataque nesse ticket e se ela continuaria em IA decide.
   Para o piloto, a correção é **simulada pelo rótulo original**. Um aviso fixo diz isso, e diz que o rótulo tem ruído próprio.
3. **Governança (direita):**
   - **Tabela por categoria:** política vigente; n sombra acumulado; precisão sombra com IC; uma barra horizontal com o IC e duas marcas verticais (1 − *e*_inf e 1 − *e*_sup); a decisão que a regra daria **hoje** (promover / manter / rebaixar), com o texto da regra; um alerta quando a decisão da regra difere da política vigente.
   - **Mini-gráfico (SVG inline)** da evolução do limite inferior por dia para a categoria selecionada, com as linhas da meta.
   - **Cartões compactos:** cobertura por faixa no dia; precisão medida em IA decide; trabalho humano evitado e economia no cenário A, com as premissas editáveis em 3 campos e a nota "cenário B: zero".

**Painel de alertas** (abre pelo contador):
- queda da cobertura de IA decide > 3 p.p. contra a base (dispara ao ligar o modo sombra);
- dano da injeção na política escolhida: com F8 OOF aparecem as 80 trocas silenciosas; com F9, zero;
- duplicados reentregues;
- categoria em que a regra discorda da política vigente.

**Log da tela:** uma faixa recolhível no rodapé com as linhas JSONL das ações (mesmos campos de `decisoes.jsonl`, sem texto).

**Rodapé fixo:**
- "Dados: holdout do DS2 (TI interna, 47.837 tickets). A transferência para a operação de suporte é premissa. A correção do atendente é simulada pelo rótulo original. Fontes: `solution/outputs/`".
- Link para o README.

## Passo 3 — Verificação visual e screenshots

- Abra com Playwright por `file://` e por `python -m http.server`, a 1440 × 900 e a 390 × 844. Confira que não há erro no console do navegador nem rolagem horizontal.
- Screenshots (deviceScaleFactor 2) em `process-log/screenshots/`:
  - `c1_console.png`: visão geral no dia 20;
  - `c2_governanca.png`: Hardware selecionada no gráfico;
  - `c3_injecao_f8_vs_f9.png`: o mesmo ataque com F8 OOF e com F9;
  - `c4_sombra.png`: modo sombra com o alerta.

## Passo 4 — Deploy (preparar; quem publica é o Gustavo)

- `console/vercel.json` mínimo, para site estático, sem build.
- Em `planning/F10-report.md`, os comandos exatos para ele rodar: `cd ai-master-challenge/submissions/gustavo-covaleski/console`, depois `npx vercel` e `npx vercel --prod`. Diga o que esperar do login no navegador.
- **Não rode a Vercel você mesmo.** Não faça login em nada.

## Passo 5 — Documentos, process log, commit

- **README:** no topo, logo abaixo do título, a linha "**Console do piloto:** `[URL — preencher após o deploy]`" e "abre localmente com duplo clique em `console/index.html`". Em Resultados, embuta `c1_console.png`. Em Limitações: "o console simula a correção do atendente com o rótulo original; a classificação de texto livre roda no protótipo Streamlit local". Em "Como rodar", o passo do `f10_console_dados.py`.
- **Process log:** linha da F10 com "Decisão minha" vazia; a exceção dos 300 tickets com texto (decisão do Gustavo).
- **Checagens:**
  - `pytest`;
  - `f1_splits.csv` com o mesmo hash;
  - add filtrado + `git diff --cached --name-only` com as regras de aborto da F8;
  - texto do DS2 só em `docs/politica.md`, na planilha adjudicada, no export e em `console/data.js` (só os 300 ids da fila);
  - checagem de segredo.
- **Commit:** `F10: console do piloto estático (fila, governança, sombra, injeção, duplicado)`. Sem push.
- `planning/F10-report.md` no formato da seção 8 do `CLAUDE.md`.
