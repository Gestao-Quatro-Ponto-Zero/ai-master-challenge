"use client"

import { Moon, Sun, Target } from "lucide-react"
import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { dataBr } from "@/lib/format"

export function Header({ dataReferencia }: { dataReferencia?: string }) {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <header className="sticky top-0 z-40 border-b border-primary/25 bg-primary text-primary-foreground shadow-[0_8px_32px_-8px_rgba(15,94,115,0.45)]">
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-accent/80 to-transparent" aria-hidden />
      <div className="relative mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 md:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-foreground/15 ring-2 ring-primary-foreground/20">
            <Target className="h-5 w-5 text-accent" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight md:text-xl">Lead Scorer</h1>
            <p className="text-[11px] text-primary-foreground/70">
              Onde focar no pipeline{dataReferencia ? ` · dados de ${dataBr(dataReferencia)}` : ""}
            </p>
          </div>
        </div>
        {mounted && (
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="text-primary-foreground hover:bg-primary-foreground/15"
            aria-label={theme === "dark" ? "Tema claro" : "Tema escuro"}
          >
            {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </Button>
        )}
      </div>
    </header>
  )
}
