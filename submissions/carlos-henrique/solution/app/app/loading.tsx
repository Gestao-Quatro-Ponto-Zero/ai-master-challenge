export default function Loading() {
  return (
    <div className="space-y-6" aria-live="polite" aria-busy="true">
      <div className="h-28 animate-pulse rounded-2xl bg-slate-200" />
      <div className="grid gap-4 md:grid-cols-3">
        {[0, 1, 2].map((item) => <div key={item} className="h-36 animate-pulse rounded-2xl bg-slate-200" />)}
      </div>
      <span className="sr-only">Loading local dashboard data</span>
    </div>
  );
}
