-- RAG por similaridade (ADR-0004 e ADR-0010): embeddings do DS2 + função de classificação por voto dos vizinhos.
-- Aplicada via MCP supabase-g4 (apply_migration "rag"). Os vetores são carregados por scripts/load_embeddings.py.

-- pgvector fica no schema "extensions" (recomendação do Supabase: nada de extensão no schema public).
create extension if not exists vector with schema extensions;

-- 512 dims de text-embedding-3-small (truncado + renormalizado = parâmetro "dimensions" da API),
-- em halfvec (16 bits): ~49 MB de vetores, cabe com folga nos 500 MB do plano free (ADR-0004).
create table if not exists public.ds2_embeddings (
  id         integer primary key references public.ds2_tickets (id) on delete cascade,
  embedding  extensions.halfvec(512) not null
);

comment on table public.ds2_embeddings is
  'Embeddings text-embedding-3-small (512 dims, normalizados) dos tickets do DS2. Memória de casos parecidos do RAG (ADR-0004/0010).';

-- Índice aproximado (HNSW) por cosseno. O loader recria este índice depois do COPY (mais rápido que indexar linha a linha).
create index if not exists ds2_embeddings_hnsw_idx
  on public.ds2_embeddings using hnsw (embedding extensions.halfvec_cosine_ops);

alter table public.ds2_embeddings enable row level security;

-- Classificação por voto ponderado dos vizinhos (ADR-0010):
--   - 50 vizinhos mais próximos, SÓ do split de treino (o teste fica fora para a avaliação ser honesta);
--   - peso de cada vizinho = similaridade^16 (similaridade negativa vira 0);
--   - confiança = fração ponderada dos votos da categoria vencedora;
--   - sensitive_share = fração dos votos em categorias sensíveis (HR Support, Administrative rights).
-- A política de 3 níveis (≥ 0,9 automático; sensível, ≥ 30% sensível ou < 0,5 só humano) é aplicada no n8n.
-- hnsw.iterative_scan: como o filtro de treino descarta ~20% dos vizinhos, a busca continua até achar 50.
create or replace function public.classify_ticket(query extensions.halfvec(512))
returns table (
  category         text,
  confidence       double precision,
  sensitive_share  double precision,
  votes            jsonb,
  similar_cases    jsonb
)
language sql
stable
set search_path = public, extensions, pg_temp
set hnsw.ef_search = 100
set hnsw.iterative_scan = strict_order
as $$
  with neighbors as (
    select e.id, t.topic_group, t.document, 1 - (e.embedding <=> query) as sim
    from public.ds2_embeddings e
    join public.ds2_tickets t on t.id = e.id
    where t.split = 'train'
    order by e.embedding <=> query
    limit 50
  ),
  weighted as (
    select topic_group, sum(power(greatest(sim, 0), 16)) as w
    from neighbors
    group by topic_group
  ),
  shares as (
    select topic_group, w / nullif(sum(w) over (), 0) as share
    from weighted
  )
  select
    (select s.topic_group from shares s order by s.share desc nulls last limit 1),
    (select max(s.share) from shares s),
    coalesce((select sum(s.share) from shares s
              where s.topic_group in ('HR Support', 'Administrative rights')), 0),
    (select jsonb_object_agg(s.topic_group, round(s.share::numeric, 4)) from shares s),
    (select jsonb_agg(jsonb_build_object(
                'id', n.id,
                'category', n.topic_group,
                'similarity', round(n.sim::numeric, 4),
                'snippet', left(n.document, 280)
              ) order by n.sim desc)
       from (select * from neighbors order by sim desc limit 5) n)
$$;

comment on function public.classify_ticket(extensions.halfvec) is
  'RAG (ADR-0010): voto dos 50 vizinhos de treino, peso sim^16. Retorna categoria, confiança, fração sensível, votos e os 5 casos mais parecidos.';

-- Só o backend (n8n via Postgres / service role) chama a função; anon e authenticated não.
revoke execute on function public.classify_ticket(extensions.halfvec) from public, anon, authenticated;
grant execute on function public.classify_ticket(extensions.halfvec) to service_role;
