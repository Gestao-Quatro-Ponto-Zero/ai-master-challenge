# Desenho: perfis, ações do vendedor e limpeza do pipeline

> Proposta para decisão. Nada disto está construído.
> Stack (decisão 11): Next.js com TypeScript strict, Postgres no Supabase G4_AI_Mastering e publicação na Vercel. Estrutura de pastas em [DESENHO-NEXT.md](DESENHO-NEXT.md).
> Identidade (decisão 12): sem login e sem senha. A pessoa escolhe o perfil (vendedor, manager ou admin) e, se for vendedor ou manager, o próprio nome.

## Perfis

| Perfil | Escolhe | Tela inicial | Enxerga | Pode registrar ação em |
|---|---|---|---|---|
| **Vendedor** | o nome, entre os 35 do dataset | Meu dia | o próprio pipeline | deals dele |
| **Manager** | o nome, entre os managers do dataset | Visão do time | o pipeline do time; abre o "Meu dia" de cada vendedor | deals do time |
| **Admin** | nada | Visão geral (todos os times) | tudo, com os filtros de região, manager e vendedor | qualquer deal |

- A escolha fica num cookie (`perfil` = papel + nome), gravado pela rota `POST /api/perfil` depois de conferir que o nome existe no dataset com aquele papel.
- O topo mostra quem está usando ("Anna Snelling, vendedora") e o botão **Trocar perfil**, que volta para a escolha.
- O perfil define as telas e os filtros: o vendedor não vê os filtros de região e manager; o manager só filtra entre os vendedores do time; o admin vê todos.
- Sem senha, o perfil organiza a tela e assina as ações, mas não protege nada: qualquer pessoa pode escolher qualquer perfil. Para uma demonstração, é suficiente. Para uso real, entraria o login com Supabase Auth sobre a mesma estrutura (tabela e rotas não mudam; só a origem do autor).

## Fluxo da escolha

```
/  ──►  "Quem é você?"  [Vendedor]  [Manager]  [Admin]
          │ Vendedor → lista dos vendedores, agrupada por manager (com a contagem de deals)
          │ Manager  → lista dos managers, com a região e o tamanho do time
          │ Admin    → entra direto
          ▼
        POST /api/perfil  → cookie  → tela inicial do perfil
```

Quem chega por um link direto sem perfil escolhido (ex.: `/time`) cai na escolha e, depois dela, volta ao link.

## O que o vendedor e o manager ganham

- No detalhe de cada deal: botões **Liguei**, **Requalifiquei**, **Desisti** (e **Desfazer**), com uma nota curta opcional.
- Deal marcado como "Desisti" sai das listas do vendedor. O pipeline fica limpo, mas nada é apagado.
- Visão do manager: quantos deals o score sugeriu encerrar e quantos o time confirmou, e quem não registra nenhuma ação há dias.
- Tela "Limpeza do pipeline": a lista de deals que o score marca como `desistir`, com confirmação em lote ("Confirmar desistência dos 43"). Cada confirmação vira um registro. O vendedor vê os dele, o manager os do time e o admin todos.

## Regra central: ler nunca depende do banco

| Situação | Comportamento |
|---|---|
| Sem credenciais, banco fora ou projeto pausado | Perfis, telas e filtros funcionam só com o `deals_scored.json`. Os botões de ação não aparecem, e uma linha discreta avisa "Registro de ações indisponível". |
| Banco no ar | As ações registradas aparecem nas telas e os botões ficam ativos para o perfil escolhido. |

A escolha de perfil não usa o banco: a lista de nomes vem do próprio JSON.

## Banco

Projeto Supabase **G4_AI_Mastering**, usado só para este desafio. A migração fica em `supabase/migrations/0001_acoes.sql`, dentro da pasta do app.

```sql
-- Ações: só acrescenta registros; nunca apaga nem edita
create table lead_scorer_acoes (
  id              bigint generated always as identity primary key,
  opportunity_id  text not null,
  sales_agent     text not null,           -- dono do deal no momento da ação
  acao            text not null check (acao in ('liguei','requalifiquei','desisti','desfazer')),
  nota            text check (char_length(nota) <= 280),
  autor_papel     text not null check (autor_papel in ('vendedor','manager','admin')),
  autor_nome      text,                    -- nulo quando o papel é admin
  reference_date  date,
  criado_em       timestamptz not null default now()
);
create index on lead_scorer_acoes (opportunity_id, criado_em desc);
create index on lead_scorer_acoes (autor_nome, criado_em desc);
alter table lead_scorer_acoes enable row level security;  -- sem política: só a service role acessa
```

- O estado atual de cada deal é a última ação registrada para ele.
- "Desfazer" é um registro novo, não uma remoção. O histórico fica inteiro e serve de auditoria.
- Sai a tabela de perfis do desenho anterior: quem é quem vem do dataset.

## Rotas de API do Next

| Rota | O que faz | Sem credenciais do banco |
|---|---|---|
| `POST /api/perfil` | `{papel, nome?}`: confere o nome no dataset e grava o cookie | funciona |
| `DELETE /api/perfil` | Trocar perfil (apaga só o cookie) | funciona |
| `GET /api/acoes` | Última ação de cada deal visível para o perfil | `503 {"disponivel": false}` |
| `POST /api/acoes` | Registra uma ação `{opportunity_id, acao, nota?}`; aceita lote para a limpeza | `503` |

Como a gravação é conferida, em `src/server/acoes.ts`:
1. Lê o perfil do cookie. Sem perfil, responde 401.
2. Confere que o nome existe no dataset com aquele papel (o cookie pode ter sido editado). Se não, 403.
3. Confere que cada deal do pedido pertence ao pipeline do perfil: vendedor → `deal.sales_agent == nome`; manager → `deal.manager == nome`; admin → qualquer deal aberto do arquivo. Se algum falhar, responde 403 e não grava nada do lote.
4. Confere o limite (até 30 gravações por minuto por autor, contadas no próprio banco, o que vale entre as instâncias da Vercel) e o tamanho da nota.
5. Grava com a service role, com `autor_papel` e `autor_nome` vindos do perfil.

Os passos 2, 3 e a regra do limite são funções puras em `src/lib/permissao.ts`, testadas sem banco.

**Onde ficam as chaves:** só `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY`, ambas usadas apenas em `src/server/` (`import "server-only"`; o build falha se um componente do navegador importar um desses arquivos). Não há variável pública: sem login, o navegador não fala com o Supabase. Localmente as chaves ficam em `.env.local` na pasta do app (fora do git; há um `.env.example` com os nomes); na Vercel, nas variáveis de ambiente do projeto.

## Riscos

- **Qualquer um grava como qualquer um.** É aceito para a demonstração. Há duas contenções: o limite por minuto e a regra de pipeline (um vendedor escolhido só grava nos deals dele).
- **Sujeira da demonstração** (avaliadores clicando): sem DELETE. As telas mostram só as ações a partir de uma data de corte (`ACOES_DESDE`, variável opcional). Para "zerar" a demonstração, basta avançar a data.
- **Plano gratuito do Supabase pausa após 7 dias sem uso:** o app cai no modo só leitura e avisa. Antes de enviar a entrega, conferir se o projeto está ativo.

## Na tela (mudanças previstas)

- O detalhe do deal ganha os botões e a última ação ("Anna ligou em 12/11").
- Os cartões e as listas mostram um selo com a última ação. Os deals com "Desisti" ficam numa seção recolhida "Encerrados".
- Ao gravar, a tela mostra "Ação registrada" na hora. Se a gravação falhar, o botão volta e aparece "Não foi possível registrar. Tente de novo."

## Decisões em aberto

1. O admin registra ações em qualquer deal (proposta acima) ou só lê?
2. Junto com o score: se "Liguei" mexe no score e se a limpeza fica com os três perfis (proposta acima) ou só com manager e admin.
