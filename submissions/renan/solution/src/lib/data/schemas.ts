import { z } from "zod";

const optionalText = z
  .string()
  .transform((v) => v.trim())
  .transform((v) => (v === "" ? null : v));

const isoDate = z
  .string()
  .regex(/^(\d{4}-\d{2}-\d{2})?$/, "data fora do formato YYYY-MM-DD")
  .transform((v) => (v === "" ? null : v));

export const accountRow = z.object({
  account: z.string().min(1),
  sector: z.string().min(1),
  year_established: z.coerce.number().int(),
  revenue: z.coerce.number(),
  employees: z.coerce.number().int(),
  office_location: z.string(),
  subsidiary_of: optionalText,
});

export const productRow = z.object({
  product: z.string().min(1),
  series: z.string().min(1),
  sales_price: z.coerce.number().positive(),
});

export const salesTeamRow = z.object({
  sales_agent: z.string().min(1),
  manager: z.string().min(1),
  regional_office: z.string().min(1),
});

export const pipelineRow = z.object({
  opportunity_id: z.string().min(1),
  sales_agent: z.string().min(1),
  product: z.string().min(1),
  account: optionalText,
  deal_stage: z.enum(["Prospecting", "Engaging", "Won", "Lost"]),
  engage_date: isoDate,
  close_date: isoDate,
  close_value: z
    .string()
    .transform((v) => (v.trim() === "" ? null : Number(v)))
    .pipe(z.number().nullable()),
});

export type AccountRow = z.infer<typeof accountRow>;
export type ProductRow = z.infer<typeof productRow>;
export type SalesTeamRow = z.infer<typeof salesTeamRow>;
export type PipelineRow = z.infer<typeof pipelineRow>;
