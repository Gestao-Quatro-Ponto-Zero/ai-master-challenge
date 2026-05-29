create extension if not exists vector;

create table if not exists profiles (
  id uuid primary key,
  email text not null,
  full_name text,
  role text not null default 'customer' check (role in ('admin','customer')),
  created_at timestamptz default now()
);

create table if not exists support_tickets_kb (
  id bigserial primary key,
  source_ticket_id text,
  description text not null,
  resolution text,
  category text,
  priority text,
  channel text,
  embedding vector(1536),
  created_at timestamptz default now()
);

create index if not exists support_tickets_kb_embedding_idx
  on support_tickets_kb using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create table if not exists tickets (
  id bigserial primary key,
  customer_id uuid not null,
  source text not null check (source in ('text','audio')),
  audio_path text,
  raw_text text not null,
  category text,
  priority text check (priority in ('low','medium','high','critical')),
  status text not null default 'open' check (status in ('open','pending','resolved','deflected')),
  rag_suggestion text,
  rag_confidence numeric,
  resolved_by_ai boolean default false,
  created_at timestamptz default now(),
  resolved_at timestamptz
);

create index if not exists tickets_customer_created_idx on tickets (customer_id, created_at desc);
create index if not exists tickets_status_idx on tickets (status);

create table if not exists deflection_events (
  id bigserial primary key,
  customer_id uuid,
  raw_text text,
  top_matches jsonb,
  created_at timestamptz default now()
);

-- ── Ticket categories from Dataset 2 (IT service tickets) ────────────────
-- Used for: auto-classify new tickets by vector similarity
create table if not exists ticket_categories (
  id bigserial primary key,
  source_ticket_id text,
  description text not null,
  category text not null,
  embedding vector(1536),
  created_at timestamptz default now()
);

create index if not exists ticket_categories_embedding_idx
  on ticket_categories using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create or replace function match_ticket_category (
  query_embedding vector(1536),
  match_count int default 7
)
returns table (
  id bigint,
  description text,
  category text,
  similarity float
)
language sql stable
as $$
  select id, description, category,
         1 - (embedding <=> query_embedding) as similarity
  from ticket_categories
  order by embedding <=> query_embedding
  limit match_count;
$$;

-- ── Knowledge base (RAG deflection) ──────────────────────────────────────
create or replace function match_kb (
  query_embedding vector(1536),
  match_threshold float default 0.75,
  match_count int default 5
)
returns table (
  id bigint,
  description text,
  resolution text,
  category text,
  similarity float
)
language sql stable
as $$
  select id, description, resolution, category,
         1 - (embedding <=> query_embedding) as similarity
  from support_tickets_kb
  where 1 - (embedding <=> query_embedding) > match_threshold
  order by embedding <=> query_embedding
  limit match_count;
$$;
