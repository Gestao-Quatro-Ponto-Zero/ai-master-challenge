# Desenho: estrutura do app em Next.js

> Proposta para decisão. Nada disto está construído.
> Identidade (decisão 12): sem login; escolha de perfil (vendedor, manager ou admin) guardada em cookie. Detalhes em [DESENHO-ACOES.md](DESENHO-ACOES.md).
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
    migrations/           um arquivo por domínio (DB-01): 0001_core, 0002_score, 0003_config_system, 0004_acao
  prototipo-html/         o app estático atual, como referência

  src/
    app/
      layout.tsx          topo (perfil + Trocar perfil), abas por perfil, aviso de dados de exemplo
      globals.css         os mesmos tokens visuais do protótipo (claro e escuro)
      page.tsx            "Quem é você?": vendedor, manager ou admin, depois o nome
      vendedor/[nome]/page.tsx   Meu dia (vendedor: o próprio; manager: do time; admin: qualquer um)
      time/page.tsx              Visão do time (manager) ou geral (admin), com ?regiao=&manager=
      deals/page.tsx             Todos os deals do perfil (busca, filtros, ordenação)
      limpeza/page.tsx           Limpeza do pipeline do perfil
      not-found.tsx, error.tsx, loading.tsx   estados vazio, erro e carregando
      api/
        perfil/route.ts          POST (escolher) e DELETE (trocar perfil)
        acoes/route.ts           GET e POST
    components/
      BarraScore.tsx      barra dividida pelos componentes (servidor)
      CartaoDeal.tsx      cartão do top 5
      ListaMini.tsx       requalificar / desistir
      TabelaDeals.tsx     tabela com ordenação (navegador)
      Filtros.tsx         região, manager, vendedor no link; só os que o perfil permite (navegador)
      EscolhaPerfil.tsx   os três papéis e a lista de nomes (navegador)
      PerfilTopo.tsx      quem está usando + Trocar perfil
      DetalheDeal.tsx     painel lateral, aberto por ?deal=ID (navegador)
      BotoesAcao.tsx      Liguei / Requalifiquei / Desisti (navegador)
      Estado.tsx          vazio e erro padronizados
    lib/                  funções puras, sem I/O, todas testadas
      contrato.ts         tipos e schema (zod) do deals_scored.json
      selecao.ts          top 5, requalificar, desistir
      agregacoes.ts       números do time e por vendedor
      perfil.ts           papéis, nomes válidos do dataset, escopo de deals de cada perfil
      permissao.ts        quem pode gravar em qual deal; limite por minuto
      texto.ts            rótulos, dinheiro, datas, plural
      config.ts           registro de ações disponível ou não
    server/               só roda no servidor (import "server-only")
      fonte.ts            escolhe o modo (banco ou arquivo) e devolve sempre o mesmo tipo Pipeline
      fonte-banco.ts      lê core_* + score_* da execução ativa (tempo máximo de 3 s)
      fonte-arquivo.ts    lê e valida o deals_scored.json; cai no exemplo se faltar
      perfil.ts           lê e confere o cookie de perfil; redireciona para a escolha se faltar
      supabase.ts         cliente com a service role
      acoes.ts            ler e gravar em acao_registros, com as conferências
      eventos.ts          grava em system_eventos (recusas, quedas para o modo arquivo)

  tests/
    contrato.test.ts      o exemplo e o arquivo oficial passam no schema
    fontes.test.ts        o mesmo conjunto de deals lido pelo banco (simulado) e pelo arquivo dá o mesmo Pipeline
    selecao.test.ts       top 5 completa com requalificar; vendedor sem deals
    agregacoes.test.ts
    perfil.test.ts        nome inexistente recusado; escopo de vendedor, manager e admin
    permissao.test.ts     vendedor não grava no deal de outro; manager só no time; lote tudo ou nada
```

## Dependências (mínimas)

- **Produção:** `next`, `react`, `react-dom`, `zod`, `@supabase/supabase-js` (só no servidor).
- **Desenvolvimento:** `typescript`, `@types/node`, `@types/react`, `eslint`, `eslint-config-next`, `vitest`.
- Sem biblioteca de componentes nem Tailwind: o CSS do protótipo já resolve e mantém a mesma identidade.

## De onde vêm os dados

- O score oficial é gerado em Python em `solution/data/scored/deals_scored.json`.
- `npm run dados` copia esse arquivo para `app/data/deals_scored.json` e valida o formato com o schema. A cópia é commitada.
- Por que commitar a cópia: a Vercel publica a partir de `solution/app` e não depende de enxergar a pasta de fora; o build fica previsível.
- O `prebuild` só avisa se a cópia estiver diferente da origem; ele não falha.
- Se a cópia não existir, `server/fonte-arquivo.ts` usa `sample/deals_scored.sample.json` e o topo mostra o aviso de dados de exemplo.
- **Dois modos** (detalhe em [DESENHO-ACOES.md](DESENHO-ACOES.md)): com credenciais e banco no ar, deals e notas vêm de `core_*` e `score_*`; sem isso, vêm do arquivo acima. As telas recebem o mesmo tipo `Pipeline` nos dois casos e não sabem de onde ele veio; só o rodapé mostra a fonte.
- A leitura acontece no servidor. Cada página recebe só o que mostra: o "Meu dia" de um vendedor não manda os 2.089 deals para o navegador.

## Telas e fluxos (iguais ao protótipo)

| Protótipo (`#hash`) | Next (rota) |
|---|---|
| `#dia` sem vendedor ("Quem é você?") | `/` (agora com vendedor, manager ou admin) |
| `#dia?vendedor=Anna+Snelling` | `/vendedor/anna-snelling` |
| `#time?manager=...` | `/time?manager=...` |
| `#todos?regiao=West` | `/deals?regiao=West` |
| painel do deal | `?deal=FZWU2I30` em qualquer rota (o link abre o detalhe) |
| (novo) | `/limpeza` |

Tela inicial e abas por perfil:

| Perfil | Abre em | Abas |
|---|---|---|
| Vendedor | `/vendedor/<o próprio>` | Meu dia, Meus deals, Limpeza |
| Manager | `/time?manager=<o próprio>` | Time, Deals do time, Limpeza (o "Meu dia" de cada vendedor abre pelo quadro do time) |
| Admin | `/time` | Visão geral, Todos os deals, Limpeza |

Um link para fora do escopo do perfil (ex.: vendedor abrindo `/vendedor/outro-nome`) volta para a tela inicial dele.

## Variáveis de ambiente

| Variável | Onde é usada | Obrigatória? |
|---|---|---|
| `SUPABASE_URL` | `src/server/` | Só para o modo banco (ler do banco e registrar ações) |
| `SUPABASE_SERVICE_ROLE_KEY` | `src/server/` | Só para o modo banco |

Os parâmetros da demonstração (execução ativa, data de corte das ações, limite por minuto) ficam em `config_parametros`, não em variáveis.

Nenhuma variável é pública: sem login, o navegador não fala com o Supabase. Sem elas, `npm ci && npm run dev` abre o app completo (perfis, telas e filtros) no modo arquivo, só leitura.

## Qualidade

- `npm run typecheck`, `npm run lint` e `npm test` sem erro antes de cada entrega.
- Fim de linha LF, garantido por `.gitattributes` na pasta.
- Acessibilidade herdada do protótipo: foco visível, navegação por teclado no painel e nas tabelas, contraste nos dois temas.

## Decisões em aberto

1. Confirmar `solution/app/` como raiz do projeto Next (recomendado).
2. Commitar a cópia de `deals_scored.json` dentro do app (recomendado) ou ligar na Vercel a opção de incluir arquivos fora da raiz.
3. As decisões em aberto de [DESENHO-ACOES.md](DESENHO-ACOES.md): modo banco, quem carrega `core_*` e `score_*`, onde ficam as migrações, se o admin grava e quem faz a limpeza.
