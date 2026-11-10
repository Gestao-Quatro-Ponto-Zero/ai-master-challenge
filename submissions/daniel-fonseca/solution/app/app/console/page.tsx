import type { Metadata } from "next"
import { Suspense } from "react"

import { getHoldoutById, getInbox, getQueue } from "@/app/console/_data"
import { ConsoleSkeleton } from "@/components/console/console-skeleton"
import { InboxView } from "@/components/console/inbox-view"
import { QueueView } from "@/components/console/queue-view"
import { TriageView } from "@/components/console/triage-view"
import { PageHeader } from "@/components/shared/page-header"
import { ViewToggle, ViewToggleFallback } from "@/components/shared/view-toggle"
import { env } from "@/lib/env"
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
      <Suspense fallback={<ConsoleSkeleton />}>
        <ConsoleView searchParams={searchParams} />
      </Suspense>
    </>
  )
}

const first = (v: string | string[] | undefined) => (Array.isArray(v) ? v[0] : v)

async function ConsoleView({ searchParams }: { searchParams: PageProps<"/console">["searchParams"] }) {
  const sp = await searchParams
  const view = readView(sp.aba, CONSOLE_VIEWS)
  const item = Number(first(sp.item)) || null

  if (view === "fila") {
    const queue = await getQueue()
    return <QueueView pending={queue.pending} decided={queue.decided} initialId={item} />
  }
  if (view === "caixa") {
    const inbox = await getInbox()
    return <InboxView items={inbox} initialId={item} />
  }
  const ds2 = Number(first(sp.ds2))
  const initialTicket = ds2 ? await getHoldoutById(ds2) : null
  return <TriageView key={initialTicket?.id ?? "novo"} freeTextEnabled={env.freeTextEnabled()} initialTicket={initialTicket} learned={first(sp.origem) === "aprendeu"} />
}
