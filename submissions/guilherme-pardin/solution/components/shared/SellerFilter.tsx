"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
} from "@/components/ui/select";
import { agents } from "@/lib/data";
import type { AgentProfile } from "@/lib/types";
import { formatPercent } from "@/lib/utils";

export function SellerFilter({
  value,
  onChange,
  includeAll = true,
  placeholder = "Todos os vendedores",
  agentPool,
}: {
  value: string;
  onChange: (value: string) => void;
  includeAll?: boolean;
  placeholder?: string;
  agentPool?: AgentProfile[];
}) {
  const list = agentPool ?? agents;
  return (
    <Select value={value} onValueChange={(v) => onChange(v ?? "__all")}>
      <SelectTrigger className="w-[240px] bg-white">
        <span className="truncate">
          {value === "__all" ? placeholder : value}
        </span>
      </SelectTrigger>
      <SelectContent>
        {includeAll && <SelectItem value="__all">{placeholder}</SelectItem>}
        {list.map((a) => (
          <SelectItem key={a.name} value={a.name}>
            <span className="flex items-center gap-2">
              <span>{a.name}</span>
              <span className="text-xs text-slate-400">
                Conv. {formatPercent(a.overallWr)}
              </span>
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
