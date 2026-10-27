import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

export function PageHeader({ title, description, actions }: { title: string; description?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-6">
      <div className="min-w-0">
        <h1 className="text-[clamp(30px,3.4vw,44px)] leading-[1.05] font-semibold tracking-[-0.03em]">{title}</h1>
        {description && <p className="mt-2 max-w-[68ch] text-[16px] text-secondary">{description}</p>}
      </div>
      {actions}
    </div>
  );
}

/** Card de indicador: ícone em círculo, rótulo, número grande e legenda. */
export function StatCard({
  icon: Icon,
  label,
  value,
  caption,
  href,
  tone = "default",
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  caption?: string;
  href?: string;
  tone?: "default" | "moment" | "stalled";
}) {
  const toneText = tone === "stalled" ? "text-stalled" : tone === "moment" ? "text-moment" : "text-primary";
  const toneBg = tone === "stalled" ? "bg-stalled-soft" : tone === "moment" ? "bg-moment-soft" : "bg-hover";
  const body = (
    <>
      <div className="flex items-center gap-3">
        <span className={`grid size-9 place-items-center rounded-full ${toneBg} ${toneText}`}>
          <Icon className="size-[18px]" aria-hidden />
        </span>
        <span className="text-[15px] font-semibold">{label}</span>
      </div>
      <p className={`mt-4 text-[30px] leading-none font-bold tracking-[-0.03em] tabular-nums ${toneText}`}>{value}</p>
      {caption && <p className="mt-2 text-[13px] text-secondary">{caption}</p>}
    </>
  );
  const className = "card block p-5 transition-[transform,box-shadow,border-color]";
  return href ? (
    <Link href={href} className={`${className} hover:-translate-y-0.5 hover:border-secondary/50 hover:shadow-md motion-reduce:hover:translate-y-0`}>
      {body}
    </Link>
  ) : (
    <div className={className}>{body}</div>
  );
}

/** Anel de progresso em CSS (conic-gradient). */
export function Ring({ value, label, tone = "stalled" }: { value: number; label: string; tone?: "stalled" | "moment" }) {
  const color = tone === "stalled" ? "var(--stalled)" : "var(--moment)";
  const percent = Math.round(value * 100);
  return (
    <div className="flex flex-col items-center gap-2">
      <div
        role="img"
        aria-label={`${percent}% ${label}`}
        className="grid size-[112px] place-items-center rounded-full"
        style={{ background: `conic-gradient(${color} ${value * 360}deg, var(--track) 0deg)` }}
      >
        <div className="grid size-[92px] place-items-center rounded-full bg-ground">
          <span className={`text-[26px] font-bold tracking-[-0.03em] tabular-nums ${tone === "stalled" ? "text-stalled" : "text-moment"}`}>
            {percent}%
          </span>
        </div>
      </div>
      <span className="max-w-[16ch] text-center text-[12px] text-secondary">{label}</span>
    </div>
  );
}

/** Barra horizontal simples (0–1). */
export function Bar({ value, tone = "moment", label }: { value: number; tone?: "moment" | "stalled" | "secondary"; label?: string }) {
  const color = tone === "stalled" ? "bg-stalled" : tone === "secondary" ? "bg-secondary" : "bg-moment";
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-track" role={label ? "img" : undefined} aria-label={label}>
      <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }} />
    </div>
  );
}

export function SectionTitle({ title, action }: { title: string; action?: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4">
      <h2 className="text-[20px] font-semibold tracking-[-0.02em]">{title}</h2>
      {action}
    </div>
  );
}

export function Pill({ children }: { children: ReactNode }) {
  return <span className="inline-flex items-center rounded-full border border-line px-2.5 py-1 text-[12px] text-secondary">{children}</span>;
}
