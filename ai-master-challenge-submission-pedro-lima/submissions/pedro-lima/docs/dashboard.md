# Documentacao — Dashboard (index.html)

## Visao geral

Aplicacao web single-file (HTML + CSS + JS inline) que consome `scored_deals.json` e apresenta o pipeline priorizado para o vendedor. Sem dependencias externas alem do Google Fonts (Manrope).

**Arquivo:** `solution/index.html`
**Dados:** `solution/data/scored_deals.json`
**Servir:** `npx http-server solution/ -p 8000 -c-1`
**URL:** `http://localhost:8000`

---

## Fluxo do usuario

### 1. Login

Tela inicial com fundo navy. O vendedor seleciona seu nome em um dropdown. Ao selecionar, ve preview:
- Escritorio
- Gestor
- Taxa de fechamento
- Deals ativos

Clica "Entrar". Transicao com fade para o dashboard.

Dados carregados via `fetch('data/scored_deals.json')`. O dropdown e populado com os agentes unicos do JSON.

### 2. Plano de acao (banner)

Apos login, o vendedor ve um banner navy com passos numerados. Exemplo:

```
1. Ligue agora para 2 deals prontos para fechar. Comece por Green-Plus. Total: R$ 550
2. Resgate 7 deals que estao esfriando (ate 172 dias). Sao R$ 11.1k em risco.
3. Avance a qualificacao de 3 deals com boa chance. Total: R$ 16.4k
4. Priorize as 16 contas que voce ja conhece (22% do pipeline).
5. Voce tem 59 deals para trabalhar esta semana. Reserve blocos de tempo.
```

O plano adapta automaticamente ao perfil do vendedor. Se nao tem deals para atacar, o passo 1 nao aparece. Se todos os deals sao de contas novas, o passo de contas conhecidas muda.

### 3. Cards de resumo

4 cards com contagem e valor:
- Fechar Agora (verde)
- Resgatar Hoje (laranja)
- Avancar Qualificacao (azul)
- Pipeline Total (navy)

### 4. Funil de vendas

Barras horizontais: Prospeccao, Em Negociacao, Ganhos (mes), Perdidos (mes). Com contagem e valor.

### 5. Filtros

- Tipo de conta: Conta conhecida / Conta nova
- Produto: dropdown com todos os produtos
- Toggle: Todos / Contas conhecidas / Contas novas

### 6. Kanban interativo com drag & drop

O kanban e a area principal de trabalho do vendedor. 5 colunas representando as acoes do motor:

| Coluna | Cor | Significado |
|--------|-----|-------------|
| Fechar Agora | Verde | Alta chance + timing ideal. Ligar agora. |
| Resgatar Hoje | Laranja | Bom potencial, mas esfriando (>90 dias). Agir rapido. |
| Avancar | Azul | Boa chance, ainda cedo. Agendar reuniao. |
| Trabalhar | Dourado | Chance moderada. Manter ritmo semanal. |
| Nutrir | Cinza | Fase inicial ou chance baixa. Contato leve. |

Cada coluna mostra contagem de deals e valor total. Cards ordenados por prioridade (maior primeiro).

**Drag & drop — o vendedor reorganiza seu pipeline:**

O vendedor pode arrastar qualquer card de uma coluna para outra. Isso permite que ele sobreponha seu julgamento ao do motor. Por exemplo: o motor classificou um deal como "Trabalhar", mas o vendedor sabe que teve uma reuniao boa ontem e quer mover para "Fechar Agora".

Ao soltar o card na nova coluna:
1. O `deal.action` e atualizado em memoria
2. A **cor da borda esquerda** do card muda para a cor da nova coluna
3. A **barra de chance** muda de cor para refletir a nova coluna
4. Os **contadores e valores totais** de ambas as colunas (origem e destino) recalculam
5. Os **cards de resumo** no topo da pagina atualizam
6. O **funil de vendas** atualiza

Implementacao tecnica: HTML5 Drag API com eventos `dragstart`, `dragover`, `dragleave`, `drop`. Cada coluna tem `data-bucket` com o nome da acao. O `onDrop` encontra o deal por ID e atualiza `deal.action`, depois chama `renderKanban()` para re-renderizar tudo.

Limitacao: mudancas de coluna nao persistem entre sessoes (nao ha backend). Ao recarregar a pagina, os deals voltam para a classificacao original do motor.

### 7. Card de deal

Cada card mostra as informacoes essenciais para o vendedor tomar decisao:

**Visivel sempre:**
- Nome da conta (ou "ID Oportunidade: XXXX" para deals sem conta no CRM)
- Tag: CONHECIDA (azul) ou NOVA (dourado)
- Produto + estagio (Prospeccao ou Negociacao)
- Barra de chance com percentual — cor da barra reflete a coluna atual
- Explicacao em linguagem simples do motivo (ex: "Ja vendeu para Cheers antes. Aberto ha 159 dias, risco alto.")
- Valor em reais + dias desde abertura (vermelho se >120 dias)

**Botoes de acao:**
- **"Ja contatei"** — Toggle. Salva timestamp em localStorage. Muda para "Contatado" com estilo visual diferente. Clicando de novo, desfaz.
- **"Anotar"** — Expande o card para mostrar detalhes e campo de texto.

**Card expandido (clique no card ou em "Anotar"):**
- Detalhes: produto, valor, setor, porte, estagio, dias aberto
- Textarea livre para anotacoes do vendedor — salva automaticamente em localStorage por deal ID (evento `onblur`)

### 8. Modal "Resumo dos Deals"

O botao **"Resumo dos Deals"** no banner superior abre um modal com a visao consolidada de todo o pipeline do vendedor. E a forma rapida de entender a situacao sem percorrer o kanban inteiro.

**Estrutura do modal:**

- **Header navy** com titulo "Resumo dos Deals" e subtitulo personalizado ("81 deals ativos no pipeline de Corliss Cosme")
- **Buckets colapsaveis** — cada bucket mostra:
  - Nome da acao com dot colorido
  - Contagem de deals
  - Chance media do bucket
  - Valor total
  - Seta para expandir/colapsar

**Ao expandir um bucket:**

1. **Explicacao do motivo** — Texto direto explicando por que esses deals estao nesse bucket. Ex: "Potencial real, mas passaram de 90 dias. Aja rapido." Sem termos tecnicos, sem bold excessivo.

2. **Lista de deals** — Cada deal mostra:
   - Nome da conta (ou ID)
   - Produto
   - Chance (%) com cor
   - Valor em reais
   - Dias aberto
   - Razao individual (ex: "Historico limitado com Zoomit. Ha 106 dias, passando do ideal. Bom potencial, mas esta esfriando.")

- **Barra de total** fixa no rodape: total de deals + valor total do pipeline

**Interacao:** Clique no bucket para expandir/colapsar. Fechar com X, clicando fora do modal, ou tecla Esc. Body scroll e bloqueado enquanto o modal esta aberto.

### 9. Aba "Como Funciona"

6 secoes visuais:
1. **Sinais usados** — Barras horizontais mostrando peso de cada sinal
2. **Contas novas vs conhecidas** — Comparacao lado a lado dos sinais disponiveis
3. **Cascata de relacionamento** — Visualizacao dos 4 niveis de fallback
4. **Timeline de urgencia** — Barra com faixas de dias e o que cada uma significa
5. **Formula de prioridade** — 55% Chance + 25% Urgencia + 20% Valor (visual)
6. **Baldes de acao** — Descricao de cada balde com criterios

---

## Persistencia (localStorage)

| Chave | Conteudo |
|-------|----------|
| `g4_contacts` | JSON com deal_id → timestamp de contato |
| `g4_notes` | JSON com deal_id → texto da anotacao |

Persiste entre sessoes. Nao sincroniza entre dispositivos.

---

## Paleta visual

| Token | Valor | Uso |
|-------|-------|-----|
| --navy | #001F35 | Header, banner, modal header |
| --gold | #B9915B | Destaques, logo, coluna Trabalhar |
| --light | #F5F4F3 | Background geral |
| --green | #3A7D44 | Fechar Agora |
| --orange | #C45A00 | Resgatar Hoje |
| --blue | #2966A3 | Avancar Qualificacao |
| --red | #B33030 | Limpar Pipeline |
| --gray-400 | #A8A8A3 | Nutrir |

Font: Manrope (400, 600, 700).

---

## Estrutura do JS

| Funcao | O que faz |
|--------|-----------|
| `doLogin()` | Valida selecao, carrega dados do agente, transicao para dashboard |
| `renderAll()` | Chama renderSummary + renderFunnel + renderGuide + renderKanban |
| `renderGuide()` | Gera plano de acao numerado baseado nos deals do agente |
| `renderKanban()` | Distribui deals nas 5 colunas, renderiza cards |
| `renderCard(d)` | Gera HTML de um card com cores dinamicas por coluna |
| `buildReason(d)` | Gera explicacao em linguagem simples (historico + timing) |
| `openSummaryModal()` | Popula e abre o modal de resumo |
| `buildModalReason(d)` | Gera razao individual para o modal |
| `onDragStart/End/Over/Leave/Drop` | Drag & drop entre colunas |
| `markContact(id)` | Toggle contato + localStorage |
| `saveNote(id, text)` | Salva anotacao em localStorage |
| `toggleAccountFilter()` | Filtra por tipo de conta |
| `formatMoney(v)` | Formata valor em R$ com sufixo k/M |

---

## Limitacoes tecnicas

1. **Single-file** — ~1600 linhas. Para escalar, separar em componentes.
2. **Sem backend** — Dados estaticos em JSON. Nao persiste mudancas de coluna (drag & drop) entre sessoes.
3. **localStorage apenas** — Anotacoes e contatos nao sincronizam entre dispositivos.
4. **Sem autenticacao** — Login e apenas selecao de nome, sem senha.
5. **Responsivo limitado** — Otimizado para desktop (1440px+). Kanban empilha em telas menores.
