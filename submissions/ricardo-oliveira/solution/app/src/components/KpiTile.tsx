export function KpiTile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="card p-4">
      <div className="text-xs font-semibold text-grey uppercase tracking-wide">{label}</div>
      <div className="text-2xl font-extrabold mt-1">{value}</div>
      {hint && <div className="text-xs text-grey mt-1">{hint}</div>}
    </div>
  );
}
