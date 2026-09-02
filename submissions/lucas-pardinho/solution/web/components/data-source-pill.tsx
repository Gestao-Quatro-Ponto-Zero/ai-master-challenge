import { Database, FlaskConical } from "lucide-react";
import type { DataStatus } from "@/lib/types";

export function DataSourcePill({ status }: { status: DataStatus }) {
  const generated = status.source === "generated";
  const Icon = generated ? Database : FlaskConical;
  return (
    <span className={`data-source-pill ${generated ? "live" : "sample"}`}>
      <Icon size={14} aria-hidden="true" />
      {generated ? "Dados reais · pipeline processado" : "Amostra controlada de desenvolvimento"}
    </span>
  );
}
