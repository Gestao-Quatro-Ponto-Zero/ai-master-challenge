"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"

import { isActive, NAV_ITEMS } from "@/components/shell/nav-items"
import { cn } from "@/lib/utils"

/**
 * Navegação das 3 áreas. Desktop: controle segmentado no centro da top bar.
 * Mobile: barra flutuante centralizada no rodapé (PRD §3.1). O item ativo usa navy/superfície,
 * nunca dourado (o dourado é do número protagonista de cada tela).
 */
export function AreaNav({ variant, consoleBadge }: { variant: "top" | "bottom"; consoleBadge?: React.ReactNode }) {
  const pathname = usePathname()
  if (variant === "top") {
    return (
      <nav aria-label="Áreas" className="hidden rounded-full bg-surface-2 p-1 md:flex">
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item.href)
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "relative inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium transition-all",
                active ? "bg-surface text-text-1 shadow-soft" : "text-text-3 hover:text-text-1",
              )}
            >
              {item.label}
              {item.href === "/console" ? consoleBadge : null}
            </Link>
          )
        })}
      </nav>
    )
  }
  return (
    <nav
      aria-label="Áreas"
      className="fixed inset-x-0 bottom-0 z-40 flex justify-center px-4 md:hidden"
      style={{ paddingBottom: "calc(1rem + env(safe-area-inset-bottom))" }}
    >
      <div className="flex items-center gap-1 rounded-full bg-navy-600/92 p-1.5 shadow-soft backdrop-blur-md dark:bg-surface-2/92">
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item.href)
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "relative inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition-all",
                active ? "bg-surface text-text-1" : "text-white/75 hover:text-white dark:text-text-3 dark:hover:text-text-1",
              )}
            >
              <Icon className="size-4" aria-hidden />
              {item.mobileLabel}
              {item.href === "/console" ? consoleBadge : null}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
