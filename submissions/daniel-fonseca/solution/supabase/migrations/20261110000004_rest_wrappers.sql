-- Fluxos n8n com nós nativos do Supabase (ADR-0013): as funções do RAG são chamadas pela API REST
-- (POST /rest/v1/rpc/<função>) com a credencial Supabase do n8n.
-- O HTTP Request do n8n transforma uma lista JSON em vários itens e, se ela vier vazia, o fluxo para.
-- Este wrapper devolve sempre UM objeto { "resolutions": [...] }, mesmo sem nenhuma solução validada.
-- Aplicada via MCP supabase-g4 (apply_migration "rest_wrappers").

create or replace function public.match_resolutions_json(query extensions.halfvec(512), p_category text, k int default 3)
returns jsonb
language sql
stable
set search_path = public, extensions, pg_temp
as $$
  select jsonb_build_object(
    'resolutions',
    coalesce((select jsonb_agg(to_jsonb(r) order by r.similarity desc)
              from public.match_resolutions(query, p_category, k) r), '[]'::jsonb)
  )
$$;

comment on function public.match_resolutions_json(extensions.halfvec, text, int) is
  'Mesmo resultado de match_resolutions, embrulhado em { resolutions: [...] } para chamada via REST no n8n.';

revoke execute on function public.match_resolutions_json(extensions.halfvec, text, int) from public, anon, authenticated;
grant execute on function public.match_resolutions_json(extensions.halfvec, text, int) to service_role;

-- O playbook-semente foi revisado e validado pelo Daniel em 2026-11-10 (ADR-0004).
update public.validated_resolutions
set approved_by = 'Daniel (revisão do playbook, 2026-11-10)'
where source = 'playbook' and approved_by is null;
