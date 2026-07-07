import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Tier } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

function toPtNumber(n: number, digits = 1): string {
  return n.toFixed(digits).replace(".", ",");
}

export function formatMoney(value: number): string {
  if (value >= 1_000_000) return `R$ ${toPtNumber(value / 1_000_000)}M`;
  if (value >= 1_000) return `R$ ${toPtNumber(value / 1_000)}K`;
  return `R$ ${Math.round(value).toLocaleString("pt-BR")}`;
}

export function formatPercent(value: number, digits = 0): string {
  return `${toPtNumber(value * 100, digits)}%`;
}

export const stageLabel: Record<string, string> = {
  Prospecting: "Prospecção",
  Engaging: "Em negociação",
  Won: "Vendas Fechadas",
  Lost: "Perdidos",
};

export function initials(name: string): string {
  if (!name) return "??";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export const tierColor: Record<
  Tier,
  { bg: string; text: string; border: string; solid: string; hex: string }
> = {
  hot: {
    bg: "bg-emerald-50",
    text: "text-emerald-700",
    border: "border-emerald-200",
    solid: "bg-emerald-500",
    hex: "#10b981",
  },
  warm: {
    bg: "bg-amber-50",
    text: "text-amber-700",
    border: "border-amber-200",
    solid: "bg-amber-500",
    hex: "#f59e0b",
  },
  cold: {
    bg: "bg-slate-100",
    text: "text-slate-600",
    border: "border-slate-300",
    solid: "bg-slate-500",
    hex: "#64748b",
  },
  at_risk: {
    bg: "bg-red-50",
    text: "text-red-700",
    border: "border-red-200",
    solid: "bg-red-500",
    hex: "#ef4444",
  },
};

const AVATAR_PALETTE = [
  "bg-blue-500",
  "bg-indigo-500",
  "bg-emerald-500",
  "bg-rose-500",
  "bg-amber-500",
  "bg-fuchsia-500",
  "bg-teal-500",
  "bg-cyan-500",
];

export function avatarBg(seed: string): string {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) | 0;
  return AVATAR_PALETTE[Math.abs(h) % AVATAR_PALETTE.length];
}
