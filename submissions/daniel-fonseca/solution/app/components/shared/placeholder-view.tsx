/** Marcador da sessão base: cada frente substitui pelo conteúdo do PRD. */
export function PlaceholderView({ title, owner, items }: { title: string; owner: "Frente A" | "Frente B"; items: string[] }) {
  return (
    <section className="rounded-xl border border-dashed border-border bg-surface/60 p-6">
      <p className="font-mono text-xs uppercase tracking-[0.14em] text-text-3">Em construção · {owner}</p>
      <h2 className="mt-2 font-serif text-2xl text-text-1">{title}</h2>
      <ul className="mt-4 list-disc space-y-1 pl-5 text-sm text-text-2">
        {items.map((i) => (
          <li key={i}>{i}</li>
        ))}
      </ul>
    </section>
  )
}
