import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

type Tone = "neutral" | "success" | "warning";

const tones: Record<Tone, string> = {
  neutral: "bg-muted text-muted-foreground",
  success: "bg-success-soft text-success-strong",
  warning: "bg-warning-soft text-warning-foreground",
};

export function Chip({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={cn("inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium", tones[tone])}>
      {children}
    </span>
  );
}

export function MomentoChip({ momento }: { momento: string | null }) {
  if (!momento) return null;
  const tone: Tone = momento === "reta final" ? "warning" : momento === "em andamento" ? "success" : "neutral";
  return <Chip tone={tone}>{momento}</Chip>;
}

export function AlertChips({ semConta, duplicata }: { semConta: boolean | null; duplicata: boolean | null }) {
  if (!semConta && !duplicata) return <span className="text-muted-foreground">—</span>;
  return (
    <div className="flex flex-wrap gap-1">
      {semConta && <Chip tone="warning">Conta não cadastrada</Chip>}
      {duplicata && <Chip tone="warning">Possível duplicata</Chip>}
    </div>
  );
}

export function ContaCell({ account }: { account: string | null }) {
  return account ? <span>{account}</span> : <Chip>sem conta</Chip>;
}

export function ScoreCell({ score }: { score: number | null }) {
  const s = score ?? 0;
  return (
    <div className="w-14">
      <div className="font-numeric text-2xl font-semibold leading-none tabular-nums text-foreground">{s}</div>
      <div className="mt-1 h-1 w-full rounded-full bg-muted">
        <div className="h-1 rounded-full bg-primary" style={{ width: `${Math.max(0, Math.min(100, s))}%` }} />
      </div>
    </div>
  );
}
