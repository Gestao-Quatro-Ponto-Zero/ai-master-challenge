-- 0034_relogio_e_rotina.sql  [O-41 — relógio que anda e rotina diária do score, decisão 48]
-- 1. Relógio: a data de negócio anda 1 dia por dia real, ancorada em 10/11/2026 (America/Sao_Paulo) = 31/12/2017.
--    17/11/2026 = 07/01/2018 (o 1º domingo novo), e assim por diante. Hoje continua dando 31/12/2017.
--    As âncoras ficam em config_parametros (data_ancora_real, data_ancora_negocio). Tudo o que usa
--    system_data_negocio() (dias no pipeline, faixas, linha do tempo, Painel) anda junto.
-- 2. Papel de login g4_rotina, membro só de system_carga, SEM senha neste arquivo: a senha é definida por quem
--    aplica, fora do git (alter role g4_rotina password '…'), e a URL vira segredo do app (DATABASE_URL_ROTINA).
--    A rotina entra com ele e faz "set local role system_carga" em cada transação.
-- 3. Registro da rotina em system_eventos (sem tabela nova): 'rotina_diaria' com o resultado e 'rotina_diaria_falha'
--    quando algo dá errado. system_rotina_ja_rodou(dia) diz se o dia de negócio já rodou com sucesso.
-- Nada é apagado. Trava de contexto, limites, auditoria e permissões seguem como estão.

select system_iniciar_contexto_sistema('00000000-0000-4000-8000-000000000034'::uuid);

-- 1. Relógio -------------------------------------------------------------------------------------------------------

insert into config_parametros (chave, valor, descricao) values
  ('data_ancora_real', '"2026-11-10"'::jsonb, 'Dia real (no fuso do CRM) que corresponde a data_ancora_negocio. O relógio anda 1 dia por dia real a partir daí (decisão 48).'),
  ('data_ancora_negocio', '"2017-12-31"'::jsonb, 'Data de negócio no dia data_ancora_real (o último dia do dataset).')
on conflict do nothing;

update config_parametros
   set descricao = 'Relógio do CRM: com true e as âncoras definidas, a data de negócio anda 1 dia por dia real (decisão 48); sem âncoras, fica em data_referencia (P6).',
       atualizado_em = now()
 where chave = 'modo_demonstracao';

create or replace function system_data_negocio() returns date
language sql stable set search_path = public as $$
  select case
           when not coalesce(config_booleano('modo_demonstracao'), false)
             then system_dia_real()
           when config_texto('data_ancora_real') is not null and config_texto('data_ancora_negocio') is not null
             then (config_texto('data_ancora_negocio'))::date + (system_dia_real() - (config_texto('data_ancora_real'))::date)
           else (config_texto('data_referencia'))::date
         end
$$;

-- 2. Papel de login da rotina (sem senha aqui) ------------------------------------------------------------------------

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'g4_rotina') then
    create role g4_rotina login noinherit;
  end if;
end $$;
grant system_carga to g4_rotina;
grant usage on schema public to g4_rotina;

-- 3. Registro da rotina -------------------------------------------------------------------------------------------------

-- O dia de negócio já rodou com sucesso?
create or replace function system_rotina_ja_rodou(p_dia date) returns boolean
language sql stable set search_path = public as $$
  select exists (select 1 from system_eventos e
                  where e.tipo = 'rotina_diaria' and e.detalhe ->> 'dia_negocio' = p_dia::text
                    and e.detalhe ->> 'status' = 'ok')
$$;

do $$
declare
  r text;
begin
  execute 'revoke execute on function system_rotina_ja_rodou(date) from public';
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('revoke execute on function system_rotina_ja_rodou(date) from %I', r);
    end if;
  end loop;
  foreach r in array array['service_role', 'system_carga'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format('grant execute on function system_rotina_ja_rodou(date) to %I', r);
    end if;
  end loop;
end $$;
