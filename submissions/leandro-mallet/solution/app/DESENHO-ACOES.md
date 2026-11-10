# Desenho: registrar ações do vendedor e limpar o pipeline

> Proposta para decisão. Nada disto está construído.

## O que o vendedor e o manager ganham

- No detalhe de cada deal: botões **Liguei**, **Requalifiquei**, **Desisti** (e **Desfazer**), com uma nota curta opcional.
- Deal marcado como "Desisti" sai das listas do vendedor. O pipeline fica limpo, mas nada é apagado.
- Visão do manager: quantos deals o score sugeriu encerrar e quantos o vendedor confirmou, e quem não registra nenhuma ação há dias.
- Tela "Limpeza do pipeline": a lista de deals que o score marca como `desistir`, com confirmação em lote ("Confirmar desistência dos 43"). Cada confirmação vira um registro.

## Regra central: o app abre só com o JSON

| Situação | Comportamento |
|---|---|
| Banco fora ou não configurado | O app funciona como hoje (só leitura). Os botões de ação não aparecem, e uma linha discreta avisa "Registro de ações indisponível". |
| Banco no ar | O app carrega as ações ao abrir e aplica o estado atual de cada deal sobre o JSON. |

Os avaliadores podem rodar sem nenhuma credencial.

## Arquitetura recomendada: servidor pequeno em Python, só com a biblioteca padrão

```
navegador ──GET/POST /api/acoes──► app/servidor.py ──REST + service role──► Supabase
            ◄── arquivos estáticos ──┘   (lê SUPABASE_URL e a chave do .env;
                                            sem as variáveis, serve só os arquivos)
```

- `servidor.py` troca o `python -m http.server`: serve os mesmos arquivos e acrescenta duas rotas (`GET /api/acoes`, `POST /api/acoes`).
- Usa `urllib` contra a REST do Supabase: sem `pip install`. Com `DATABASE_URL` direto seria preciso o `psycopg`, e isso quebra o "roda sem dependência".
- **A service role nunca vai para o navegador.** Numa página estática ela ficaria visível para qualquer pessoa com o link e daria acesso total ao banco.
- Alternativa descartada: o navegador falar direto com o Supabase usando a chave pública e RLS. Sem login, qualquer pessoa com o link poderia gravar na tabela.

## Tabela (só acrescenta registros; nunca apaga nem edita)

```sql
create table lead_scorer_acoes (
  id              bigint generated always as identity primary key,
  opportunity_id  text not null,
  sales_agent     text not null,
  acao            text not null check (acao in ('liguei','requalifiquei','desisti','desfazer')),
  nota            text,
  reference_date  date,          -- data do pipeline em que a ação foi tomada
  criado_em       timestamptz not null default now()
);
create index on lead_scorer_acoes (opportunity_id, criado_em desc);
alter table lead_scorer_acoes enable row level security;  -- sem política: só a service role acessa
```

- O estado atual de cada deal é a última ação registrada para ele (uma `view` ou a conta no próprio app).
- "Desfazer" é um registro novo, não uma remoção. O histórico fica inteiro e serve de auditoria.

## No app (mudanças previstas)

- `app.js`: ao abrir, tenta `GET /api/acoes`. Se a resposta for 404 ou a chamada falhar, entra no modo só leitura.
- O detalhe do deal ganha os botões e a última ação ("Você ligou em 12/11").
- Os cartões e as listas mostram um selo com a última ação. Os deals com "Desisti" ficam numa seção recolhida "Encerrados por você".
- Ao gravar, a tela mostra "Ação registrada" na hora. Se a gravação falhar, o botão volta e aparece "Não foi possível registrar. Tente de novo."

## Decisões em aberto para o Leandro

1. Qual projeto Supabase usar (de preferência um só para o desafio, separado dos outros).
2. Se o "Liguei" deve mexer no score: por exemplo, contato recente não deixa o deal virar "esfriando" por X dias. Isso cabe à #3.
3. Se a tela de limpeza fica só com o manager ou também com o vendedor.
