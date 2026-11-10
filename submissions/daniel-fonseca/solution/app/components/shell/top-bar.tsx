import Link from "next/link"
import { Suspense } from "react"

import { AreaNav } from "@/components/shell/area-nav"
import { ConsoleBadge } from "@/components/shell/console-badge"
import { ThemeToggle } from "@/components/shell/theme-toggle"

export function TopBar() {
  const badge = (
    <Suspense fallback={null}>
      <ConsoleBadge />
    </Suspense>
  )
  return (
    <>
      <header className="sticky top-0 z-40 border-b border-border bg-bg/85 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          <Link href="/" className="font-serif text-lg leading-none text-text-1 sm:text-xl">
            Triagem Inteligente
          </Link>
          <AreaNav variant="top" consoleBadge={badge} />
          <ThemeToggle />
        </div>
      </header>
      <AreaNav variant="bottom" consoleBadge={badge} />
    </>
  )
}
