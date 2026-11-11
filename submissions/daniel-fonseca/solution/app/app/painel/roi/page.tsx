import type { Metadata } from "next"
import { Suspense } from "react"

import { RoiView } from "@/components/painel/roi-view"
import { ViewSkeleton } from "@/components/painel/view-skeleton"
import { AtRequest } from "@/components/shared/at-request"

export const metadata: Metadata = { title: "ROI" }

export default function Page() {
  return (
    <Suspense fallback={<ViewSkeleton />}>
      <AtRequest>
        <RoiView />
      </AtRequest>
    </Suspense>
  )
}
