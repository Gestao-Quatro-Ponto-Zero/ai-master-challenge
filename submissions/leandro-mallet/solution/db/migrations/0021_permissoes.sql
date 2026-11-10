-- 0021_permissoes.sql  [LOTE 2]
-- Fecha as permissões (BD-03): só o servidor, com a service role, executa as funções; anon e authenticated
-- não leem tabelas nem views e não executam funções. Os papéis existem no Supabase; o bloco ignora papel ausente.

do $$
declare
  r text;
begin
  execute 'revoke execute on all functions in schema public from public';
  execute 'alter default privileges in schema public revoke execute on functions from public';
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke execute on all functions in schema public from %I', r);
      execute format('revoke all on all tables in schema public from %I', r);
      execute format('alter default privileges in schema public revoke execute on functions from %I', r);
      execute format('alter default privileges in schema public revoke all on tables from %I', r);
    end if;
  end loop;
  if exists (select 1 from pg_roles where rolname = 'service_role') then
    execute 'grant execute on all functions in schema public to service_role';
    execute 'grant select, insert, update on all tables in schema public to service_role';
    execute 'grant usage, select on all sequences in schema public to service_role';
    execute 'revoke delete, truncate on all tables in schema public from service_role';
  end if;
end $$;
