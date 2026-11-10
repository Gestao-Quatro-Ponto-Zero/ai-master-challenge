-- 0032_meta_prioridades_20.sql  [O-34 — 20 prioridades por dia, todas à mostra]
-- Pedido do Leandro: a lista do dia passa de 10 para 20 itens, para todos os papéis (manager e admin seguem com o
-- filtro "atencao"). O que muda:
--   1. config_parametros.meta_prioridades_dia = 20 (uma linha de configuração, auditada);
--   2. acao_prioridades guarda a meta usada (meta_dia). Lista de hoje montada com meta menor fica "desatualizada":
--      a leitura volta vazia e acao_prioridades_do_dia completa a lista até a meta nova, sem mexer nos itens que já
--      estão nela (marcados ou não). Se não houver deals suficientes, a lista fica com o que houver e não é refeita
--      a cada leitura (todas as linhas ativas passam a guardar a meta nova);
--   3. acao_prioridades_do_dia e acao_lista_desatualizada passam a considerar a meta (o resto da 0030 segue igual).
-- Nada é apagado. Trava de contexto, limites, auditoria e permissões seguem como estão.

select system_iniciar_contexto_sistema('00000000-0000-4000-8000-000000000032'::uuid);

-- 1. Meta do dia -------------------------------------------------------------------------------------------------

update config_parametros
   set valor = '20'::jsonb,
       descricao = 'Meta diária de itens nas Prioridades do dia (20, todos à mostra; O-34).',
       atualizado_em = now()
 where chave = 'meta_prioridades_dia';

-- 2. A lista guarda a meta usada -----------------------------------------------------------------------------------

alter table acao_prioridades
  add column meta_dia smallint check (meta_dia > 0);

-- Lista de hoje desatualizada: item não marcado de outra execução (0030) ou meta menor que a atual (0032).
create or replace function acao_lista_desatualizada(p_usuario_id bigint) returns boolean
language sql stable set search_path = public as $$
  select exists (select 1 from acao_prioridades p
                  where p.usuario_id = p_usuario_id and p.dia = system_dia_real() and p.substituida_em is null
                    and p.execucao_id is distinct from score_execucao_ativa()
                    and not acao_item_marcado(p_usuario_id, p.opportunity_id, p.dia))
      or exists (select 1 from acao_prioridades p
                  where p.usuario_id = p_usuario_id and p.dia = system_dia_real() and p.substituida_em is null
                    and coalesce(p.meta_dia, 0) < coalesce(config_inteiro('meta_prioridades_dia'), 20))
$$;

-- 3. Lista do dia: monta, atualiza a execução (0030) e completa até a meta ---------------------------------------------

create or replace function acao_prioridades_do_dia(p_usuario_id bigint, p_correlation_id uuid)
returns table (posicao smallint, opportunity_id text, nome text, vendedor_nome text, produto_nome text, conta_nome text,
               score smallint, faixa_nota text, icone text, valor_esperado integer, marcada text, pulado_dias_seguidos integer)
language plpgsql set search_path = public as $$
declare
  u      config_usuarios := system_iniciar_contexto(p_usuario_id, p_correlation_id, false);
  v_dia  date := system_dia_real();
  v_meta integer := coalesce(config_inteiro('meta_prioridades_dia'), 20);
  v_tem  integer;
begin
  perform pg_advisory_xact_lock(30030, u.id::integer);
  if exists (select 1 from acao_prioridades p where p.usuario_id = u.id and p.dia = v_dia and p.substituida_em is null) then
    perform acao_atualizar_prioridades(u);
  end if;
  select count(*) into v_tem from acao_prioridades p where p.usuario_id = u.id and p.dia = v_dia and p.substituida_em is null;
  if v_tem < v_meta then
    perform acao_montar_prioridades(u, v_meta - v_tem);
  end if;
  update acao_prioridades p
     set meta_dia = v_meta
   where p.usuario_id = u.id and p.dia = v_dia and p.substituida_em is null
     and p.meta_dia is distinct from v_meta;
  return query select * from acao_listar_prioridades(u.id);
end $$;
