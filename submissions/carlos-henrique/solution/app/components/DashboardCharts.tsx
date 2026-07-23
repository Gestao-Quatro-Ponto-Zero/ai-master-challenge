"use client";

import { Bar, BarChart, CartesianGrid, Cell, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatDecimalPtBr, formatIntegerPtBr, formatStructuredLabel } from "@/lib/format";

type Datum = Record<string, string | number>;
const palette = ["#315f8c", "#b68433", "#c66b3d", "#708253", "#a85d76", "#7895b2"];
const compactChartLabels: Record<string, string> = { READY_FOR_REVIEW: "Pronto p/ revisão", VALID_WITH_WARNING: "Válido c/ alerta" };
function formatChartLabel(value: string): string { return compactChartLabels[value] ?? formatStructuredLabel(value); }
function formatAxisNumber(value: number): string { return Number.isInteger(value) ? formatIntegerPtBr(value) : formatDecimalPtBr(value); }

function ChartFrame({ title, subtitle, children, summary }: { title: string; subtitle: string; children: React.ReactNode; summary: string }) {
  return <figure className="panel min-w-0 p-5"><figcaption><h3 className="font-semibold">{title}</h3><p className="mt-1 text-sm text-muted">{subtitle}</p></figcaption><div className="mt-5 h-72" aria-hidden>{children}</div><p className="mt-3 text-xs leading-5 text-muted">Resumo do gráfico: {summary}</p></figure>;
}

export function SimpleBarChart({ data, category, value, title, subtitle, summary, color = "#315f8c" }: { data: Datum[]; category: string; value: string; title: string; subtitle: string; summary: string; color?: string }) {
  return <ChartFrame title={title} subtitle={subtitle} summary={summary}><ResponsiveContainer width="100%" height="100%"><BarChart data={data} layout="vertical" margin={{ left: 18, right: 24 }}><CartesianGrid stroke="#e7ebf1" horizontal={false} /><XAxis type="number" tick={{ fontSize: 11 }} domain={[0, "dataMax"]} tickFormatter={(item) => formatAxisNumber(Number(item))} /><YAxis type="category" dataKey={category} width={112} tick={{ fontSize: 10 }} tickFormatter={(item) => formatStructuredLabel(String(item))} /><Tooltip formatter={(item) => formatDecimalPtBr(Number(item))} labelFormatter={(label) => formatChartLabel(String(label))} /><Bar dataKey={value} fill={color} radius={[0, 4, 4, 0]} /></BarChart></ResponsiveContainer></ChartFrame>;
}

export function MultiColorBarChart({ data, category, value, title, subtitle, summary }: { data: Datum[]; category: string; value: string; title: string; subtitle: string; summary: string }) {
  return <ChartFrame title={title} subtitle={subtitle} summary={summary}><ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ left: 4, right: 12 }}><CartesianGrid stroke="#e7ebf1" vertical={false} /><XAxis dataKey={category} tick={{ fontSize: 10 }} tickFormatter={(item) => formatChartLabel(String(item))} /><YAxis tick={{ fontSize: 11 }} domain={[0, "dataMax"]} tickFormatter={(item) => formatAxisNumber(Number(item))} /><Tooltip formatter={(item) => formatDecimalPtBr(Number(item))} labelFormatter={(label) => formatChartLabel(String(label))} /><Bar dataKey={value} radius={[4, 4, 0, 0]}>{data.map((_, index) => <Cell key={index} fill={palette[index % palette.length]} />)}</Bar></BarChart></ResponsiveContainer></ChartFrame>;
}

export function GroupedSampleChart({ data }: { data: Array<{ experiment: string; available: number; required: number }> }) {
  return <ChartFrame title="Amostra disponível versus necessária" subtitle="Contas anônimas elegíveis comparadas à necessidade ajustada por atrito" summary="Somente o EXP006 possui mais contas disponíveis do que sua necessidade ajustada."><ResponsiveContainer width="100%" height="100%"><BarChart data={data} margin={{ left: 4, right: 12 }}><CartesianGrid stroke="#e7ebf1" vertical={false} /><XAxis dataKey="experiment" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 11 }} domain={[0, "dataMax"]} tickFormatter={(item) => formatAxisNumber(Number(item))} /><Tooltip formatter={(item) => formatDecimalPtBr(Number(item))} /><Legend /><Bar dataKey="available" name="Disponível" fill="#315f8c" radius={[4, 4, 0, 0]} /><Bar dataKey="required" name="Necessária" fill="#d7b879" stroke="#8b6725" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></ChartFrame>;
}
