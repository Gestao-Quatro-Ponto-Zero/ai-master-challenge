'use client'

import { useMounted } from '@/components/client-only'

/**
 * Hydration-safe date/number formatting.
 *
 * Locale APIs (`toLocaleDateString`, `Intl.*`) default to the runtime's locale and
 * timezone, which differ between server (UTC) and browser — a classic hydration
 * mismatch. These components format with an explicit locale + timeZone so SSR and
 * client render identical text. Set `localize` to re-render in the visitor's own
 * locale/timezone after mount (safe: wrapped in suppressHydrationWarning).
 */

const DEFAULT_LOCALE = 'en-US'
const DEFAULT_TIME_ZONE = 'UTC'

type SafeDateProps = {
  date: Date | string | number
  options?: Intl.DateTimeFormatOptions
  locale?: string
  localize?: boolean
  className?: string
}

export function SafeDate({ date, options, locale = DEFAULT_LOCALE, localize = false, className }: SafeDateProps) {
  const mounted = useMounted()
  const d = date instanceof Date ? date : new Date(date)
  const useLocal = localize && mounted
  // toLocaleDateString throws on timeStyle (and toLocaleTimeString on dateStyle),
  // so date+time option mixes render via toLocaleString.
  const text = (options?.timeStyle ? d.toLocaleString : d.toLocaleDateString).call(d, useLocal ? undefined : locale, {
    timeZone: useLocal ? undefined : DEFAULT_TIME_ZONE,
    ...options,
  })
  return (
    <span suppressHydrationWarning className={className}>
      {text}
    </span>
  )
}

export function SafeTime({ date, options, locale = DEFAULT_LOCALE, localize = false, className }: SafeDateProps) {
  const mounted = useMounted()
  const d = date instanceof Date ? date : new Date(date)
  const useLocal = localize && mounted
  const text = (options?.dateStyle ? d.toLocaleString : d.toLocaleTimeString).call(d, useLocal ? undefined : locale, {
    timeZone: useLocal ? undefined : DEFAULT_TIME_ZONE,
    ...options,
  })
  return (
    <span suppressHydrationWarning className={className}>
      {text}
    </span>
  )
}

type SafeNumberProps = {
  value: number
  options?: Intl.NumberFormatOptions
  locale?: string
  /** ISO 4217 code, e.g. 'USD' — shorthand for style: 'currency'. */
  currency?: string
  localize?: boolean
  className?: string
}

export function SafeNumber({ value, options, locale = DEFAULT_LOCALE, currency, localize = false, className }: SafeNumberProps) {
  const mounted = useMounted()
  const useLocal = localize && mounted
  const text = value.toLocaleString(useLocal ? undefined : locale, {
    ...(currency ? { style: 'currency' as const, currency } : {}),
    ...options,
  })
  return (
    <span suppressHydrationWarning className={className}>
      {text}
    </span>
  )
}
