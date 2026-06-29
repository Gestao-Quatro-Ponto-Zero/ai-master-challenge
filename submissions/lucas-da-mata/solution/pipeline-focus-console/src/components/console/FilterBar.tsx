import { Search, X, Zap, Flame, Snowflake, UserCheck, Handshake, Telescope } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n-context";
import { cn } from "@/lib/utils";

export type QuickFilter =
  "act_now" | "high_score" | "cooling_risk" | "manager_review" | "engaging" | "prospecting";

export interface Filters {
  seller: string;
  manager: string;
  region: string;
  stage: string;
  priority: string;
  product: string;
  search: string;
  quick: QuickFilter[];
}

export const EMPTY_FILTERS: Filters = {
  seller: "all",
  manager: "all",
  region: "all",
  stage: "all",
  priority: "all",
  product: "all",
  search: "",
  quick: [],
};

const ALL = "all";

function FilterSelect({
  label,
  allLabel,
  value,
  options,
  onChange,
  getLabel,
}: {
  label: string;
  allLabel: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
  getLabel?: (v: string) => string;
}) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="h-9 min-w-[8.5rem] border-border bg-secondary/60 text-sm">
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent className="max-h-72">
        <SelectItem value={ALL}>{allLabel}</SelectItem>
        {options.map((o) => (
          <SelectItem key={o} value={o}>
            {getLabel ? getLabel(o) : o}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

export function FilterBar({
  filters,
  onChange,
  options,
  resultCount,
}: {
  filters: Filters;
  onChange: (f: Filters) => void;
  options: {
    sellers: string[];
    managers: string[];
    regions: string[];
    stages: string[];
    products: string[];
  };
  resultCount: number;
}) {
  const { t, num, stage, priority } = useI18n();
  const set = (k: keyof Filters, v: string) => onChange({ ...filters, [k]: v });
  const hasActive = Object.entries(filters).some(([k, v]) => {
    if (k === "search") return v !== "";
    if (k === "quick") return (v as QuickFilter[]).length > 0;
    return v !== ALL;
  });

  const all = (label: string) => t("filter.allSuffix", { label });

  const CHIPS: { id: QuickFilter; label: string; icon: typeof Zap }[] = [
    { id: "act_now", label: t("chips.actNow"), icon: Zap },
    { id: "high_score", label: t("chips.highScore"), icon: Flame },
    { id: "cooling_risk", label: t("chips.coolingRisk"), icon: Snowflake },
    { id: "manager_review", label: t("chips.managerReview"), icon: UserCheck },
    { id: "engaging", label: t("chips.engaging"), icon: Handshake },
    { id: "prospecting", label: t("chips.prospecting"), icon: Telescope },
  ];
  const toggleQuick = (id: QuickFilter) =>
    onChange({
      ...filters,
      quick: filters.quick.includes(id)
        ? filters.quick.filter((q) => q !== id)
        : [...filters.quick, id],
    });

  return (
    <div className="rounded-lg border border-border bg-card p-3 shadow-sm">
      <div className="-mx-1 mb-2.5 flex items-center gap-1.5 overflow-x-auto px-1 pb-1.5 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <span className="shrink-0 pr-0.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          {t("chips.label")}
        </span>
        {CHIPS.map((c) => {
          const active = filters.quick.includes(c.id);
          return (
            <button
              key={c.id}
              type="button"
              aria-pressed={active}
              onClick={() => toggleQuick(c.id)}
              className={cn(
                "inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
                active
                  ? "border-gold/60 bg-gold/15 text-gold"
                  : "border-border bg-secondary/50 text-muted-foreground hover:border-gold/40 hover:text-foreground",
              )}
            >
              <c.icon className="h-3.5 w-3.5" />
              {c.label}
            </button>
          );
        })}
      </div>
      <div className="grid grid-cols-1 items-center gap-2 md:grid-cols-2 xl:grid-cols-[minmax(16rem,1fr)_repeat(6,minmax(7.5rem,9.5rem))_auto]">
        <div className="relative min-w-0">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={filters.search}
            onChange={(e) => set("search", e.target.value)}
            placeholder={t("filter.search")}
            className="h-9 w-full rounded-md border border-border bg-secondary/60 pl-8 pr-3 text-sm text-foreground placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
        <FilterSelect
          label={t("filter.seller")}
          allLabel={all(t("filter.seller"))}
          value={filters.seller}
          options={options.sellers}
          onChange={(v) => set("seller", v)}
        />
        <FilterSelect
          label={t("filter.manager")}
          allLabel={all(t("filter.manager"))}
          value={filters.manager}
          options={options.managers}
          onChange={(v) => set("manager", v)}
        />
        <FilterSelect
          label={t("filter.region")}
          allLabel={all(t("filter.region"))}
          value={filters.region}
          options={options.regions}
          onChange={(v) => set("region", v)}
        />
        <FilterSelect
          label={t("filter.stage")}
          allLabel={all(t("filter.stage"))}
          value={filters.stage}
          options={options.stages}
          onChange={(v) => set("stage", v)}
          getLabel={(v) => stage(v)}
        />
        <FilterSelect
          label={t("filter.priority")}
          allLabel={all(t("filter.priority"))}
          value={filters.priority}
          options={["High", "Priority", "Watch", "Low"]}
          onChange={(v) => set("priority", v)}
          getLabel={(v) => priority(v)}
        />
        <FilterSelect
          label={t("filter.product")}
          allLabel={all(t("filter.product"))}
          value={filters.product}
          options={options.products}
          onChange={(v) => set("product", v)}
        />
        {hasActive && (
          <Button
            variant="ghost"
            size="sm"
            className="h-9 justify-start text-muted-foreground xl:justify-center"
            onClick={() => onChange(EMPTY_FILTERS)}
          >
            <X className="h-4 w-4" /> {t("filter.clear")}
          </Button>
        )}
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        {(() => {
          const parts = t("filter.showing", { n: "\u0000" }).split("\u0000");
          return (
            <>
              {parts[0]}
              <span className="tabular font-semibold text-foreground">{num(resultCount)}</span>
              {parts[1]}
            </>
          );
        })()}
      </p>
    </div>
  );
}
