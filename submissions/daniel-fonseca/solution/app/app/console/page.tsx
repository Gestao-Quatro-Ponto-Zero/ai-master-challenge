import type { Metadata } from "next"
import { Suspense } from "react"

import { PageHeader } from "@/components/shared/page-header"
import { PlaceholderView } from "@/components/shared/placeholder-view"
import { ViewToggle, ViewToggleFallback } from "@/components/shared/view-toggle"
import { CONSOLE_VIEWS, readView } from "@/lib/views"

export const metadata: Metadata = { title: "Console" }

export default function ConsolePage({ searchParams }: PageProps<"/console">) {
  return (
    <>
      <PageHeader eyebrow="Console" title="A triagem funcionando com tickets reais">
        <Suspense fallback={<ViewToggleFallback options={[...CONSOLE_VIEWS]} />}>
          <ViewToggle param="aba" options={[...CONSOLE_VIEWS]} defaultValue="triagem" label="Aba do console" />
        </Suspense>
      </PageHeader>
      <Suspense fallback={null}>
        <ConsoleView searchParams={searchParams} />
      </Suspense>
    </>
  )
}

async function ConsoleView({ searchParams }: { searchParams: PageProps<"/console">["searchParams"] }) {
  const view = readView((await searchParams).aba, CONSOLE_VIEWS)
  if (view === "fila") return <PlaceholderView owner="Frente B" title="Fila de revisão humana" items={["Lista + detalhe", "Rascunho editável e checagens", "Aprovar · Editar e aprovar · Rejeitar", "Efeito 'aprendeu'"]} />
  if (view === "caixa") return <PlaceholderView owner="Frente B" title="Caixa de mensagens" items={["Slack simulado", "Filtro Tickets · Sistema", "Marcar como lida e assumir"]} />
  return <PlaceholderView owner="Frente B" title="Triagem" items={["Sortear do holdout ou escrever em inglês", "Caminho, confiança, votos, 5 casos parecidos", "Etapas com tempos, rótulo real, histórico", "Modo offline"]} />
}
