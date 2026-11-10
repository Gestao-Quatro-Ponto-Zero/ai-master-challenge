# G4 Sight: estrutura do app

> Descreve o app como ele está construído. A especificação das telas está em [ESPEC-TELAS.md](ESPEC-TELAS.md); o banco, em `solution/db/`.

## Stack

| Camada | Escolha |
|---|---|
| Frontend | Next.js 16 (App Router), React 19, TypeScript 5.9 `strict` (com `noUncheckedIndexedAccess`), Tailwind CSS 4 |
| Backend | Route Handlers no runtime Node.js, zod em toda entrada |
| Dados | Postgres no Supabase (`@supabase/supabase-js`, só no servidor); reserva somente leitura em arquivo (`data/`) |
| Publicação | Vercel, com a raiz em `submissions/leandro-mallet/solution/app` |

```bash
npm ci
npm run dev        # http://localhost:3010
```

## Árvore

```
solution/app/
  package.json, package-lock.json
  next.config.ts          inclui data/ no pacote publicado (outputFileTracingIncludes)
  tsconfig.json, eslint.config.mjs, postcss.config.mjs, vitest.config.ts
  .gitignore              node_modules/, .next/, .env*.local
  COMO-RODAR.md, ESPEC-TELAS.md, DESENHO-NEXT.md, DESENHO-ACOES.md, DESENHO-CRM.md

  data/
    base.json             8.800 deals, 85 contas, 35 vendedores e 7 produtos (gerado dos CSVs limpos)
    deals_scored.json     notas do score, quando existir (opcional)
  scripts/
    dados.mjs             gera data/base.json a partir de solution/data/clean
    espelhar-para-drive.ps1   copia o código da cópia de trabalho para esta pasta

  src/
    tema/
      tema.css            ÚNICO arquivo com cores, fontes, tamanhos, raios, sombras e animações
      fontes.ts           Libre Baskerville e Manrope via next/font
    app/
      layout.tsx          topo, aviso de somente leitura, provedores e o modal do deal
      page.tsx            "Quem é você?" (escolha de perfil)
      painel/             Painel: números, funil, Prioridades do dia e quadro por vendedor
      pipeline/           Pipeline: duas colunas, cartões e filtro livre
      leads/              Leads: tabela, lote e a aba Contas (?aba=contas)
      error.tsx, not-found.tsx, */loading.tsx   estados de erro, vazio e carregando
      api/                rotas (tabela abaixo)
    components/
      Topo, TopoCliente   marca, abas e "Trocar perfil"
      EscolhaPerfil       vendedor, manager ou admin
      Prioridades         lista do dia, ✓ com registro obrigatório e ✗
      Funil               situação do funil (quantidade | valor)
      Quadro              colunas do Pipeline, cartão e arraste
      Estagio             mudança de estágio (uma implementação para arraste, seletor e modal)
      ModalDeal           linha do tempo, nota, comentários, tags e contato (?deal=ID)
      TabelaLeads         tabela com seleção e ações em lote
      NovoLead            cadastro de lead
      Contas              lista das empresas, ficha (?conta=Nome) e cadastro
      Filtros, FiltrosEquipe   filtro livre com etiquetas; seletores de região, manager e vendedor
      Avisos              avisos com "Desfazer" e recarga dos dados
      Dialogo, Estado, Nota    peças comuns (diálogo, selo de tag, vazio/erro/esqueleto, barra da nota, ícone)
    lib/                  funções puras, sem I/O
      tipos.ts, config.ts, calculos.ts, painel.ts, cliente.ts
      filtro/             etiquetas.ts, interpretar.ts (frase → etiquetas), aplicar.ts
    server/               só roda no servidor (import "server-only")
      banco.ts            cliente do Supabase (service_role só aqui), tradução de erros e correlation_id
      repositorio.ts      a única porta das telas: escolhe banco ou reserva e faz as contas das telas
      repositorio-banco.ts    leitura pela view e pelas tabelas; escrita só pelas functions do banco
      repositorio-arquivo.ts  reserva em arquivo (somente leitura; memória só com G4_ESCRITA_EM_MEMORIA=1)
      fonte.ts            lê data/base.json e data/deals_scored.json
      sessao.ts           perfil escolhido (cookie)
      rota.ts             base das rotas: usuário, limite por IP, correlation_id, zod, erro em frase simples
      parametros.ts       lê e valida os filtros do link
```

## Rotas de API

| Rota | Faz |
|---|---|
| `GET /api/health` | saúde do app e fonte dos dados |
| `POST` / `DELETE /api/perfil` | escolher / trocar o perfil (o usuário "sistema" nunca é aceito) |
| `POST /api/deals` | novo lead |
| `GET /api/deals/[id]` | detalhe para o modal |
| `POST /api/deals/[id]/estagio` | mudar estágio (arraste, seletor e modal) |
| `POST /api/deals/[id]/acoes` | Liguei, Requalifiquei, Desisti |
| `POST /api/deals/[id]/comentarios` | postar comentário |
| `DELETE /api/comentarios/[id]` | apagar comentário (remoção lógica) |
| `POST /api/deals/[id]/contato` | adicionar o contato principal |
| `POST` / `DELETE /api/deals/[id]/tags` | aplicar / remover tag |
| `GET` / `POST /api/tags` | listar / criar tag (manager e admin) |
| `POST /api/prioridades` | ✓ (tipo de atividade e comentário obrigatórios) ou ✗ |
| `POST /api/prioridades/mais` | puxar mais 5 |
| `POST /api/lotes` | ação em lote (marcados ou todos os do filtro, até 500) |
| `GET /api/contas/[nome]` | ficha da empresa |
| `POST /api/contas` | criar ou editar empresa |
| `POST /api/desfazer` | desfazer uma mudança ou um lote |

Toda rota de escrita: valida a entrada com zod, tem limite por endereço de rede (60 por minuto, resposta 429 em frase simples), gera o `correlation_id` no servidor e o devolve em `x-correlation-id`, e responde erro sempre como `{ erro, codigo }`.

## Marca visual (DES-01, FE-03)

- Fundo branco; azul-marinho `#001f35` no topo, no botão principal e nos títulos; dourado `#c9a96e` na aba ativa, nos selos e nos destaques.
- Títulos em Libre Baskerville e texto em Manrope.
- Tudo sai de `src/tema/tema.css`. Uma regra do ESLint recusa cor ou tamanho de fonte solto fora desse arquivo.
- Contraste medido sobre branco: o dourado (2,2:1) nunca é cor de texto; o texto secundário usa `#66727c` (4,9:1), um pouco mais escuro que o cinza da marca, para passar no WCAG AA.

## Dados: banco e reserva

- As telas só falam com `src/server/repositorio.ts`, que devolve os tipos de `src/lib/tipos.ts`.
- **Leitura no banco:** os deals do perfil vêm da view `core_deals_visao`, com o filtro do escopo aplicado no banco. Os abertos vêm com todas as colunas (ícone, nota, tags); os fechados, só com as colunas básicas, porque são a maioria e não têm ícone nem nota. Filtro, ordenação e números do Painel são calculados no servidor pelas funções puras de `src/lib/`, as mesmas da reserva.
- **Por que não as functions de leitura do banco:** `core_buscar_deals` leva cerca de 6 s e `core_painel_numeros` passa do tempo limite (8 s) no escopo do admin. Lendo a view direto, o Painel do admin (8.800 deals) abre em 3 a 4 s e o do vendedor em cerca de 1 s.
- **Escrita:** só pelas functions do banco (`core_mudar_estagio`, `acao_registrar`, `acao_marcar_prioridade`, `system_executar_lote`…), com `p_usuario_id` do perfil e `p_correlation_id` gerado na rota. O "Desfazer" chama a function inversa (`core_desfazer_alteracao`, `acao_desfazer`, `acao_restaurar_comentario`, `system_desfazer_lote`).
- **Erros do banco:** `GS400`–`GS429` viram a frase simples que o banco devolve; conflito de versão (`GS409`) diz quem alterou. Falha de rede ou tempo esgotado marca o banco como fora por 15 s.
- **Reserva:** banco fora ou não configurado = leitura de `data/base.json`, faixa de somente leitura e escrita recusada (503).
- Variáveis: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `G4_ESCRITA_EM_MEMORIA` e `G4_SOMENTE_LEITURA` (ver `.env.example`).

## Ainda não construído

- Importação de leads por CSV (desenhada em [DESENHO-CRM.md](DESENHO-CRM.md)).
- Editar o nome do deal e a empresa do deal pelo modal.
- Cadastrar e editar empresa com o banco ligado (falta a function no banco).
- Playwright nos caminhos críticos (o Vitest já cobre a reserva, as prioridades e o escopo da ficha da empresa).
