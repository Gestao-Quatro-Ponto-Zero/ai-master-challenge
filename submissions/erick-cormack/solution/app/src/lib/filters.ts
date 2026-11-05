import { fallback } from "@tanstack/zod-adapter";
import { z } from "zod";

export const filterSearchSchema = z.object({
  regiao: fallback(z.string(), "").default(""),
  manager: fallback(z.string(), "").default(""),
  vendedor: fallback(z.string(), "").default(""),
});

export type Filters = z.infer<typeof filterSearchSchema>;

type Scoped = {
  regional_office: string | null;
  manager: string | null;
  sales_agent: string | null;
};

export function matchesFilters(row: Scoped, f: Filters): boolean {
  if (f.regiao && row.regional_office !== f.regiao) return false;
  if (f.manager && row.manager !== f.manager) return false;
  if (f.vendedor && row.sales_agent !== f.vendedor) return false;
  return true;
}
