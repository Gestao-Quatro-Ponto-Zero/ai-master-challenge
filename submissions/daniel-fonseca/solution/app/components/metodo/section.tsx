import { Headline } from "@/components/shared/headline"

/** Bloco de "Como foi feito": rótulo, conclusão em serifa, texto de apoio e conteúdo. */
export function Section({ eyebrow, title, lead, children }: { eyebrow: string; title: string; lead?: string; children: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-4">
      <div className="space-y-2">
        <p className="font-mono text-xs uppercase tracking-[0.14em] text-text-3">{eyebrow}</p>
        <Headline>{title}</Headline>
        {lead ? <p className="max-w-3xl text-sm leading-relaxed text-text-2">{lead}</p> : null}
      </div>
      {children}
    </section>
  )
}
