"use client"

import { Popover } from "@base-ui/react/popover"
import { ChevronDown } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"

import { activeChild, isAreaActive, NAV_AREAS, type NavArea } from "@/components/shell/nav-items"
import { cn } from "@/lib/utils"

/**
 * Navegação de um nível com submenus (ADR-0015). Desktop: controle no centro da top bar; as áreas com
 * subpáginas abrem um menu com clique. Mobile: barra flutuante no rodapé, e o menu abre para cima.
 * O item ativo usa navy/superfície, nunca dourado (o dourado é do número protagonista de cada tela).
 */
export function AreaNav({ variant, ticketsBadge }: { variant: "top" | "bottom"; ticketsBadge?: React.ReactNode }) {
  const pathname = usePathname()
  const top = variant === "top"

  const items = NAV_AREAS.map((area) => {
    const active = isAreaActive(pathname, area)
    const child = active ? activeChild(pathname, area) : undefined
    const Icon = area.icon
    const itemCls = top
      ? cn("relative inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-medium transition-all outline-none focus-visible:ring-2 focus-visible:ring-text-3/40", active ? "bg-surface text-text-1 shadow-soft" : "text-text-3 hover:text-text-1")
      : cn(
          "relative inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold transition-all outline-none",
          active ? "bg-surface text-text-1" : "text-white/75 hover:text-white dark:text-text-3 dark:hover:text-text-1",
        )
    const content = (
      <>
        {top ? null : <Icon className="size-4" aria-hidden />}
        <span>{top ? area.label : area.mobileLabel}</span>
        {top && child ? <span className="text-text-3">· {child.label}</span> : null}
        {area.key === "tickets" ? ticketsBadge : null}
        {area.children ? <ChevronDown className="size-3.5 opacity-70" aria-hidden /> : null}
      </>
    )
    if (!area.children) {
      return (
        <Link key={area.key} href={area.base} aria-current={active ? "page" : undefined} className={itemCls}>
          {content}
        </Link>
      )
    }
    return <AreaMenu key={area.key} area={area} pathname={pathname} className={itemCls} side={top ? "bottom" : "top"} active={active}>{content}</AreaMenu>
  })

  if (top) {
    return (
      <nav aria-label="Áreas" className="hidden rounded-full bg-surface-2 p-1 md:flex">
        {items}
      </nav>
    )
  }
  return (
    <nav aria-label="Áreas" className="mobile-nav fixed inset-x-0 bottom-0 z-40 flex justify-center px-4 md:hidden" style={{ paddingBottom: "calc(1rem + env(safe-area-inset-bottom))" }}>
      <div className="flex items-center gap-1 rounded-full bg-navy-600/92 p-1.5 shadow-soft backdrop-blur-md dark:bg-surface-2/92">{items}</div>
    </nav>
  )
}

function AreaMenu({ area, pathname, className, side, active, children }: { area: NavArea; pathname: string; className: string; side: "top" | "bottom"; active: boolean; children: React.ReactNode }) {
  const [open, setOpen] = useState(false)
  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger className={className} aria-current={active ? "page" : undefined}>
        {children}
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Positioner side={side} sideOffset={10} align="center" collisionPadding={12} className="z-[70]">
          <Popover.Popup className="w-[min(20rem,calc(100vw-2rem))] origin-[var(--transform-origin)] rounded-xl border border-border bg-surface p-1.5 shadow-soft outline-none transition-[scale,opacity] duration-100 data-ending-style:scale-[0.98] data-ending-style:opacity-0 data-starting-style:scale-[0.98] data-starting-style:opacity-0">
            <Popover.Title className="px-3 pt-2 pb-1 font-mono text-[10px] uppercase tracking-[0.14em] text-text-3">{area.label}</Popover.Title>
            <ul className="flex flex-col">
              {area.children!.map((c) => {
                const current = pathname === c.href
                return (
                  <li key={c.href}>
                    <Link
                      href={c.href}
                      onClick={() => setOpen(false)}
                      aria-current={current ? "page" : undefined}
                      className={cn("flex flex-col gap-0.5 rounded-lg px-3 py-2.5 transition-colors hover:bg-surface-2", current && "bg-surface-2")}
                    >
                      <span className="text-sm font-medium text-text-1">{c.label}</span>
                      <span className="text-xs leading-snug text-text-3">{c.description}</span>
                    </Link>
                  </li>
                )
              })}
            </ul>
          </Popover.Popup>
        </Popover.Positioner>
      </Popover.Portal>
    </Popover.Root>
  )
}
