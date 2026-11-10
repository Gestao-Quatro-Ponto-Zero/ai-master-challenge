import type { Metadata } from "next"
import { Suspense } from "react"

import { RoiView } from "@/components/painel/roi-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"

export const metadata: Metadata = { title: "ROI" }

export default function Page() {
  return (
    <Suspense fallback={<ViewSkeleton />}>
      <RoiView />
    </Suspense>
  )
}
