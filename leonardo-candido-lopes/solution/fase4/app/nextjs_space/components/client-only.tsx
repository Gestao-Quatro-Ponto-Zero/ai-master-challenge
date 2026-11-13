'use client'

import { ReactNode, useEffect, useState } from 'react'

/** True only after the component has mounted on the client. Use to gate browser-only values. */
export function useMounted(): boolean {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  return mounted
}

/**
 * Renders children only after client mount, so SSR output stays deterministic.
 * Use for anything that differs between server and client (window/localStorage reads,
 * user timezone/locale values, random ids, live clocks, third-party widgets).
 * Pass a `fallback` matching the final size to avoid layout shift.
 */
export function ClientOnly({ children, fallback = null }: { children: ReactNode; fallback?: ReactNode }) {
  const mounted = useMounted()
  return <>{mounted ? children : fallback}</>
}
