import type { Metadata } from "next"
import { Suspense } from "react"

import { TicketsApp } from "@/components/tickets/tickets-app"
import { env } from "@/lib/env"

export const metadata: Metadata = { title: "Tickets" }

export default function TicketsPage() {
  return (
    <Suspense fallback={<div className="h-[calc(100dvh-15rem)] rounded-xl border border-border bg-surface md:h-[calc(100dvh-13rem)]" aria-busy="true" />}>
      <TicketsApp freeTextEnabled={env.freeTextEnabled()} />
    </Suspense>
  )
}
