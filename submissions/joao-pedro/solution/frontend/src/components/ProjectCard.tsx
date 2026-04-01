import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type ReactNode,
  type UIEvent,
} from 'react'
import { cn } from '@/lib/utils'

/** Ref exposto para controlar o scroll horizontal entre slides (ex.: menu lateral). */
export type ProjectCardRef = {
  scrollToPage: (index: number) => void
}

export type Page = {
  index: string
  title?: string
  body?: string
  content?: ReactNode
}

const defaultPages: Page[] = [
  { index: '01', title: 'Macro Analysis' },
  { index: '02', title: 'Products & Regional Analysis' },
  { index: '03', title: 'Transfer Analysis' },
]

const emptyPages: Page[] = [{ index: '01' }, { index: '02' }, { index: '03' }]

type Props = {
  id?: string
  label?: string
  description?: string
  gradientFrom?: string
  gradientTo?: string
  scrollHint?: boolean
  /** Notifica o índice do slide visível (carrossel horizontal). */
  onDashboardSlideChange?: (index: number) => void
  /** Botão de tela cheia no canto superior direito (carrossel). */
  showFullscreenToggle?: boolean
  empty?: boolean
  singlePage?: boolean
  pages?: Page[]
  children?: ReactNode
}

const ProjectCard = forwardRef<ProjectCardRef, Props>(function ProjectCard(
  {
    id,
    label,
    description,
    scrollHint = false,
    onDashboardSlideChange,
    showFullscreenToggle = false,
    empty = false,
    singlePage = false,
    pages,
    children,
  },
  ref,
) {
  const resolvedPages = pages ?? (empty ? emptyPages : defaultPages)
  const scrollPortRef = useRef<HTMLDivElement>(null)
  const fullscreenTargetRef = useRef<HTMLElement>(null)
  const [nativeFullscreen, setNativeFullscreen] = useState(false)
  const [visualFullscreen, setVisualFullscreen] = useState(false)

  const isFullscreen = nativeFullscreen || visualFullscreen

  useEffect(() => {
    const syncNative = () => {
      const el = fullscreenTargetRef.current
      const fs =
        document.fullscreenElement ??
        (document as Document & { webkitFullscreenElement?: Element | null }).webkitFullscreenElement
      setNativeFullscreen(!!el && fs === el)
    }
    document.addEventListener('fullscreenchange', syncNative)
    document.addEventListener('webkitfullscreenchange', syncNative as EventListener)
    return () => {
      document.removeEventListener('fullscreenchange', syncNative)
      document.removeEventListener('webkitfullscreenchange', syncNative as EventListener)
    }
  }, [])

  useEffect(() => {
    if (!visualFullscreen) return
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setVisualFullscreen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = prev
      window.removeEventListener('keydown', onKey)
    }
  }, [visualFullscreen])

  const enterFullscreen = useCallback(async () => {
    const el = fullscreenTargetRef.current
    if (!el) return
    try {
      if (typeof el.requestFullscreen === 'function') {
        await el.requestFullscreen()
        return
      }
    } catch {
      /* usuário negou ou não suportado */
    }
    const wk = (el as HTMLElement & { webkitRequestFullscreen?: () => void }).webkitRequestFullscreen
    if (wk) {
      try {
        wk.call(el)
        return
      } catch {
        /* fallback visual */
      }
    }
    setVisualFullscreen(true)
  }, [])

  const exitFullscreen = useCallback(() => {
    const doc = document as Document & {
      webkitFullscreenElement?: Element | null
      webkitExitFullscreen?: () => void
    }
    if (document.fullscreenElement && document.exitFullscreen) {
      void document.exitFullscreen()
    } else if (doc.webkitFullscreenElement && doc.webkitExitFullscreen) {
      doc.webkitExitFullscreen()
    }
    setVisualFullscreen(false)
  }, [])

  const handleHorizontalScroll = useCallback(
    (e: UIEvent<HTMLDivElement>) => {
      const el = e.currentTarget
      const w = el.clientWidth || 1
      const idx = Math.round(el.scrollLeft / w)
      const clamped = Math.max(0, Math.min(idx, resolvedPages.length - 1))
      onDashboardSlideChange?.(clamped)
    },
    [onDashboardSlideChange, resolvedPages.length],
  )

  useImperativeHandle(
    ref,
    () => ({
      scrollToPage: (index: number) => {
        const root = scrollPortRef.current
        if (!root) return
        const w = root.clientWidth
        root.scrollTo({ left: index * w, behavior: 'smooth' })
        onDashboardSlideChange?.(index)
      },
    }),
    [onDashboardSlideChange],
  )

  const showFsChrome = showFullscreenToggle && !singlePage

  return (
    <article
      ref={fullscreenTargetRef}
      id={id}
      className={cn(
        'min-w-0 max-w-full snap-start lg:h-[calc(100svh-2rem)] rounded-3xl shadow-[0_4px_24px_rgba(0,0,0,0.08)]',
        visualFullscreen &&
          'fixed inset-0 z-[200] m-0 flex h-[100dvh] max-h-[100dvh] min-h-[100dvh] w-screen max-w-screen snap-none flex-col rounded-none shadow-none',
        isFullscreen &&
          !visualFullscreen &&
          'flex h-[100dvh] max-h-[100dvh] min-h-[100dvh] flex-col rounded-none shadow-none',
      )}
    >
      {/* Inner container */}
      <div
        className={cn(
          'relative flex min-w-0 max-w-full flex-col overflow-hidden rounded-3xl bg-white',
          isFullscreen ? 'min-h-0 flex-1 rounded-none' : 'h-full min-h-0',
        )}
      >
        {showFsChrome && !isFullscreen && (
          <button
            type="button"
            onClick={() => void enterFullscreen()}
            className="absolute right-5 top-4 z-20 rounded-lg p-2 text-neutral-400 transition-colors hover:bg-neutral-100 hover:text-neutral-700"
            aria-label="Tela cheia"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden
            >
              <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" />
            </svg>
          </button>
        )}
        {showFsChrome && isFullscreen && (
          <button
            type="button"
            onClick={exitFullscreen}
            className="absolute right-5 top-4 z-30 rounded-lg p-2 text-neutral-500 transition-colors hover:bg-neutral-100 hover:text-neutral-900"
            aria-label="Sair da tela cheia"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}

        {/* Card label — oculto em tela cheia */}
        {label && !isFullscreen && (
          <div className="shrink-0 px-8 pt-6 pb-0">
            <span className="text-xs font-semibold tracking-widest text-neutral-400 uppercase">
              {label}
            </span>
            {description && (
              <div className="flex items-center gap-1 mt-1 select-none">
                <p className="text-[11px] font-medium tracking-widest text-neutral-400 uppercase">
                  {description}
                </p>
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-neutral-400">
                  <line x1="7" y1="17" x2="17" y2="7" /><polyline points="7 7 17 7 17 17" />
                </svg>
              </div>
            )}
            {scrollHint && (
              <div className="mt-2 flex flex-wrap items-center gap-1.5 select-none">
                <svg
                  width="11"
                  height="11"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="shrink-0 text-neutral-400"
                  aria-hidden
                >
                  <line x1="19" y1="12" x2="5" y2="12" />
                  <polyline points="12 5 5 12 12 19" />
                </svg>
                <span className="text-[11px] font-medium tracking-wide text-neutral-400">
                  ROLE HORIZONTALMENTE DENTRO DO CANVAS PARA VISUALIZAR
                </span>
                <svg
                  width="11"
                  height="11"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="shrink-0 text-neutral-400"
                  aria-hidden
                >
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </div>
            )}
          </div>
        )}

        {singlePage ? (
          /* Single page — conteúdo livre via children */
          <div className="min-h-0 min-w-0 flex-1 overflow-y-auto">
            {children}
          </div>
        ) : (
          /* Multi-page — scroll horizontal com snap */
          <div className="relative min-h-0 min-w-0 flex-1">
            {/* Scroll container — min-w-0: não herda largura mínima do conteúdo (tabelas) */}
            <div
              ref={scrollPortRef}
              onScroll={handleHorizontalScroll}
              className="h-full w-full min-w-0 max-w-full snap-x snap-mandatory overflow-x-auto overflow-y-hidden overscroll-x-contain scroll-smooth"
            >
              <div className="flex h-full min-w-0">
                {resolvedPages.map((page) => (
                  <div
                    key={page.index}
                    className="relative box-border flex h-full min-h-0 min-w-full max-w-full shrink-0 snap-start snap-always flex-col overflow-hidden"
                  >
                    {page.content ? (
                      <div
                        className={cn(
                          'flex min-h-0 w-full max-w-full flex-1 flex-col',
                          isFullscreen
                            ? 'items-center justify-center overflow-y-auto overflow-x-auto px-4 py-6 sm:px-8'
                            : 'overflow-y-auto',
                        )}
                      >
                        <div
                          className={cn(
                            'flex min-h-0 w-full min-w-0 max-w-full flex-1 flex-col',
                            isFullscreen &&
                              'items-center justify-center [&>*]:max-w-full',
                          )}
                        >
                          {page.content}
                        </div>
                      </div>
                    ) : (
                      <div
                        className={cn(
                          'flex h-full flex-col justify-center p-8 sm:p-12',
                          isFullscreen && 'items-center text-center',
                        )}
                      >
                        <span className="text-xs font-mono text-neutral-300 mb-4 tracking-widest">
                          {page.index} / {String(resolvedPages.length).padStart(2, '0')}
                        </span>
                        {page.title && (
                          <h2 className="text-2xl sm:text-3xl font-bold text-neutral-900 leading-tight">
                            {page.title}
                          </h2>
                        )}
                        {page.body && (
                          <p className="mt-4 max-w-[55ch] text-base text-neutral-500 leading-relaxed">
                            {page.body}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

      </div>
    </article>
  )
})

export default ProjectCard
