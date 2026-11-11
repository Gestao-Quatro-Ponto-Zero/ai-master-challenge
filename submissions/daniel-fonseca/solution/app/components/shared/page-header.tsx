/** Título da área + conclusão em serifa ("headline first", PRD §4.1 e §6.1). */
export function PageHeader({ eyebrow, title, lead, children }: { eyebrow?: string; title: string; lead?: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-4 pb-6">
      <div className="space-y-2">
        {eyebrow ? <p className="font-mono text-xs uppercase tracking-[0.14em] text-text-3">{eyebrow}</p> : null}
        <h1 className="font-serif text-3xl leading-tight text-text-1 sm:text-4xl">{title}</h1>
        {lead ? <p className="max-w-3xl text-base leading-relaxed text-text-2">{lead}</p> : null}
      </div>
      {children}
    </div>
  )
}
