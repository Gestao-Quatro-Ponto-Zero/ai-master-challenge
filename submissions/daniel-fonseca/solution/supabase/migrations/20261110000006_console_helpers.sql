-- Funções de apoio ao Console (PRD v1.1 §4.4 e §4.5). Só service role executa.
-- Aplicada via MCP supabase-g4 (apply_migration "console_helpers").

-- Carrega a biblioteca do pgvector (registra hnsw.*) antes do CREATE FUNCTION com SET hnsw.*;
-- sem isso o Supabase recusa o SET ("permission denied to set parameter hnsw.ef_search").
select '[1,2]'::extensions.halfvec;

-- Sorteia um ticket do holdout (split de teste), opcionalmente de uma categoria real.
-- Devolve só id e texto: o rótulo real é revelado pelo app depois da triagem.
create or replace function public.random_holdout_ticket(p_category text default null)
returns table (id integer, document text)
language sql
volatile
set search_path = public, pg_temp
as $$
  select t.id, t.document
  from public.ds2_tickets t
  where t.split = 'test'
    and (p_category is null or t.topic_group = p_category)
    and array_length(regexp_split_to_array(t.document, '\s+'), 1) between 8 and 120
  order by random()
  limit 1
$$;

-- Efeito "aprendeu" (PRD §4.5): o ticket do holdout mais parecido com o de uma triagem já decidida,
-- excluindo o próprio ticket. Usa o embedding gravado em triage_runs.
create or replace function public.nearest_holdout_ticket(p_triage_run_id bigint)
returns table (id integer, document text, similarity double precision)
language sql
stable
set search_path = public, extensions, pg_temp
set hnsw.ef_search = 100
set hnsw.iterative_scan = strict_order
as $$
  select t.id, t.document, 1 - (e.embedding <=> r.embedding) as similarity
  from public.triage_runs r
  join public.ds2_embeddings e on true
  join public.ds2_tickets t on t.id = e.id and t.split = 'test'
  where r.id = p_triage_run_id
    and r.embedding is not null
    and (r.ds2_id is null or t.id <> r.ds2_id)
  order by e.embedding <=> r.embedding
  limit 1
$$;

revoke execute on function public.random_holdout_ticket(text) from public, anon, authenticated;
revoke execute on function public.nearest_holdout_ticket(bigint) from public, anon, authenticated;
grant execute on function public.random_holdout_ticket(text) to service_role;
grant execute on function public.nearest_holdout_ticket(bigint) to service_role;
