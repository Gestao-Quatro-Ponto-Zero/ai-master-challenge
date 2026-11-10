# Desenho do CRM: estrutura em Next.js

> Proposta para decisão. Nada disto está construído.
> Decisão 20: este é o CRM do time, com a prioridade embutida no pipeline; o nome definitivo ainda vai ser escolhido. O mínimo de CRM que falta está em [DESENHO-CRM.md](DESENHO-CRM.md).
> Usuários, operação do pipeline, banco e auditoria em [DESENHO-ACOES.md](DESENHO-ACOES.md) (decisões 15 e 16).
> Este arquivo segue a stack canônica (decisão 19) e a marca visual do G4 em fundo branco (decisão 18).
> O protótipo em HTML/JS (`index.html`, `app.js`, `styles.css`), feito quando a ideia era uma ferramenta de priorização, vira referência de telas e fluxos e vai para `prototipo-html/`.

## Stack

| Camada | Escolha |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript 5.9 `strict`, Tailwind CSS 4 com os tokens da marca no tema |
| Backend | Route Handlers no runtime Node.js, zod em toda entrada, `@supabase/supabase-js` só no servidor |
| Banco | Postgres no Supabase G4_AI_Mastering (detalhes em [DESENHO-ACOES.md](DESENHO-ACOES.md)) |
| Testes | Vitest nas funções puras; Playwright nos caminhos críticos |
| Publicação | Vercel |
| Metas | LCP abaixo de 2 s, JavaScript da primeira carga abaixo de 300 kB gzip, WCAG AA |

## Onde fica o projeto

**Recomendado: o próprio `solution/app/` vira o projeto Next.**

```bash
cd submissions/leandro-mallet/solution/app
npm ci
npm run dev        # http://localhost:3000
```

- O Next fica separado da parte em Python (`data/`, `analysis/`, `scoring/`), e o dono da pasta continua o mesmo.
- Alternativa descartada: o Next na raiz de `solution/`. O Next trataria a pasta `solution/app/` atual como o roteador dele, e o `package.json` ficaria misturado com o pipeline em Python.
- Vercel: Root Directory = `submissions/leandro-mallet/solution/app`.

## Marca visual (decisão 18, DES-01)

Fundo branco. As cores da marca vão nos menus, botões, abas, selos, gráficos e destaques. Títulos em **Libre Baskerville** e texto em **Manrope**, carregadas por `next/font` (servidas pelo próprio app, sem pedido externo, o que ajuda o LCP).

### Um único arquivo de tema: `src/tema/tema.css`

É o único lugar do projeto com cor, fonte, tamanho de texto, raio e sombra. O Tailwind 4 lê o bloco `@theme` e gera as classes (`bg-marinho`, `text-texto-2`, `font-titulo`…). O CSS e o JavaScript que precisarem de cor leem as mesmas variáveis (`var(--color-marinho)`).

```css
@theme {
  /* Marca */
  --color-marinho:        #001f35;   /* menus, botão principal, títulos */
  --color-marinho-2:      #082437;   /* hover do marinho, topo */
  --color-dourado:        #c9a96e;   /* destaques, aba ativa, selo "focar" (fundo) */
  --color-dourado-claro:  #e4c993;   /* fundos de destaque */
  --color-dourado-medio:  #b9915b;   /* gráficos */
  --color-bronze:         #a57b41;   /* gráficos, bordas de destaque */
  --color-bronze-escuro:  #78501d;   /* texto em tom dourado (único dourado legível sobre branco) */
  --color-marfim:         #fffdf8;   /* superfícies: cartões, painel lateral */

  /* Base */
  --color-fundo:          #ffffff;
  --color-texto:          #001f35;
  --color-texto-2:        #66727c;   /* ver "Contraste" abaixo */
  --color-linha:          #e4c993;

  /* Componentes do score (barra e detalhe) */
  --color-comp-chance:    #001f35;
  --color-comp-valor:     #a57b41;
  --color-comp-tempo:     #e4c993;
  --color-comp-conta:     #6f7c87;

  /* Tipografia */
  --font-titulo: var(--font-libre-baskerville), Georgia, serif;
  --font-texto:  var(--font-manrope), system-ui, sans-serif;
  --text-xs: 0.75rem;  --text-sm: 0.875rem;  --text-base: 1rem;
  --text-lg: 1.125rem; --text-xl: 1.5rem;    --text-2xl: 2rem;   --text-score: 2.75rem;

  /* Forma */
  --radius-cartao: 10px;
  --radius-controle: 6px;
  --shadow-cartao: 0 1px 2px rgb(0 31 53 / 0.06), 0 6px 16px rgb(0 31 53 / 0.06);
}
```

### Contraste (WCAG AA), medido sobre branco

| Cor | Contraste | Uso permitido |
|---|---|---|
| marinho `#001f35` | 16,8:1 | texto, botão principal (texto branco sobre marinho: 16,8:1) |
| dourado `#c9a96e` | 2,2:1 | **nunca texto sobre branco**. Fundo com texto marinho (7,5:1), bordas, aba ativa, gráficos |
| bronze escuro `#78501d` | 7,1:1 | texto em tom dourado |
| cinza `#6f7c87` | **4,3:1** | não passa no AA para texto pequeno (exige 4,5). Fica para bordas, ícones e texto grande |
| cinza ajustado `#66727c` | 4,9:1 | texto secundário. É o cinza da marca 8% mais escuro, e ainda passa sobre o marfim (4,85:1) |

O ajuste do cinza é a única mudança nos tokens recebidos; precisa do ok do Leandro.

### Onde a marca aparece

| Elemento | Visual |
|---|---|
| Topo e menu | fundo marinho, texto branco; aba ativa com sublinhado dourado |
| Botão principal (um por tela) | fundo marinho, texto branco |
| Botão secundário | contorno marinho, texto marinho |
| Selos de ação | Focar: dourado com texto marinho · Requalificar: contorno bronze com texto bronze escuro · Desistir: marfim com texto marinho e ícone |
| Score | número em Libre Baskerville; barra com os 4 componentes nas cores `comp-*` |
| Cartões e painel lateral | marfim, borda dourado claro |
| Gráficos do manager | marinho, bronze, dourado médio, cinza |

O tema é só claro: a decisão pede fundo branco.

### Regra que o build confere

- É proibido hex, `rgb()`, `hsl()` ou tamanho de fonte solto em componente. Isso vale também para os valores avulsos do Tailwind (`text-[#…]`, `text-[13px]`, `bg-[rgb…]`).
- Uma regra do ESLint (`no-restricted-syntax` sobre literais e `className`) e o script `npm run check:tokens` falham se encontrarem algum desses em `src/`, com exceção de `src/tema/`.
- Nenhuma cor sem significado fica de fora do tema: se a tela precisa de uma cor nova, ela entra primeiro em `tema.css`.

## UI e UX ultra simples (decisão 19)

| Tela | Ação principal (a única com botão marinho) |
|---|---|
| Quem é você? | Entrar como o usuário escolhido |
| Meu dia | Abrir o deal nº 1 (os outros são cartões clicáveis, sem botão de destaque) |
| Detalhe do deal | Registrar a ação sugerida pelo score (Liguei, Requalificar ou Encerrar), conforme o caso |
| Visão do time | Abrir o dia do vendedor com mais valor esfriando |
| Deals | Buscar |
| Limpeza | Encerrar os N deals selecionados |

- Sem jargão: "Em negociação", não "Engaging"; "valor esperado", não "EV"; "empresa", não "account".
- Nenhum erro cru e nenhum dado bruto na tela. Todo erro vira uma frase simples com o próximo passo ("Não foi possível salvar. Confira a conexão e tente de novo.").
- O que é técnico fica atrás de **Ver detalhes**: id do deal, código para suporte (correlation_id), execução do score e fonte dos dados.
- **Nenhuma tela sem os três estados.** Carregando: `loading.tsx` com esqueleto do layout final. Vazio: frase que diz o que fazer. Erro: `error.tsx` com a frase e o botão "Tentar de novo". O componente `Estado.tsx` padroniza os três.

## Árvore proposta

```
solution/app/
  package.json            scripts: dev, build, start, lint, typecheck, test, e2e, check:tokens, check:bundle, dados
  package-lock.json       commitado
  .nvmrc                  versão do Node (também em "engines")
  tsconfig.json           "strict": true, "noUncheckedIndexedAccess": true
  next.config.ts
  postcss.config.mjs      @tailwindcss/postcss
  eslint.config.mjs       inclui a regra de tokens
  vitest.config.ts
  playwright.config.ts    sobe `next start` no modo reserva (sem banco) e roda os caminhos críticos
  .gitignore              node_modules/, .next/, .env*.local, coverage/, playwright-report/, test-results/
  .gitattributes          fim de linha LF
  .env.example            nomes das variáveis, sem valores
  COMO-RODAR.md
  DESENHO-ACOES.md
  DESENHO-NEXT.md

  data/
    deals_scored.json     cópia do arquivo oficial (reserva somente leitura)
  sample/
    deals_scored.sample.json, gerar_sample.py
  scripts/
    dados.mjs             copia ../data/scored/deals_scored.json para data/ e confere o formato
    check-tokens.mjs      procura hex, rgb, hsl e tamanho de fonte solto fora de src/tema/
    check-bundle.mjs      lê o resultado do build e falha se a primeira carga passar de 300 kB gzip
  supabase/
    migrations/           0001_core … 0005_system, 0006_guardas, 0007_funcoes (ver DESENHO-ACOES.md)
  prototipo-html/         o app estático atual, como referência

  src/
    tema/
      tema.css            o único arquivo de tema (DES-01)
      fontes.ts           Libre Baskerville e Manrope via next/font
    app/
      layout.tsx          topo marinho (usuário + Trocar perfil), abas por papel, aviso de modo reserva
      globals.css         @import "tailwindcss"; @import "../tema/tema.css"; estilos de base
      page.tsx            "Quem é você?": vendedor, manager ou admin, depois o usuário
      vendedor/[nome]/page.tsx   Meu dia
      time/page.tsx              Visão do time (manager) ou geral (admin), com ?regiao=&manager=
      deals/page.tsx             Deals do usuário (busca, filtros, ordenação, encerrados)
      limpeza/page.tsx           Limpeza do pipeline em lote
      loading.tsx, error.tsx, not-found.tsx   em cada rota que carrega dados
      api/
        health/route.ts                GET: app, banco e fonte dos dados
        perfil/route.ts                POST (escolher) e DELETE (trocar perfil)
        acoes/route.ts                 POST registrar
        acoes/[id]/route.ts            PATCH desfazer
        deals/[id]/route.ts            PATCH estágio e empresa
        deals/[id]/encerrar/route.ts   POST ganho ou perdido
        limpeza/route.ts               POST encerramento em lote (até 100)
    components/
      BarraScore.tsx      barra dividida pelos componentes (servidor)
      CartaoDeal.tsx      cartão do top 5
      ListaMini.tsx       requalificar / desistir
      TabelaDeals.tsx     tabela com ordenação (navegador)
      Filtros.tsx         região, manager e vendedor no link; só os que o papel usa (navegador)
      EscolhaPerfil.tsx   os três papéis e a lista de config_usuarios (navegador)
      PerfilTopo.tsx      quem está usando + Trocar perfil
      DetalheDeal.tsx     painel lateral, aberto por ?deal=ID (navegador)
      BotoesAcao.tsx      Liguei / Requalifiquei / Desisti / Desfazer (navegador)
      EditarDeal.tsx      avançar estágio, escolher empresa, encerrar ganho/perdido (navegador)
      HistoricoDeal.tsx   linha do tempo lida da auditoria
      ConfirmarLote.tsx   confirmação da limpeza com a quantidade (navegador)
      VerDetalhes.tsx     área recolhida para o que é técnico
      Estado.tsx          carregando, vazio e erro padronizados
    lib/                  funções puras, sem I/O, todas testadas
      contrato.ts         tipos e schemas (zod): deals_scored.json e corpo de cada rota
      selecao.ts          top 5, requalificar, desistir, encerrados
      agregacoes.ts       números do time e por vendedor
      escopo.ts           o que cada papel vê (vendedor, time, tudo)
      estagios.ts         transições aceitas; reabrir só manager/admin
      usuarios.ts         lista de usuários a partir do JSON (modo reserva, mesmos ids)
      texto.ts            rótulos sem jargão, dinheiro, datas, plural, frases de erro
      config.ts           modo banco disponível ou não
    server/               só roda no servidor (import "server-only")
      fonte.ts            escolhe o modo (banco ou reserva) e devolve sempre o mesmo tipo Pipeline
      fonte-banco.ts      lê core_* + score_* + acao_* (tempo máximo de 3 s)
      fonte-arquivo.ts    lê e valida o deals_scored.json; cai no exemplo se faltar
      usuario.ts          lê o cookie e busca o usuário pela chave; volta para a escolha se faltar
      supabase.ts         cliente com a service role
      escrita.ts          chama as funções do banco com usuario_id e correlation_id; traduz 409/422/503
      correlacao.ts       gera o correlation_id e devolve no cabeçalho x-correlation-id
      log.ts              uma linha JSON por pedido

  tests/
    unit/                 Vitest
      contrato.test.ts    o exemplo e o arquivo oficial passam no schema; corpos inválidos recusados
      fontes.test.ts      o mesmo conjunto de deals lido pelo banco (simulado) e pelo arquivo dá o mesmo Pipeline
      selecao.test.ts     top 5 completa com requalificar; vendedor sem deals; encerrados fora do foco
      agregacoes.test.ts
      escopo.test.ts      vendedor vê o próprio, manager o time, admin tudo
      estagios.test.ts    transições válidas e inválidas; reabrir por papel
      usuarios.test.ts    lista do modo reserva com os mesmos ids do banco
      texto.test.ts       nenhuma mensagem de erro sem próximo passo
    e2e/                  Playwright: os caminhos críticos
      escolher-perfil.spec.ts   vendedor, manager e admin chegam à tela inicial certa
      ver-o-dia.spec.ts         top 5 com motivos; o detalhe abre e explica o score
      registrar-acao.spec.ts    Liguei → selo na tela → Desfazer (com banco de teste; no modo reserva, confere que os botões somem)
      limpar-pipeline.spec.ts   selecionar, confirmar a quantidade, encerrados saem da lista (com banco de teste)
      acessibilidade.spec.ts    @axe-core/playwright sem violações AA nas 5 telas
    banco/                (opcional, só com credenciais de teste) auditoria gravada em cada escrita,
                          DELETE recusado, conflito de versão vira 409
```

## Backend: saúde e logs

- **`GET /api/health`:** responde `200` com `{ "app": "ok", "banco": "ok" | "indisponivel" | "nao_configurado", "fonte": "banco" | "arquivo", "execucao_score": "2017-12-31", "versao": "<commit>" }`. Ele faz um `select 1` no banco com tempo máximo de 2 s e não expõe chave nem mensagem crua de erro. O status é `503` só se o próprio app não conseguir ler nem a reserva.
- **Logs:** `src/server/log.ts` escreve uma linha JSON por pedido: `{ momento, nivel, correlation_id, rota, metodo, status, duracao_ms, usuario_id, modo }`. Nunca vão para o log corpo de pedido, chave ou nota escrita pelo usuário. A Vercel guarda esses logs, e o `correlation_id` liga o log à linha de `system_auditoria`.

## Desempenho

- As páginas são renderizadas no servidor e mandam ao navegador só o que mostram. O "Meu dia" carrega os deals de um vendedor, não os 2.089.
- Os componentes interativos (painel, botões, filtros, tabela) são os únicos `"use client"`.
- Fontes por `next/font`, com `display: swap` e só os pesos usados.
- `check:bundle` falha acima de 300 kB gzip na primeira carga. O LCP abaixo de 2 s é medido pelo Lighthouse (Playwright) na tela "Meu dia" contra o build de produção.

## Dependências

- **Produção:** `next@16`, `react@19`, `react-dom@19`, `zod`, `@supabase/supabase-js` (só no servidor).
- **Desenvolvimento:** `typescript@5.9`, `tailwindcss@4`, `@tailwindcss/postcss`, `@types/node`, `@types/react`, `eslint`, `eslint-config-next`, `vitest`, `@playwright/test`, `@axe-core/playwright`.
- Sem biblioteca de componentes: os componentes são poucos e seguem o tema.

## De onde vêm os dados

- **Modo banco (principal):** deals, notas, ações e usuários vêm do Supabase. Detalhes em [DESENHO-ACOES.md](DESENHO-ACOES.md).
- **Modo reserva:** sem credenciais ou com o banco fora, o app lê `app/data/deals_scored.json` (cópia do arquivo oficial, gerada por `npm run dados` e commitada) ou, na falta dele, o exemplo. A tela vira somente leitura e avisa.
- Por que commitar a cópia: a Vercel publica a partir de `solution/app` e não depende de enxergar a pasta de fora; o build fica previsível. O `prebuild` só avisa se a cópia estiver diferente da origem.
- As telas recebem o mesmo tipo `Pipeline` nos dois modos e não sabem de onde ele veio; a fonte aparece em "Ver detalhes".

## Telas e fluxos

| Protótipo (`#hash`) | Next (rota) |
|---|---|
| `#dia` sem vendedor ("Quem é você?") | `/` (vendedor, manager ou admin) |
| `#dia?vendedor=Anna+Snelling` | `/vendedor/anna-snelling` |
| `#time?manager=...` | `/time?manager=...` |
| `#todos?regiao=West` | `/deals?regiao=West` |
| painel do deal | `?deal=FZWU2I30` em qualquer rota (agora com edição e histórico) |
| (novo) | `/limpeza` |

| Papel | Abre em | Abas |
|---|---|---|
| Vendedor | `/vendedor/<o próprio>` | Meu dia, Meus deals, Limpeza |
| Manager | `/time?manager=<o próprio>` | Time, Deals do time, Limpeza (o "Meu dia" de cada vendedor abre pelo quadro do time) |
| Admin | `/time` | Visão geral, Todos os deals, Limpeza |

As abas e os filtros seguem o papel. O servidor não bloqueia links de fora do escopo (decisão 16); a tela só não os oferece.

## Variáveis de ambiente

| Variável | Onde é usada | Obrigatória? |
|---|---|---|
| `SUPABASE_URL` | `src/server/` | Só para o modo banco |
| `SUPABASE_SERVICE_ROLE_KEY` | `src/server/` | Só para o modo banco |

- Os parâmetros (execução ativa, data de corte das ações, limite por minuto) ficam em `config_parametros`.
- Nenhuma variável é pública: o navegador nunca fala com o Supabase.
- Sem as variáveis, `npm ci && npm run dev` abre o app completo (usuários, telas e filtros) no modo reserva, somente leitura.

## Pronto para entregar quando

- `npm run typecheck`, `npm run lint`, `npm run check:tokens`, `npm test`, `npm run build`, `npm run check:bundle` e `npm run e2e` passam sem erro.
- Cada tela foi vista nos três estados (carregando, vazio e erro).
- Fim de linha LF (`.gitattributes`).

## Decisões em aberto

1. Confirmar `solution/app/` como raiz do projeto Next (recomendado).
2. Commitar a cópia de `deals_scored.json` dentro do app (recomendado) ou ligar na Vercel a opção de incluir arquivos fora da raiz.
3. Aprovar o cinza de texto `#66727c` no lugar de `#6f7c87`, que não passa no WCAG AA para texto pequeno (4,3:1 contra 4,5:1 exigido). O `#6f7c87` continua para bordas, ícones e texto grande.
4. As decisões em aberto de [DESENHO-ACOES.md](DESENHO-ACOES.md).
