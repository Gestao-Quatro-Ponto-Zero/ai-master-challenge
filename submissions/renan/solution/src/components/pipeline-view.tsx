import { X } from "lucide-react";
import Link from "next/link";
import { DealTable } from "@/components/deal-table";
import { asOptions, SelectField, SubmitButton } from "@/components/select-field";
import { PageHeader, Pill } from "@/components/ui";
import { count, usd } from "@/lib/format";
import { applyFilters, filterQuery, MOMENTUM_ORDER, options, parseFilters, pipeline, summarize, type Filters } from "@/lib/pipeline";
import { MOMENTUM_LABEL } from "@/lib/scoring/score";

const PAGE = 50;

type Params = Record<string, string | string[] | undefined>;

/** Lista filtrável do pipeline, usada em /pipeline e em /parados (momento fixo). */
export function PipelineView({
  params,
  basePath,
  title,
  description,
  fixed = {},
}: {
  params: Params;
  basePath: "/pipeline" | "/parados";
  title: string;
  description?: React.ReactNode;
  fixed?: Filters;
}) {
  const filters = { ...parseFilters(params), ...fixed };
  const limit = Math.max(PAGE, Math.min(Number(params.limite) || PAGE, 5000));
  const rows = applyFilters(pipeline, filters);
  const { active, stalled, activeExpectedValue, withoutAccount } = summarize(rows);
  const shown = rows.slice(0, limit);
  const own = { ...filters, momentum: fixed.momentum ? undefined : filters.momentum };

  return (
    <div className="space-y-6">
      <PageHeader title={title} description={description} />

      <form method="get" className="card grid grid-cols-1 items-end gap-3 p-4 sm:grid-cols-[repeat(auto-fit,minmax(10rem,1fr))]">
        <label className="flex flex-col gap-1.5 sm:col-span-2">
          <span className="field">Busca</span>
          <input
            name="q"
            type="search"
            defaultValue={filters.query}
            placeholder="Código, conta, vendedor…"
            className="h-11 w-full rounded-full border border-line bg-surface px-4 text-[15px] placeholder:text-secondary focus:border-moment focus:outline-none"
          />
        </label>
        <SelectField name="vendedor" label="Vendedor" value={filters.agent} options={asOptions(options.agents)} allLabel="Todos" />
        <SelectField name="manager" label="Manager" value={filters.manager} options={asOptions(options.managers)} allLabel="Todos" />
        <SelectField name="escritorio" label="Escritório" value={filters.office} options={asOptions(options.offices)} allLabel="Todos" />
        <SelectField name="produto" label="Produto" value={filters.product} options={asOptions(options.products)} allLabel="Todos" />
        {!fixed.momentum && (
          <SelectField
            name="momento"
            label="Momento"
            value={filters.momentum}
            options={MOMENTUM_ORDER.map((m) => ({ value: m, label: MOMENTUM_LABEL[m] }))}
            allLabel="Todos"
          />
        )}
        <div className="flex items-center gap-2">
          <SubmitButton>Filtrar</SubmitButton>
          <Link href={basePath} className="inline-flex h-11 items-center gap-1 rounded-full px-4 text-[14px] text-secondary hover:bg-hover hover:text-primary">
            <X className="size-4" aria-hidden /> Limpar
          </Link>
        </div>
      </form>

      <div className="flex flex-wrap items-center gap-2">
        <Pill>{count(rows.length)} deals</Pill>
        {!fixed.momentum && <Pill>{count(active.length)} ativos · {usd(activeExpectedValue)} esperados</Pill>}
        <Pill>
          <span className="text-stalled">{count(stalled.length)} parados</span>
        </Pill>
        <Pill>{count(withoutAccount)} sem conta</Pill>
      </div>

      {rows.length === 0 ? (
        <p className="card p-6 text-secondary">Nenhum deal com esses filtros.</p>
      ) : (
        <DealTable rows={shown} caption={`${title}: deals ordenados por valor esperado`} />
      )}

      {rows.length > shown.length && (
        <div className="flex justify-center">
          <Link
            href={`${basePath}${filterQuery(own, { limite: String(limit + PAGE) })}`}
            scroll={false}
            className="inline-flex h-11 items-center rounded-full border border-line bg-surface px-5 text-[14px] font-semibold hover:bg-hover"
          >
            Mostrar mais {Math.min(PAGE, rows.length - shown.length)} de {count(rows.length - shown.length)} restantes
          </Link>
        </div>
      )}
    </div>
  );
}
