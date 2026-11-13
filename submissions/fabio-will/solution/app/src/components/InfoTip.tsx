'use client'

import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState } from 'react'

const GAP = 8
const EDGE = 12

interface Props {
  /** What the icon explains, read by screen readers as "Sobre <label>". */
  label: string
  /** The explanation itself. Plain text, one or two sentences. */
  text: string
}

/**
 * Info icon with an explanation bubble.
 * Mouse: shows on hover, pins on click. Keyboard: shows on focus. Touch: tap toggles.
 * Esc, a tap outside, scroll or resize close it. The bubble is position: fixed, so tables with
 * overflow-x never clip it, and it flips above the icon when there is no room below.
 */
export function InfoTip({ label, text }: Props) {
  const id = useId()
  const button = useRef<HTMLButtonElement>(null)
  const bubble = useRef<HTMLSpanElement>(null)
  const pinned = useRef(false)
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null)

  const close = useCallback(() => {
    pinned.current = false
    setOpen(false)
    setPos(null)
  }, [])

  useLayoutEffect(() => {
    if (!open || !button.current || !bubble.current) return
    const r = button.current.getBoundingClientRect()
    const { offsetWidth: w, offsetHeight: h } = bubble.current
    const left = Math.max(EDGE, Math.min(r.left + r.width / 2 - w / 2, window.innerWidth - w - EDGE))
    const below = r.bottom + GAP
    const top = below + h > window.innerHeight - EDGE && r.top - GAP - h > EDGE ? r.top - GAP - h : below
    setPos({ top, left })
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        close()
        button.current?.focus()
      }
    }
    const onDown = (e: PointerEvent) => {
      const t = e.target as Node
      if (!button.current?.contains(t) && !bubble.current?.contains(t)) close()
    }
    window.addEventListener('keydown', onKey)
    window.addEventListener('pointerdown', onDown)
    window.addEventListener('scroll', close, { capture: true, passive: true })
    window.addEventListener('resize', close)
    return () => {
      window.removeEventListener('keydown', onKey)
      window.removeEventListener('pointerdown', onDown)
      window.removeEventListener('scroll', close, { capture: true })
      window.removeEventListener('resize', close)
    }
  }, [open, close])

  return (
    <span className="infotip">
      <button
        ref={button}
        type="button"
        className="infotip-btn"
        aria-label={`Sobre ${label}`}
        aria-expanded={open}
        aria-describedby={id}
        onPointerEnter={(e) => e.pointerType === 'mouse' && setOpen(true)}
        onPointerLeave={(e) => e.pointerType === 'mouse' && !pinned.current && close()}
        onFocus={() => setOpen(true)}
        onBlur={close}
        onClick={(e) => {
          e.stopPropagation() // a tip inside a clickable row must not select the row
          if (open && pinned.current) close()
          else {
            pinned.current = true
            setOpen(true)
          }
        }}
      >
        <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" focusable="false">
          <circle cx="10" cy="10" r="8.25" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <rect x="9.2" y="8.6" width="1.6" height="5.8" rx="0.8" fill="currentColor" />
          <circle cx="10" cy="6.1" r="1.05" fill="currentColor" />
        </svg>
      </button>
      <span ref={bubble} id={id} role="tooltip" className="infotip-bubble" hidden={!open} style={pos ?? undefined}>
        {text}
      </span>
    </span>
  )
}
