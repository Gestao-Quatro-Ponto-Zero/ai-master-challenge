import type { Metadata } from "next"
import { Suspense } from "react"

import { OperacaoView } from "@/components/painel/operacao-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"
import { AtRequest } from "@/components/shared/at-request"

export const metadata: Metadata = { title: "Operação" }

export default function Page() {
  return (
    <Suspense fallback={<ViewSkeleton />}>
      <AtRequest>
        <OperacaoView />
      </AtRequest>
    </Suspense>
  )
}
