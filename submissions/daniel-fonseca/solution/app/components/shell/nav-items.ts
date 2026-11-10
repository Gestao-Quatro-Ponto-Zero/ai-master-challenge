import { BookOpen, LayoutDashboard, MessageSquareText, type LucideIcon } from "lucide-react"

export interface NavItem {
  href: "/" | "/console" | "/como-foi-feito"
  label: string
  mobileLabel: string
  icon: LucideIcon
}

/** As 3 áreas do app (PRD §3). */
export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Painel", mobileLabel: "Painel", icon: LayoutDashboard },
  { href: "/console", label: "Console", mobileLabel: "Console", icon: MessageSquareText },
  { href: "/como-foi-feito", label: "Como foi feito", mobileLabel: "Método", icon: BookOpen },
]

export function isActive(pathname: string, href: NavItem["href"]) {
  return href === "/" ? pathname === "/" : pathname.startsWith(href)
}
