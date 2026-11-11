import { BookOpen, LayoutDashboard, MessageSquareText, type LucideIcon } from "lucide-react"

export interface NavChild {
  href: string
  label: string
  description: string
}

export interface NavArea {
  key: "painel" | "tickets" | "metodo"
  label: string
  mobileLabel: string
  icon: LucideIcon
  /** prefixo das rotas da área; a área sem filhos usa como link direto */
  base: string
  children?: NavChild[]
}

/** As 3 áreas do app, com os subitens de cada uma (ADR-0015). */
export const NAV_AREAS: NavArea[] = [
  {
    key: "painel",
    label: "Painel",
    mobileLabel: "Painel",
    icon: LayoutDashboard,
    base: "/painel",
    children: [
      { href: "/painel/diagnostico", label: "Diagnóstico", description: "Onde a operação perde tempo nos 8.469 tickets do DS1" },
      { href: "/painel/roi", label: "ROI", description: "Quanto a IA economizaria nos casos em que teria autonomia" },
      { href: "/painel/operacao", label: "Operação", description: "Indicadores do sistema de triagem, ao vivo" },
    ],
  },
  { key: "tickets", label: "Tickets", mobileLabel: "Tickets", icon: MessageSquareText, base: "/tickets" },
  {
    key: "metodo",
    label: "Como foi feito",
    mobileLabel: "Método",
    icon: BookOpen,
    base: "/como-foi-feito",
    children: [
      { href: "/como-foi-feito/proposta", label: "Proposta", description: "Fluxo da automação, os 3 caminhos e o que fica com pessoas" },
      { href: "/como-foi-feito/decisoes", label: "Decisões", description: "As ADRs e onde a IA errou" },
      { href: "/como-foi-feito/conducao", label: "Condução", description: "Como o projeto foi conduzido com IA" },
    ],
  },
]

export const isAreaActive = (pathname: string, area: NavArea) => pathname === area.base || pathname.startsWith(`${area.base}/`)

export const activeChild = (pathname: string, area: NavArea) => area.children?.find((c) => pathname === c.href || pathname.startsWith(`${c.href}/`))
