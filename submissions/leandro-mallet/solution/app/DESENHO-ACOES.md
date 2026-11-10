# Desenho: registrar ações do vendedor e limpar o pipeline

> Proposta para decisão. Nada disto está construído.

## O que o vendedor e o manager ganham

- No detalhe de cada deal: botões **Liguei**, **Requalifiquei**, **Desisti** (e **Desfazer**), com uma nota curta opcional.
- Deal marcado como "Desisti" sai das listas do vendedor. O pipeline fica limpo, mas nada é apagado.
- Visão do manager: quantos deals o score sugeriu encerrar e quantos o vendedor confirmou, e quem não registra nenhuma ação há dias.
- Tela "Limpeza do pipeline": a lista de deals que o score marca como `desistir`, com confirmação em lote ("Confirmar desistência dos 43"). Cada confirmação vira um registro.

## Regra central: ler nunca depende do banco nem de login

| Situação | Comportamento |
|---|---|
| Banco fora, não configurado ou projeto pausado | O app funciona como hoje (só leitura, a partir do JSON). Os botões de ação não aparecem, e uma linha discreta avisa "Registro de ações indisponível". |
| Banco no ar, sem login | Leitura completa, incluindo as ações já registradas. Os botões aparecem com "Entre para registrar". |
| Banco no ar, com login | O usuário registra ações no próprio pipeline (vendedor) ou no do time (manager). |

Os avaliadores sempre conseguem abrir e usar a parte de priorização, mesmo que o login ou o banco falhem.

## Banco

Projeto Supabase **G4_AI_Mastering**, usado só para este desafio. Variáveis: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` e `SUPABASE_ANON_KEY` (esta só para o login). Localmente elas vêm do `.env` da raiz do clone; na Vercel, das variáveis de ambiente do projeto. O `.env` nunca vai para o git.

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

## Um código só, local e na Vercel

A Vercel roda funções Python sem dependência quando o arquivo em `api/` define uma classe `handler` derivada de `BaseHTTPRequestHandler`. O servidor local reaproveita essas mesmas classes. Nenhuma linha da lógica fica duplicada.

```
solution/                         ← raiz do projeto na Vercel
  vercel.json                     redireciona "/" para "/app/"
  api/
    _supabase.py                  chamadas à REST e ao Auth do Supabase (urllib); lê as variáveis
    acoes.py                      class handler: GET lista ações, POST registra uma ação
    sessao.py                     class handler: POST entra (e-mail + senha), devolve o token
  app/
    servidor.py                   local: serve os arquivos e repassa /api/* para as classes acima
    index.html, app.js, ...       iguais nos dois lugares
  data/scored/deals_scored.json   servido como arquivo estático nos dois lugares
```

O servidor local, inteiro, fica assim:

```python
# app/servidor.py — uso: python app/servidor.py  (a partir de solution/)
import sys, pathlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "api"))
import acoes, sessao  # as mesmas classes que a Vercel usa

ROTAS = {"/api/acoes": acoes.handler, "/api/sessao": sessao.handler}

class Servidor(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=str(RAIZ), **k)
    def _api(self, metodo):
        h = ROTAS.get(self.path.split("?")[0])
        if not h: return False
        getattr(h, metodo)(self); return True
    def do_GET(self):  self._api("do_GET") or super().do_GET()
    def do_POST(self): self._api("do_POST") or self.send_error(404)

ThreadingHTTPServer(("127.0.0.1", 8000), Servidor).serve_forever()
```

- O app chama sempre `../api/acoes` (caminho relativo a `/app/`), que funciona nos dois lugares.
- Sem as variáveis de ambiente, `GET /api/acoes` responde `503 {"disponivel": false}` e o app entra no modo só leitura.
- O `python -m http.server` continua funcionando: as rotas `/api` dão 404 e o app fica só leitura.
- O login também passa pelo servidor (`/api/sessao`). Assim o navegador não precisa de nenhuma configuração do Supabase, e as chaves ficam num lugar só.
- A função confere o token a cada gravação (`GET /auth/v1/user`), busca o perfil e só aceita ação em deal do próprio vendedor ou de alguém do time do manager. Depois grava com a service role.

## Identidade: três caminhos

| | A. Só escolher o perfil, sem senha | B. Login obrigatório (Supabase Auth) | **C. Ler sem login, gravar com login de demonstração** (recomendado) |
|---|---|---|---|
| Como é | O "Quem é você?" de hoje também vale para gravar | Tela de login antes de tudo; contas de vendedor e de manager no README | O app abre como hoje. Para registrar ação, "Entrar" com uma conta de demonstração (botão "Usar conta de demonstração" preenche os dados) |
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
- Com a senha pública no README, qualquer um grava com essas contas. Para conter isso: limite de gravações por conta por minuto na função, nota com no máximo 280 caracteres, e o reset da demonstração feito pelo filtro de data (mostrar só as ações dos últimos N dias), nunca por DELETE.
- Token guardado só na aba (`sessionStorage`): fechou a aba, saiu.

## No app (mudanças previstas)

- `app.js`: ao abrir, tenta `GET ../api/acoes`. Se a resposta for 404, 503 ou a chamada falhar, entra no modo só leitura.
- O detalhe do deal ganha os botões e a última ação ("Anna ligou em 12/11").
- Os cartões e as listas mostram um selo com a última ação. Os deals com "Desisti" ficam numa seção recolhida "Encerrados".
- Ao gravar, a tela mostra "Ação registrada" na hora. Se a gravação falhar, o botão volta e aparece "Não foi possível registrar. Tente de novo."
- O topo ganha "Entrar" / "Sair" e o nome de quem está conectado.

## Arquivos fora de `app/`

`solution/api/` e `solution/vercel.json` ficam fora da pasta desta sessão: a Vercel exige `api/` na raiz do projeto. Criar só com o ok da #1.

## Decisões em aberto

1. Caminho de identidade: A, B ou C (recomendado C).
2. Qual vendedor e qual manager do dataset recebem as contas de demonstração.
3. Junto com o score: se "Liguei" mexe no score e se a limpeza fica só com o manager ou também com o vendedor.
