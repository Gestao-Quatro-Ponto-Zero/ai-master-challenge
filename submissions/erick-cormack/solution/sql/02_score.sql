-- Lead Scorer — lógica de score, 100% em SQL.
-- Por que assim: o score se recalcula sozinho quando os dados mudam, e qualquer pessoa
-- pode auditar a regra lendo este arquivo.
--
-- Achados que sustentam a regra (ver analise/analise_exploratoria.ipynb):
--   * produto, setor, região, manager e vendedor NÃO preveem ganho (backtest AUC < 0,5; logística p = 0,82)
--   * o tempo prevê: perdas se concentram nos primeiros 14 dias e nenhum deal fechou após 138 dias
--   * o preço de lista é um ótimo proxy do valor fechado (mediana fechado/lista = 1,00)

-- 1) Curva de chance de ganho por idade:
--    P(ganho | o deal já sobreviveu X dias sem fechar), calculada só com deals fechados.
create or replace view public.v_curva_ganho
with (security_invoker = true) as
with fechados as (
  select (close_date - engage_date) as ciclo,
         (deal_stage = 'Won')::int  as ganho
  from public.sales_pipeline
  where deal_stage in ('Won', 'Lost')
)
select g.idade,
       count(f.ciclo)                  as n_sobreviventes,
       round(avg(f.ganho)::numeric, 4) as p_ganho
from public.parametros p
cross join lateral generate_series(0, p.ciclo_max_dias) as g(idade)
left join fechados f on f.ciclo > g.idade
where p.id = 1
group by g.idade
order by g.idade;

-- 2) Um deal por linha, com fila, chance, valor esperado, score, prazo e motivos.
create or replace view public.v_deals_score
with (security_invoker = true) as
with par as (
  select * from public.parametros where id = 1
),
curva as (
  select * from public.v_curva_ganho
),
idade_confiavel as (
  -- Na cauda da curva há poucos deals; acima daqui, repete o último valor com amostra suficiente.
  select max(c.idade) as idade_max
  from curva c, par
  where c.n_sobreviventes >= par.amostra_minima
),
taxa_base as (
  select round(avg((deal_stage = 'Won')::int)::numeric, 4) as p
  from public.sales_pipeline
  where deal_stage in ('Won', 'Lost')
),
d as (
  select sp.opportunity_id, sp.sales_agent, sp.product, sp.account, sp.deal_stage,
         sp.engage_date, sp.close_date, sp.close_value,
         st.manager, st.regional_office,
         pr.series, pr.sales_price,
         a.sector, a.revenue, a.employees, a.office_location,
         case when sp.engage_date is not null then par.data_referencia - sp.engage_date end as idade_dias,
         par.ciclo_max_dias, par.fase_risco_dias, par.reta_final_dias,
         case when sp.account is not null
              then count(*) over (partition by sp.sales_agent, sp.product, sp.account, sp.engage_date) > 1
              else false end as possivel_duplicata
  from public.sales_pipeline sp
  join public.sales_teams st on st.sales_agent = sp.sales_agent
  join public.products    pr on pr.product     = sp.product
  left join public.accounts a on a.account     = sp.account
  cross join par
),
filas as (
  select d.*,
         case
           when d.deal_stage in ('Won', 'Lost')      then 'fechado'
           when d.deal_stage = 'Prospecting'         then 'prospectar'
           when d.idade_dias > d.ciclo_max_dias      then 'requalificar'
           else 'focar'
         end as fila
  from d
),
chance as (
  select f.*,
         case f.fila
           when 'focar'      then (select c.p_ganho from curva c, idade_confiavel ic
                                   where c.idade = least(f.idade_dias, ic.idade_max))
           when 'prospectar' then (select p from taxa_base)
         end as p_ganho
  from filas f
),
valor as (
  select c.*,
         round(c.p_ganho * c.sales_price, 2) as valor_esperado
  from chance c
),
pontuado as (
  -- Score 0–100 em escala logarítmica do valor esperado, dentro de cada fila.
  -- Log porque o valor varia ~500x entre produtos; em escala linear quase tudo seria zero.
  select v.*,
         case when v.valor_esperado is not null then
           round(100 * (ln(v.valor_esperado) - min(ln(v.valor_esperado)) over (partition by v.fila))
                 / nullif(max(ln(v.valor_esperado)) over (partition by v.fila)
                          - min(ln(v.valor_esperado)) over (partition by v.fila), 0))::int
         end as score
  from valor v
)
select p.opportunity_id, p.fila, p.score, p.p_ganho, p.valor_esperado,
       p.sales_agent, p.manager, p.regional_office,
       p.product, p.series, p.sales_price,
       p.account, p.sector, p.revenue, p.employees, p.office_location,
       p.deal_stage, p.engage_date, p.close_date, p.close_value, p.idade_dias,
       case when p.fila = 'focar' then p.engage_date + p.ciclo_max_dias end as prazo_limite,
       case when p.fila = 'focar' then p.ciclo_max_dias - p.idade_dias end as dias_ate_limite,
       case
         when p.fila <> 'focar'                      then null
         when p.idade_dias <= p.fase_risco_dias      then 'fase de risco'
         when p.idade_dias >= p.reta_final_dias      then 'reta final'
         else 'em andamento'
       end as momento,
       (p.account is null)  as sem_conta,
       p.possivel_duplicata,
       array_remove(array[
         case p.fila
           when 'focar' then format('Valor esperado US$ %s = chance de %s%% × preço de lista US$ %s (%s)',
                                    replace(to_char(p.valor_esperado, 'FM999G999'), ',', '.'), round(p.p_ganho * 100),
                                    replace(to_char(p.sales_price, 'FM999G999'), ',', '.'), p.product)
           when 'prospectar' then format('Ainda não engajado. Valor de lista US$ %s (%s); chance média de %s%% se engajar',
                                         replace(to_char(p.sales_price, 'FM999G999'), ',', '.'), p.product, round(p.p_ganho * 100))
           when 'requalificar' then format('Parado há %s dias: %s dias além do maior ciclo já fechado (%s dias). Nenhum deal fechou depois disso',
                                           p.idade_dias, p.idade_dias - p.ciclo_max_dias, p.ciclo_max_dias)
         end,
         case
           when p.fila = 'focar' and p.idade_dias <= p.fase_risco_dias then
             format('Aberto há %s dias: ainda na fase de maior risco. A maioria das perdas acontece até o dia %s',
                    p.idade_dias, p.fase_risco_dias)
           when p.fila = 'focar' and p.idade_dias = p.ciclo_max_dias then
             format('Aberto há %s dias: hoje é o último dia do limite histórico. Decidir agora: fechar ou encerrar',
                    p.idade_dias)
           when p.fila = 'focar' and p.idade_dias >= p.reta_final_dias then
             format('Aberto há %s dias: reta final. Faltam %s dias para o limite histórico de %s dias',
                    p.idade_dias, p.ciclo_max_dias - p.idade_dias, p.ciclo_max_dias)
           when p.fila = 'focar' then
             format('Aberto há %s dias: já passou da fase de maior risco; quem chega aqui ganha mais que a média',
                    p.idade_dias)
         end,
         case when p.fila = 'requalificar' then
           format('Valor de lista US$ %s (%s) travado no pipeline', replace(to_char(p.sales_price, 'FM999G999'), ',', '.'), p.product)
         end,
         case when p.fila <> 'fechado' and p.account is null then 'Conta não cadastrada: completar no CRM' end,
         case when p.fila <> 'fechado' and p.possivel_duplicata then 'Possível duplicata: mesmo vendedor, produto, conta e data de engajamento' end
       ], null) as motivos
from pontuado p;

-- 3) Resumo por vendedor (visão do gestor).
create or replace view public.v_resumo_vendedor
with (security_invoker = true) as
select sales_agent, manager, regional_office,
       count(*) filter (where fila = 'focar')                          as deals_focar,
       coalesce(sum(valor_esperado) filter (where fila = 'focar'), 0)  as valor_esperado_focar,
       count(*) filter (where fila = 'focar' and momento = 'reta final') as deals_reta_final,
       count(*) filter (where fila = 'requalificar')                   as deals_requalificar,
       coalesce(sum(sales_price) filter (where fila = 'requalificar'), 0) as valor_parado,
       count(*) filter (where fila = 'prospectar')                     as deals_prospectar,
       count(*) filter (where fila <> 'fechado' and sem_conta)         as deals_sem_conta,
       count(*) filter (where fila <> 'fechado' and possivel_duplicata) as deals_possivel_duplicata,
       count(*) filter (where deal_stage = 'Won')                      as ganhos,
       count(*) filter (where deal_stage = 'Lost')                     as perdidos
from public.v_deals_score
group by sales_agent, manager, regional_office;

-- Leitura liberada para o app (acesso anônimo, sem login).
grant select on public.v_curva_ganho, public.v_deals_score, public.v_resumo_vendedor to anon, authenticated;

-- Conferência esperada (mesmos números de scripts/gabarito_score.py):
--   focar 298 | requalificar 1291 | prospectar 500 | fechado 6711
select fila, count(*) as deals, sum(sales_price) as valor_lista, sum(valor_esperado) as valor_esperado,
       round(avg(score), 2) as score_medio
from public.v_deals_score group by fila order by fila;
