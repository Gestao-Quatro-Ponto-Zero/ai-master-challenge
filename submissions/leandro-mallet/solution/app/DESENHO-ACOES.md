# Desenho: registrar ações do vendedor e limpar o pipeline

> Proposta para decisão. Nada disto está construído.
> Stack (decisão 11): Next.js com TypeScript strict, Postgres no Supabase G4_AI_Mastering e publicação na Vercel. A estrutura de pastas está em [DESENHO-NEXT.md](DESENHO-NEXT.md).

## O que o vendedor e o manager ganham

- No detalhe de cada deal: botões **Liguei**, **Requalifiquei**, **Desisti** (e **Desfazer**), com uma nota curta opcional.
- Deal marcado como "Desisti" sai das listas do vendedor. O pipeline fica limpo, mas nada é apagado.
- Visão do manager: quantos deals o score sugeriu encerrar e quantos o vendedor confirmou, e quem não registra nenhuma ação há dias.
- Tela "Limpeza do pipeline": a lista de deals que o score marca como `desistir`, com confirmação em lote ("Confirmar desistência dos 43"). Cada confirmação vira um registro.

## Regra central: ler nunca depende do banco nem de login

| Situação | Comportamento |
|---|---|
| Sem credenciais, banco fora ou projeto pausado | O app funciona só com o `deals_scored.json`. Os botões de ação não aparecem, e uma linha discreta avisa "Registro de ações indisponível". |
| Banco no ar, sem login | Leitura completa, incluindo as ações já registradas. Os botões aparecem com "Entre para registrar". |
| Banco no ar, com login | O usuário registra ações no próprio pipeline (vendedor) ou no do time (manager). |

Os avaliadores sempre conseguem abrir e usar a parte de priorização, mesmo que o login ou o banco falhem.

## Banco

Projeto Supabase **G4_AI_Mastering**, usado só para este desafio. A migração fica em `supabase/migrations/0001_acoes.sql`, dentro da pasta do app.

```sql
-- Quem é quem: liga a conta de login a um vendedor ou manager do dataset
create table lead_scorer_perfis (
  user_id  uuid primary key references auth.users(id),
  papel    text not null check (papel in ('vendedor','manager')),
  nome     text not null           -- sales_agent ou manager, exatamente como no dataset
);

-- Ações: só acrescenta registros; nunca apaga nem edita
create table lead_scorer_acoes (
  id              bigint generated always as identity primary key,
  opportunity_id  text not null,
  sales_agent     text not null,
  acao            text not null check (acao in ('liguei','requalifiquei','desisti','desfazer')),
  nota            text check (char_length(nota) <= 280),
  autor_id        uuid not null references auth.users(id),
  autor_papel     text not null,
  reference_date  date,
  criado_em       timestamptz not null default now()
);
create index on lead_scorer_acoes (opportunity_id, criado_em desc);
alter table lead_scorer_perfis enable row level security;  -- sem política: só a service role acessa
alter table lead_scorer_acoes  enable row level security;
```

- O estado atual de cada deal é a última ação registrada para ele.
- "Desfazer" é um registro novo, não uma remoção. O histórico fica inteiro e serve de auditoria.

## Rotas de API do Next (substituem o servidor.py e as funções Python)

| Rota | O que faz | Sem credenciais |
|---|---|---|
| `GET /api/acoes?vendedor=&manager=` | Lista a última ação de cada deal do filtro | `503 {"disponivel": false}` |
| `POST /api/acoes` | Registra uma ação `{opportunity_id, acao, nota?}`; aceita lote para a limpeza | `503` |
| `POST /api/sessao` | Entra com e-mail e senha (Supabase Auth) e grava a sessão em cookie httpOnly | `503` |
| `DELETE /api/sessao` | Sai | `503` |

Como a gravação é conferida, dentro de `src/server/acoes.ts`:
1. Lê a sessão do cookie (`@supabase/ssr`, chave pública) e confirma o usuário com `auth.getUser()`.
2. Busca o perfil em `lead_scorer_perfis` com a service role.
3. Confere a permissão contra o `deals_scored.json`: o deal precisa ser do próprio vendedor ou de alguém do time do manager. Se não for, responde 403.
4. Confere o limite de gravações por conta por minuto e o tamanho da nota.
5. Grava com a service role.

Os passos 3 e 4 são funções puras em `src/lib/permissao.ts`, testadas sem banco.

**Onde ficam as chaves:**
- `SUPABASE_SERVICE_ROLE_KEY` só existe em `src/server/` (arquivos com `import "server-only"`; o build falha se algum componente do navegador importar um deles).
- `NEXT_PUBLIC_SUPABASE_URL` e `NEXT_PUBLIC_SUPABASE_ANON_KEY` são públicas por natureza e servem só para a sessão.
- Localmente as chaves ficam em `.env.local`, na pasta do app (fora do git; há um `.env.example` com os nomes). Na Vercel, ficam nas variáveis de ambiente do projeto.
- `src/lib/config.ts` diz se o registro de ações está disponível (as três variáveis presentes). Sem elas, as rotas respondem 503 e o middleware de sessão não roda.

Por que rotas de API e não Server Actions: o contrato fica explícito, é testável com `fetch` e permite a confirmação em lote da limpeza. Os botões chamam as rotas a partir de um componente do navegador.

## Identidade: três caminhos

| | A. Só escolher o perfil, sem senha | B. Login obrigatório (Supabase Auth) | **C. Ler sem login, gravar com login de demonstração** (recomendado) |
|---|---|---|---|
| Como é | O "Quem é você?" de hoje também vale para gravar | Tela de login antes de tudo; contas de vendedor e de manager no README | O app abre sem login. Para registrar ação, "Entrar" com uma conta de demonstração (botão "Usar conta de demonstração" preenche os dados) |
| Avaliação travada? | Nunca | **Sim**, se o Auth ou o projeto estiver fora: o avaliador não vê nada | Nunca: priorização e explicação abrem sem login; só os botões de gravar dependem dele |
| Quem gravou é confiável? | Não. Qualquer um grava como qualquer um, e "quem não registra ações" vira autodeclaração | Sim | Sim, para as gravações |
| Endpoint público na Vercel | Aberto: qualquer um com o link grava | Fechado por conta | Fechado por conta |
| Ver outros vendedores | Livre | Preso à conta (o avaliador só veria 1 vendedor) | Livre para ler; gravar só no que a conta permite |
| Esforço | Mínimo | Médio | Médio (o mesmo de B) |

Por que C: o critério "dá para rodar seguindo as instruções" não pode depender do login funcionar no dia da avaliação, e a gravação precisa de dono para que a visão do manager signifique algo.

**Contas de demonstração (no README):**
- vendedor: ligada a um vendedor do dataset com bastante pipeline (ex.: Anna Snelling);
- manager: ligada ao manager desse vendedor (ex.: Dustin Brinkmann), para gravar no time.

**Riscos e como cobrir:**
- O plano gratuito do Supabase pausa o projeto após 7 dias sem uso. Nesse caso o app fica só leitura e avisa. Antes de enviar a entrega, conferir se o projeto está ativo.
- Com a senha pública no README, qualquer um grava com essas contas. Para conter isso: limite de gravações por conta por minuto, nota com no máximo 280 caracteres, e o reset da demonstração feito pelo filtro de data (mostrar só as ações dos últimos N dias), nunca por DELETE.

## Na tela (mudanças previstas)

- O detalhe do deal ganha os botões e a última ação ("Anna ligou em 12/11").
- Os cartões e as listas mostram um selo com a última ação. Os deals com "Desisti" ficam numa seção recolhida "Encerrados".
- Ao gravar, a tela mostra "Ação registrada" na hora. Se a gravação falhar, o botão volta e aparece "Não foi possível registrar. Tente de novo."
- O topo ganha "Entrar" / "Sair" e o nome de quem está conectado.

## Decisões em aberto

1. Caminho de identidade: A, B ou C (recomendado C).
2. Qual vendedor e qual manager do dataset recebem as contas de demonstração.
3. Junto com o score: se "Liguei" mexe no score e se a limpeza fica só com o manager ou também com o vendedor.
