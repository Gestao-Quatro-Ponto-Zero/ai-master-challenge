# Desenho: estrutura do app em Next.js

> Proposta para decisão. Nada disto está construído.
> O app atual em HTML/JS (`index.html`, `app.js`, `styles.css`) vira referência de telas e fluxos e vai para `prototipo-html/`.

## Onde fica o projeto Next

**Recomendado: o próprio `solution/app/` vira o projeto Next.**

```bash
cd submissions/leandro-mallet/solution/app
npm ci
npm run dev        # http://localhost:3000
```

- O Next fica separado da parte em Python (`data/`, `analysis/`, `scoring/`), e o dono da pasta continua o mesmo.
- Alternativa descartada: o Next na raiz de `solution/`. O Next trataria a pasta `solution/app/` atual como o roteador dele, e o `package.json` ficaria misturado com o pipeline em Python.
- Vercel: Root Directory = `submissions/leandro-mallet/solution/app`.

## Árvore proposta

```
solution/app/
  package.json            scripts: dev, build, start, lint, typecheck, test, dados
  package-lock.json       commitado
  .nvmrc                  versão do Node (também em "engines")
  tsconfig.json           "strict": true, "noUncheckedIndexedAccess": true
  next.config.ts
  eslint.config.mjs
  vitest.config.ts
  .gitignore              node_modules/, .next/, .env*.local, coverage/
  .env.example            nomes das variáveis, sem valores
  COMO-RODAR.md
  DESENHO-ACOES.md
  DESENHO-NEXT.md

  data/
    deals_scored.json     cópia do arquivo oficial (ver "De onde vêm os dados")
  sample/
    deals_scored.sample.json, gerar_sample.py
  scripts/
    dados.mjs             copia ../data/scored/deals_scored.json para data/ e confere o formato
  supabase/
    migrations/0001_acoes.sql
  prototipo-html/         o app estático atual, como referência

  src/
    middleware.ts         renova a sessão do Supabase; não roda sem credenciais
    app/
      layout.tsx          topo, abas, filtros, aviso de dados de exemplo
      globals.css         os mesmos tokens visuais do protótipo (claro e escuro)
      page.tsx            "Quem é você?" (escolha do vendedor)
      vendedor/[nome]/page.tsx   Meu dia
      time/page.tsx              Visão do manager (?regiao=&manager=)
      deals/page.tsx             Todos os deals (busca, filtros, ordenação)
      limpeza/page.tsx           Limpeza do pipeline (só com login)
      entrar/page.tsx            Login com conta de demonstração
      not-found.tsx, error.tsx, loading.tsx   estados vazio, erro e carregando
      api/
        acoes/route.ts           GET e POST
        sessao/route.ts          POST e DELETE
    components/
      BarraScore.tsx      barra dividida pelos componentes (servidor)
      CartaoDeal.tsx      cartão do top 5
      ListaMini.tsx       requalificar / desistir
      TabelaDeals.tsx     tabela com ordenação (navegador)
      Filtros.tsx         região, manager, vendedor no link (navegador)
      DetalheDeal.tsx     painel lateral, aberto por ?deal=ID (navegador)
      BotoesAcao.tsx      Liguei / Requalifiquei / Desisti (navegador)
      Estado.tsx          vazio e erro padronizados
    lib/                  funções puras, sem I/O, todas testadas
      contrato.ts         tipos e schema (zod) do deals_scored.json
      selecao.ts          top 5, requalificar, desistir
      agregacoes.ts       números do time e por vendedor
      permissao.ts        quem pode gravar em qual deal; limite por minuto
      texto.ts            rótulos, dinheiro, datas, plural
      config.ts           registro de ações disponível ou não
    server/               só roda no servidor (import "server-only")
      dados.ts            lê e valida o JSON uma vez; cai no exemplo se faltar
      supabase.ts         cliente com a service role
      sessao.ts           sessão por cookie (@supabase/ssr)
      acoes.ts            ler e gravar ações, com as conferências

  tests/
    contrato.test.ts      o exemplo e o arquivo oficial passam no schema
    selecao.test.ts       top 5 completa com requalificar; vendedor sem deals
    agregacoes.test.ts
    permissao.test.ts     vendedor não grava no deal de outro; manager só no time
```

## Dependências (mínimas)

- **Produção:** `next`, `react`, `react-dom`, `zod`, `@supabase/supabase-js`, `@supabase/ssr`.
- **Desenvolvimento:** `typescript`, `@types/node`, `@types/react`, `eslint`, `eslint-config-next`, `vitest`.
- Sem biblioteca de componentes nem Tailwind: o CSS do protótipo já resolve e mantém a mesma identidade.

## De onde vêm os dados

- O score oficial é gerado em Python em `solution/data/scored/deals_scored.json`.
- `npm run dados` copia esse arquivo para `app/data/deals_scored.json` e valida o formato com o schema. A cópia é commitada.
- Por que commitar a cópia: a Vercel publica a partir de `solution/app` e não depende de enxergar a pasta de fora; o build fica previsível.
- O `prebuild` só avisa se a cópia estiver diferente da origem; ele não falha.
- Se a cópia não existir, `server/dados.ts` usa `sample/deals_scored.sample.json` e o topo mostra o aviso de dados de exemplo.
- A leitura acontece no servidor. Cada página recebe só o que mostra: o "Meu dia" de um vendedor não manda os 2.089 deals para o navegador.

## Telas e fluxos (iguais ao protótipo)

| Protótipo (`#hash`) | Next (rota) |
|---|---|
| `#dia` sem vendedor | `/` |
| `#dia?vendedor=Anna+Snelling` | `/vendedor/anna-snelling` |
| `#time?manager=...` | `/time?manager=...` |
| `#todos?regiao=West` | `/deals?regiao=West` |
| painel do deal | `?deal=FZWU2I30` em qualquer rota (o link abre o detalhe) |
| (novo) | `/limpeza`, `/entrar` |

## Variáveis de ambiente

| Variável | Onde é usada | Obrigatória? |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | sessão e rotas | Só para registrar ações |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | sessão (cookie) | Só para registrar ações |
| `SUPABASE_SERVICE_ROLE_KEY` | `src/server/` | Só para registrar ações |

Sem nenhuma delas, `npm ci && npm run dev` abre o app completo em modo só leitura.

## Qualidade

- `npm run typecheck`, `npm run lint` e `npm test` sem erro antes de cada entrega.
- Fim de linha LF, garantido por `.gitattributes` na pasta.
- Acessibilidade herdada do protótipo: foco visível, navegação por teclado no painel e nas tabelas, contraste nos dois temas.

## Decisões em aberto

1. Confirmar `solution/app/` como raiz do projeto Next (recomendado).
2. Commitar a cópia de `deals_scored.json` dentro do app (recomendado) ou ligar na Vercel a opção de incluir arquivos fora da raiz.
3. As decisões de identidade e ações de [DESENHO-ACOES.md](DESENHO-ACOES.md).
