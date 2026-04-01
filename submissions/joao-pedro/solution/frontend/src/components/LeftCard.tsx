import { useState, useEffect } from 'react'
import ProfileCard from './ProfileCard'
import { cn } from '@/lib/utils'
import type { Manager } from '@/types'

const DASHBOARD_SECTIONS = [
  'Macro Analysis',
  'Products & Regional Analysis',
  'Transfer Analysis',
] as const

type Props = {
  selectedManager?: string
  managers?: Manager[]
  onManagerChange?: (name: string) => void
  /** Slide ativo do carrossel do card Dashboard (0-based). */
  dashboardSlideIndex?: number
  /** Navega até o card Dashboard e faz scroll horizontal até a seção. */
  onDashboardSectionClick?: (sectionIndex: number) => void
}

const navItems = [
  {
    label: 'Dashboard',
    targetId: 'card-dashboard',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="18" y1="20" x2="18" y2="10" />
        <line x1="12" y1="20" x2="12" y2="4" />
        <line x1="6" y1="20" x2="6" y2="14" />
      </svg>
    ),
  },
  {
    label: 'Transfers',
    targetId: 'card-transfers',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 1l4 4-4 4" /><path d="M3 11V9a4 4 0 0 1 4-4h14" />
        <path d="M7 23l-4-4 4-4" /><path d="M21 13v2a4 4 0 0 1-4 4H3" />
      </svg>
    ),
  },
  {
    label: 'Sellers',
    targetId: 'card-seller-analysis',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
        <circle cx="12" cy="8" r="4" />
        <path d="M4 20v-1a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v1" />
      </svg>
    ),
  },
  {
    label: 'Alertas',
    targetId: 'card-alertas',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    ),
  },
  {
    label: 'Squad',
    targetId: 'card-squad',
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="9" cy="7" r="3" />
        <path d="M3 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        <path d="M21 21v-2a4 4 0 0 0-3-3.85" />
      </svg>
    ),
  },
]

function scrollToCard(targetId: string) {
  document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

export default function LeftCard({
  selectedManager,
  managers = [],
  onManagerChange,
  dashboardSlideIndex = 0,
  onDashboardSectionClick,
}: Props) {
  const [activeId, setActiveId] = useState<string>('card-dashboard')
  const [isFilterOpen, setIsFilterOpen] = useState(false)

  const currentManager = managers.find((m) => m.manager === selectedManager)

  useEffect(() => {
    const ids = navItems.map((item) => item.targetId)
    const scrollContainer = document.querySelector('main')
    if (!scrollContainer) return

    const update = () => {
      const containerTop = scrollContainer.getBoundingClientRect().top
      let closestId = ids[0]
      let closestDist = Infinity

      for (const id of ids) {
        const el = document.getElementById(id)
        if (!el) continue
        const dist = Math.abs(el.getBoundingClientRect().top - containerTop)
        if (dist < closestDist) {
          closestDist = dist
          closestId = id
        }
      }

      setActiveId(closestId)
    }

    scrollContainer.addEventListener('scroll', update, { passive: true })
    // Run once after mount so initial state is set
    const t = window.setTimeout(update, 100)

    return () => {
      scrollContainer.removeEventListener('scroll', update)
      clearTimeout(t)
    }
  }, [])

  useEffect(() => {
    if (!isFilterOpen) return
    const handle = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (!target.closest('[data-filter-root]')) setIsFilterOpen(false)
    }
    document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [isFilterOpen])

  return (
    <div
      className="relative flex h-full flex-col rounded-3xl bg-white overflow-hidden shadow-[0_4px_24px_rgba(0,0,0,0.08)]"
      data-filter-root=""
    >
      {/* Profile card — topo */}
      <ProfileCard
        name={currentManager?.manager}
        role="Manager"
        region={currentManager?.regional_office}
        managers={managers}
        isFilterOpen={isFilterOpen}
        onFilterToggle={() => setIsFilterOpen((v) => !v)}
        onManagerChange={onManagerChange}
      />

      {/* Nav */}
      <nav className="flex flex-col gap-1 px-6 pt-5">
        {navItems.map(({ label, targetId, icon }) => {
          if (targetId === 'card-dashboard' && onDashboardSectionClick) {
            return (
              <div key={targetId} className="flex flex-col gap-1">
                <button
                  type="button"
                  onClick={() => { scrollToCard(targetId); setActiveId(targetId) }}
                  className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors text-left ${
                    activeId === targetId
                      ? 'bg-neutral-100 text-neutral-900'
                      : 'text-neutral-400 hover:bg-neutral-50 hover:text-neutral-700'
                  }`}
                >
                  {icon}
                  {label}
                </button>
                <div
                  className="ml-2 flex flex-col gap-2 border-l border-neutral-100 pl-3 py-0.5"
                  role="group"
                  aria-label="Seções do dashboard"
                >
                  {DASHBOARD_SECTIONS.map((sectionLabel, i) => (
                    <button
                      key={sectionLabel}
                      type="button"
                      onClick={() => onDashboardSectionClick(i)}
                      className={cn(
                        'rounded-md px-2 py-1.5 text-left text-[11px] font-medium tracking-wide transition-colors',
                        dashboardSlideIndex === i && activeId === 'card-dashboard'
                          ? 'bg-neutral-100/90 text-neutral-800'
                          : 'text-neutral-400 hover:bg-neutral-50 hover:text-neutral-600',
                      )}
                    >
                      {sectionLabel}
                    </button>
                  ))}
                </div>
              </div>
            )
          }

          return (
            <button
              key={targetId}
              type="button"
              onClick={() => { scrollToCard(targetId); setActiveId(targetId) }}
              className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-colors text-left ${
                activeId === targetId
                  ? 'bg-neutral-100 text-neutral-900'
                  : 'text-neutral-400 hover:bg-neutral-50 hover:text-neutral-700'
              }`}
            >
              {icon}
              {label}
            </button>
          )
        })}
      </nav>
    </div>
  )
}
