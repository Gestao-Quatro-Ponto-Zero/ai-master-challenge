"use client"

export default function MetodoError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <section className="flex flex-col items-start gap-3 rounded-xl border border-border bg-surface p-6">
      <h2 className="font-serif text-2xl text-text-1">Os dados desta seção não carregaram</h2>
      <p className="text-sm leading-relaxed text-text-2">A leitura do banco de dados falhou. Tente de novo em alguns segundos.</p>
      <button type="button" onClick={reset} className="rounded-full bg-text-1 px-4 py-2 text-sm font-medium text-bg">
        Tentar de novo
      </button>
    </section>
  )
}
