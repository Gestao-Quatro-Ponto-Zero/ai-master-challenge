# Desenho: estrutura do app em Next.js

> Proposta para decisão. Nada disto está construído.
> Usuários, operação do pipeline, banco e auditoria em [DESENHO-ACOES.md](DESENHO-ACOES.md).
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
  supabase/
    migrations/
      0001_core.sql                 core_* (dados do CRM)
      0002_config.sql               config_usuarios, config_parametros
      0003_score.sql                score_*
      0004_acao.sql                 acao_registros
      0005_system.sql               system_auditoria, system_eventos
      0006_guardas.sql              gatilho de auditoria, bloqueio de DELETE, revoke delete/truncate, RLS
      0007_funcoes.sql              acao_registrar, acao_desfazer, core_atualizar_deal, core_encerrar_deal, core_encerrar_lote
  prototipo-html/         o app estático atual, como referência

  src/
    app/
      layout.tsx          topo (usuário + Trocar perfil), abas por papel, aviso de modo reserva
      globals.css         os mesmos tokens visuais do protótipo (claro e escuro)
      page.tsx            "Quem é você?": vendedor, manager ou admin, depois o usuário
      vendedor/[nome]/page.tsx   Meu dia
      time/page.tsx              Visão do time (manager) ou geral (admin), com ?regiao=&manager=
      deals/page.tsx             Deals do usuário (busca, filtros, ordenação, encerrados)
      limpeza/page.tsx           Limpeza do pipeline em lote
      not-found.tsx, error.tsx, loading.tsx   estados vazio, erro e carregando
      api/
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
      Filtros.tsx         região, manager, vendedor no link; só os que o papel usa (navegador)
      EscolhaPerfil.tsx   os três papéis e a lista de config_usuarios (navegador)
      PerfilTopo.tsx      quem está usando + Trocar perfil
      DetalheDeal.tsx     painel lateral, aberto por ?deal=ID (navegador)
      BotoesAcao.tsx      Liguei / Requalifiquei / Desisti / Desfazer (navegador)
      EditarDeal.tsx      avançar estágio, escolher empresa, encerrar ganho/perdido (navegador)
      HistoricoDeal.tsx   linha do tempo lida da auditoria
      ConfirmarLote.tsx   confirmação da limpeza com a quantidade (navegador)
      Estado.tsx          vazio e erro padronizados (com o código para suporte)
    lib/                  funções puras, sem I/O, todas testadas
      contrato.ts         tipos e schemas (zod): deals_scored.json e corpo de cada rota
      selecao.ts          top 5, requalificar, desistir, encerrados
      agregacoes.ts       números do time e por vendedor
      escopo.ts           o que cada papel vê (vendedor, time, tudo)
      estagios.ts         transições aceitas; reabrir só manager/admin
      usuarios.ts         lista de usuários a partir do JSON (modo reserva, mesmos ids)
      texto.ts            rótulos, dinheiro, datas, plural, mensagens de erro
      config.ts           modo banco disponível ou não
    server/               só roda no servidor (import "server-only")
      fonte.ts            escolhe o modo (banco ou reserva) e devolve sempre o mesmo tipo Pipeline
      fonte-banco.ts      lê core_* + score_* + acao_* (tempo máximo de 3 s)
      fonte-arquivo.ts    lê e valida o deals_scored.json; cai no exemplo se faltar
      usuario.ts          lê o cookie e busca o usuário pela chave; volta para a escolha se faltar
      supabase.ts         cliente com a service role
      escrita.ts          chama as funções do banco com usuario_id e correlation_id; traduz 409/422/503
      correlacao.ts       gera o correlation_id e devolve no cabeçalho x-correlation-id

  tests/
    contrato.test.ts      o exemplo e o arquivo oficial passam no schema; corpos inválidos recusados
    fontes.test.ts        o mesmo conjunto de deals lido pelo banco (simulado) e pelo arquivo dá o mesmo Pipeline
    selecao.test.ts       top 5 completa com requalificar; vendedor sem deals; encerrados fora do foco
    agregacoes.test.ts
    escopo.test.ts        vendedor vê o próprio, manager o time, admin tudo
    estagios.test.ts      transições válidas e inválidas; reabrir por papel
    usuarios.test.ts      lista do modo reserva com os mesmos ids do banco
    banco/                (opcional, roda só com credenciais de teste) auditoria gravada em cada escrita,
                          DELETE recusado, conflito de versão vira 409
```

## Dependências (mínimas)

- **Produção:** `next`, `react`, `react-dom`, `zod`, `@supabase/supabase-js` (só no servidor).
- **Desenvolvimento:** `typescript`, `@types/node`, `@types/react`, `eslint`, `eslint-config-next`, `vitest`.
- Sem biblioteca de componentes nem Tailwind: o CSS do protótipo já resolve e mantém a mesma identidade.

## De onde vêm os dados

- **Modo banco (principal):** deals, notas, ações e usuários vêm do Supabase. Detalhes em [DESENHO-ACOES.md](DESENHO-ACOES.md).
- **Modo reserva:** sem credenciais ou com o banco fora, o app lê `app/data/deals_scored.json` (cópia do arquivo oficial, gerada por `npm run dados` e commitada) ou, na falta dele, o exemplo. A tela vira somente leitura e avisa.
- Por que commitar a cópia: a Vercel publica a partir de `solution/app` e não depende de enxergar a pasta de fora; o build fica previsível. O `prebuild` só avisa se a cópia estiver diferente da origem.
- As telas recebem o mesmo tipo `Pipeline` nos dois modos e não sabem de onde ele veio; só o rodapé mostra a fonte.
- A leitura acontece no servidor. Cada página recebe só o que mostra: o "Meu dia" de um vendedor não manda os 2.089 deals para o navegador.

## Telas e fluxos

| Protótipo (`#hash`) | Next (rota) |
|---|---|
| `#dia` sem vendedor ("Quem é você?") | `/` (vendedor, manager ou admin) |
| `#dia?vendedor=Anna+Snelling` | `/vendedor/anna-snelling` |
| `#time?manager=...` | `/time?manager=...` |
| `#todos?regiao=West` | `/deals?regiao=West` |
| painel do deal | `?deal=FZWU2I30` em qualquer rota (agora com edição e histórico) |
| (novo) | `/limpeza` |

Tela inicial e abas por papel:

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

- Os parâmetros (execução ativa, data de corte das ações, limite por minuto) ficam em `config_parametros`, não em variáveis.
- Nenhuma variável é pública: o navegador nunca fala com o Supabase.
- Sem as variáveis, `npm ci && npm run dev` abre o app completo (usuários, telas e filtros) no modo reserva, somente leitura.

## Qualidade

- `npm run typecheck`, `npm run lint` e `npm test` sem erro antes de cada entrega.
- Todo corpo de rota validado com zod; erro sempre com frase simples, próximo passo e código para suporte (correlation_id).
- Fim de linha LF, garantido por `.gitattributes` na pasta.
- Acessibilidade herdada do protótipo: foco visível, navegação por teclado no painel e nas tabelas, contraste nos dois temas.

## Decisões em aberto

1. Confirmar `solution/app/` como raiz do projeto Next (recomendado).
2. Commitar a cópia de `deals_scored.json` dentro do app (recomendado) ou ligar na Vercel a opção de incluir arquivos fora da raiz.
3. As decisões em aberto de [DESENHO-ACOES.md](DESENHO-ACOES.md).
