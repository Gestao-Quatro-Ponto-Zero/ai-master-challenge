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
  tsconfig.json, eslint.config.mjs, postcss.config.mjs, vitest.config.mts
  vercel.json             cron da rotina diária (06:00 UTC → /api/rotina/diaria)
  .env.example            as variáveis, sem valores
  .gitignore              node_modules/, .next/, .env*.local
  COMO-RODAR.md, ESPEC-TELAS.md, DESENHO-NEXT.md

  data/
    base.json             8.800 deals, 85 contas, 35 vendedores e 7 produtos (gerado dos CSVs limpos);
                          reserva sem banco, sem notas (as notas ficam no banco)
  scripts/
    dados.mjs             gera data/base.json a partir de solution/data/clean
    espelhar-para-drive.ps1   copia o código da cópia de trabalho para esta pasta

  src/
    tema/
      tema.css            ÚNICO arquivo com cores, fontes, tamanhos, raios, sombras e animações
      fontes.ts           Libre Baskerville e Manrope via next/font
    app/
      layout.tsx          topo, aviso de somente leitura, provedores e o modal do deal
      page.tsx            tela de login sem senha (Selecione o Perfil, Selecione o Usuário, Login)
      painel/             Painel: grade com 8 números, Prioridades do dia (20, bloco azul), funil de 5 etapas e quadro por vendedor
      pipeline/           Pipeline: cinco colunas (Novo lead, Atendimento, Em negociação, Fechado, Perdido), cartões e filtro livre
      leads/              Leads: tabela, lote e a aba Contas (?aba=contas)
      error.tsx, not-found.tsx, */loading.tsx   estados de erro, vazio e carregando
      api/                rotas (tabela abaixo)
    components/
      Topo, TopoCliente   marca, abas e "Trocar perfil"
      EscolhaPerfil       tela de login: perfil e usuário em listas suspensas (vendedores por time)
      Prioridades         lista do dia: 20 da meta à mostra; ✓ com registro obrigatório, ✗ e Contato hoje
      Funil               situação do funil em 5 etapas (quantidade | valor); barras na horizontal no celular
      Quadro              as 5 colunas do Pipeline, cartão e arraste
      Estagio             mudança de etapa (uma implementação para arraste, seletor e modal) e registro de atendimento
      ModalDeal           linha do tempo, Liguei/Requalifiquei/Desisti, comentários, tags e contato (?deal=ID)
      NotaExplicada       "Por que a nota é N": a conta, a barra por componente, os motivos e o FIT em % de conversão
      TabelaLeads         tabela com seleção e ações em lote
      LotesRecentes       lotes das últimas 24 horas, com "Desfazer este lote"
      NovoLead            cadastro de lead
      Contas              lista das empresas, ficha (?conta=Nome) e cadastro
      Filtros, FiltrosEquipe   filtro livre com etiquetas; seletores de região, manager e vendedor
      Avisos              avisos com "Desfazer" e recarga dos dados
      Dialogo, Estado, Nota    peças comuns (diálogo, selo de tag, vazio/erro/esqueleto, barra da nota, ícone)
      ui/                 objetos da interface, um conjunto só para todas as telas:
        Botao             3 níveis (primário navy, secundário branco com borda neutra, discreto), 40 px ou 32 px
        Campo             campo e área de texto com a altura do botão; rótulo e erro de formulário
        Seletor           lista estilizada no lugar do <select> nativo, por teclado; grupos opcionais; modo ação (estágio, + Tag)
        Etiqueta          uma forma, tons neutro, atenção, negativo, positivo e destaque
        BarraNota         barra fina, cor pela faixa, número em Manrope 600 tabular
        Superficie        painel, lista com divisória, cartão leve, alternador e caixa de marcar
        Icones            ícones em SVG (sem glifos)
        CartaoNumero      cartão de número do Painel: ícone na cor do grupo, número grande em Manrope, selo de variação (verde sobe, vermelho cai, cinza em 0%)
    lib/                  funções puras, sem I/O
      tipos.ts, config.ts, calculos.ts, painel.ts, cliente.ts
      desfazer.ts         formato do token do "Desfazer"
      lotes.ts            rótulos, prazo de 24 horas e quem vê cada lote
      prioridades.ts      contador e ordem das Prioridades do dia (a mesma da 0030) e a explicação do item
      relogio.ts          relógio do CRM (decisão 48): data de negócio = âncora + dias reais
      explicacaoNota.ts   a conta da nota, as partes e o FIT em % para "Por que a nota é N"
      score/              motor do lead score em TypeScript: regra.ts (FIT absoluto, HEAT, bônus, nota), movimentos.ts (redistribuição e repasse)
      etapas.ts           as 5 etapas da tela: Novo lead e Atendimento = Prospecting sem e com contato
      validacao.ts        frase específica para erro de campo na API
      filtro/             etiquetas.ts, interpretar.ts (frase → etiquetas), aplicar.ts
    server/               só roda no servidor (import "server-only")
      motor/              rotina diária do score: rotina.ts (transação, idempotência, rodada forçada, falha), motor-score.ts
                          (liga src/lib/score ao banco; cada repasse num savepoint), conexao.ts (DATABASE_URL_ROTINA),
                          autorizacao.ts (CRON_SECRET), contrato.ts e instalado.ts
      banco.ts            cliente do Supabase (service_role só aqui), tradução de erros e correlation_id
      repositorio.ts      a única porta das telas: escolhe banco ou reserva e faz as contas das telas
      repositorio-banco.ts    leitura pela view e pelas tabelas; escrita só pelas functions do banco
      repositorio-arquivo.ts  reserva em arquivo (somente leitura; memória só com G4_ESCRITA_EM_MEMORIA=1)
      fonte.ts            lê data/base.json (e data/deals_scored.json, se existir; hoje não existe)
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
| `POST /api/deals/[id]/estagio` | mudar etapa (arraste, seletor e modal) |
| `POST /api/deals/[id]/atendimento` | registrar atendimento (tipo e comentário obrigatórios): leva o Novo lead para Atendimento |
| `POST /api/deals/[id]/acoes` | Liguei, Requalifiquei, Desisti |
| `POST /api/deals/[id]/comentarios` | postar comentário |
| `DELETE /api/comentarios/[id]` | apagar comentário (remoção lógica) |
| `POST /api/deals/[id]/contato` | adicionar o contato principal |
| `POST` / `DELETE /api/deals/[id]/tags` | aplicar / remover tag |
| `GET` / `POST /api/tags` | listar / criar tag (manager e admin) |
| `POST /api/prioridades` | ✓ (tipo de atividade e comentário obrigatórios) ou ✗ |
| `POST /api/prioridades/mais` | puxar mais 5 (a tela não usa: os 20 da meta ficam à mostra) |
| `GET /api/lotes` | lotes das últimas 24 horas que o perfil pode desfazer (os próprios; manager: os do time; admin: todos) |
| `POST /api/lotes` | ação em lote (marcados ou todos os do filtro, até 500) |
| `GET /api/contas/[nome]` | ficha da empresa |
| `POST /api/contas` | criar ou editar empresa |
| `GET /api/rotina/diaria` | rotina diária do score (cron da Vercel, `Authorization: Bearer CRON_SECRET`); um dia de negócio roda uma vez |
| `POST /api/rotina/rodar-agora` | a mesma rotina, na mão, com o mesmo segredo; `?forcar=1` roda mesmo com o dia já rodado (`rotina_forcada`) |
| `POST /api/desfazer` | desfazer uma mudança ou um lote (token fora do formato = 400, sem chamar o banco); no lote, devolve quantas mudanças voltaram e quantas ficaram |

Toda rota de escrita: valida a entrada com zod, tem limite por endereço de rede (60 por minuto, resposta 429 em frase simples), gera o `correlation_id` no servidor e o devolve em `x-correlation-id`, e responde erro sempre como `{ erro, codigo }`. Erro de campo vem com a frase do campo ("E-mail inválido…", "Preencha o nome.") e `detalhe.campo`; o valor digitado nunca volta na resposta.

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
- **Erros do banco:** `GS400`–`GS429` viram a frase simples que o banco devolve; conflito de versão (`GS409`) diz quem alterou. Entrada que o banco recusa (dado inválido, pedido mal formado) vira frase simples (400 ou 422), sem mostrar a mensagem crua.
- **Banco fora por 15 s:** só em falha de disponibilidade (rede, tempo esgotado, HTTP 5xx, erro de conexão do Postgres). Entrada inválida nunca aciona, para que ninguém consiga travar as escritas dos outros de propósito. Consulta que passa do tempo limite do banco falha só naquele pedido.
- **Reserva:** banco fora ou não configurado = leitura de `data/base.json`, faixa de somente leitura e escrita recusada (503).
- Variáveis: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL_ROTINA`, `CRON_SECRET`, `G4_ESCRITA_EM_MEMORIA` e `G4_SOMENTE_LEITURA` (ver `.env.example` e `COMO-RODAR.md`).

## Ainda não construído

- Importação de leads por CSV na tela (a função existe no banco; o desenho ficou como registro em [../historico/DESENHO-CRM.md](../historico/DESENHO-CRM.md)).
- Editar o nome do deal e a empresa do deal pelo modal.
- Cadastrar e editar empresa com o banco ligado (falta a function no banco).
- Playwright nos caminhos críticos. O Vitest cobre a reserva, as prioridades, o escopo da ficha da empresa, os erros do banco, o "Desfazer", o filtro livre, o desfazer de lote, as frases de erro de campo, a tela de login, a explicação da nota e a rotina diária (inclusive contra um Postgres em memória com todas as migrations e o dataset inteiro).
