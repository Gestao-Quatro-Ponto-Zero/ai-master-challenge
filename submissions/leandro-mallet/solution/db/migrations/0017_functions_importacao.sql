-- 0017_functions_importacao.sql  [LOTE 2]
-- Cria a importação de deals por planilha CSV (DESENHO-CRM): conferência linha a linha sem gravar,
-- importação numa transação só, reimportação sem duplicar (on conflict do nothing) e resumo em
-- system_importacoes. Cada deal inserido passa pela auditoria com o mesmo correlation_id.
-- O servidor lê o CSV, normaliza nomes (ex.: "GTXPro" → "GTX Pro") e envia as linhas como JSON:
--   [{"linha": 2, "opportunity_id": "...", "sales_agent": "...", "product": "...", "account": "...",
--     "deal_stage": "...", "engage_date": "AAAA-MM-DD", "close_date": "AAAA-MM-DD", "close_value": "1054"}]

create or replace function core_importar_deals(
  p_usuario_id        bigint,
  p_correlation_id    uuid,
  p_arquivo_nome      text,
  p_arquivo_sha256    text,
  p_linhas            jsonb,
  p_somente_conferir  boolean default true
) returns jsonb
language plpgsql set search_path = public as $$
declare
  u           config_usuarios;
  l           jsonb;
  v_total     integer;
  v_num       integer;
  v_id        text;
  v_vend      text;
  v_prod      text;
  v_conta     text;
  v_estagio   text;
  v_abert     date;
  v_fech      date;
  v_valor     integer;
  v_motivo    text;
  v_vistos    text[] := '{}';
  v_aceitas   jsonb := '[]'::jsonb;
  v_recusas   jsonb := '[]'::jsonb;
  v_ja        integer := 0;
  v_inseridos integer := 0;
  v_imp_id    bigint;
begin
  u := system_iniciar_contexto(p_usuario_id, p_correlation_id, false);
  perform system_exigir_papel(u, config_lista('papeis_importacao'));
  if p_linhas is null or jsonb_typeof(p_linhas) <> 'array' then
    raise exception 'O arquivo não tem linhas para importar.' using errcode = 'GS400';
  end if;
  v_total := jsonb_array_length(p_linhas);
  if v_total > coalesce(config_inteiro('limite_linhas_importacao'), 10000) then
    raise exception 'O arquivo tem % linhas; o máximo é %.', v_total, config_inteiro('limite_linhas_importacao')
      using errcode = 'GS400';
  end if;

  for l in select value from jsonb_array_elements(p_linhas) loop
    v_motivo  := null;
    v_num     := coalesce((l ->> 'linha')::integer, 0);
    v_id      := upper(btrim(l ->> 'opportunity_id'));
    v_vend    := btrim(l ->> 'sales_agent');
    v_prod    := btrim(l ->> 'product');
    v_conta   := nullif(btrim(l ->> 'account'), '');
    v_estagio := btrim(l ->> 'deal_stage');
    begin
      v_abert := nullif(btrim(l ->> 'engage_date'), '')::date;
      v_fech  := nullif(btrim(l ->> 'close_date'), '')::date;
      v_valor := nullif(btrim(l ->> 'close_value'), '')::numeric::integer;
    exception when others then
      v_abert := null;
      v_fech := null;
      v_valor := null;
      v_motivo := 'Data ou valor em formato inválido (use AAAA-MM-DD e número inteiro).';
    end;

    if v_motivo is null then
      v_motivo := case
        when v_id is null or v_id !~ '^[A-Z0-9]{8}$'
          then 'O código do deal (opportunity_id) precisa ter 8 letras ou números.'
        when v_id = any (v_vistos)
          then 'Código repetido neste arquivo: a linha anterior com o mesmo opportunity_id já vale.'
        when not exists (select 1 from core_vendedores where nome = v_vend)
          then format('O vendedor "%s" não está no time.', coalesce(v_vend, ''))
        when not exists (select 1 from core_produtos where nome = v_prod)
          then format('O produto "%s" não está no catálogo.', coalesce(v_prod, ''))
        when v_conta is not null and not exists (select 1 from core_contas where nome = v_conta)
          then format('A empresa "%s" não está cadastrada. Cadastre a empresa ou deixe a coluna vazia.', v_conta)
        when v_estagio is null or v_estagio not in ('Prospecting', 'Engaging', 'Won', 'Lost')
          then 'Estágio inválido: use Prospecting, Engaging, Won ou Lost.'
        when v_estagio <> 'Prospecting' and v_abert is null and not (v_estagio = 'Lost')
          then 'Falta a data de abertura (engage_date).'
        when v_estagio in ('Won', 'Lost') and v_fech is null
          then 'Falta a data de fechamento (close_date).'
        when v_estagio in ('Prospecting', 'Engaging') and (v_fech is not null or v_valor is not null)
          then 'Deal aberto não pode ter data nem valor de fechamento.'
        when v_estagio = 'Won' and (v_valor is null or v_valor <= 0)
          then 'Deal ganho sem valor de fechamento.'
        when v_estagio = 'Lost' and coalesce(v_valor, 0) <> 0
          then 'Deal perdido deve ter valor 0.'
        when v_fech is not null and v_abert is not null and v_fech < v_abert
          then 'A data de fechamento é anterior à de abertura.'
      end;
    end if;

    if v_motivo is null then
      v_vistos := v_vistos || v_id;          -- só linhas válidas contam para "código repetido"
    end if;

    if v_motivo is not null then
      v_recusas := v_recusas || jsonb_build_object('linha', v_num, 'motivo', v_motivo);
    elsif exists (select 1 from core_deals where opportunity_id = v_id) then
      v_ja := v_ja + 1;
    else
      v_aceitas := v_aceitas || jsonb_build_object(
        'opportunity_id', v_id, 'sales_agent', v_vend, 'product', v_prod, 'account', v_conta,
        'deal_stage', v_estagio, 'engage_date', v_abert, 'close_date', v_fech,
        'close_value', case when v_estagio = 'Lost' then 0 else v_valor end);
    end if;
  end loop;

  if not p_somente_conferir then
    insert into system_importacoes (usuario_id, arquivo_nome, arquivo_sha256, linhas_total, aceitas, ja_existiam,
                                    recusadas, recusas, correlation_id)
    values (u.id, p_arquivo_nome, lower(p_arquivo_sha256), v_total, 0, v_ja,
            jsonb_array_length(v_recusas), v_recusas, p_correlation_id)
    returning id into v_imp_id;

    insert into core_deals (opportunity_id, nome, vendedor_nome, produto_nome, conta_nome, estagio,
                            data_abertura, close_date, close_value, criado_em, criado_por, importacao_id)
    select x ->> 'opportunity_id',
           core_nome_padrao(x ->> 'account', x ->> 'product'),
           x ->> 'sales_agent', x ->> 'product', x ->> 'account', x ->> 'deal_stage',
           (x ->> 'engage_date')::date, (x ->> 'close_date')::date, (x ->> 'close_value')::integer,
           now(), u.id, v_imp_id
      from jsonb_array_elements(v_aceitas) x
    on conflict (opportunity_id) do nothing;
    get diagnostics v_inseridos = row_count;

    update system_importacoes
       set aceitas = v_inseridos,
           ja_existiam = v_ja + (jsonb_array_length(v_aceitas) - v_inseridos)
     where id = v_imp_id;
    perform system_registrar_evento('importacao', jsonb_build_object('importacao_id', v_imp_id, 'aceitas', v_inseridos,
                                    'recusadas', jsonb_array_length(v_recusas)));
  end if;

  return jsonb_build_object(
    'conferencia', p_somente_conferir,
    'importacao_id', v_imp_id,
    'linhas_total', v_total,
    'aceitas', case when p_somente_conferir then jsonb_array_length(v_aceitas) else v_inseridos end,
    'ja_existiam', case when p_somente_conferir then v_ja else v_ja + (jsonb_array_length(v_aceitas) - v_inseridos) end,
    'recusadas', jsonb_array_length(v_recusas),
    'recusas', v_recusas);
end $$;
