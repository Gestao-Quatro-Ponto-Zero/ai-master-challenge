// hooks/useApi.js
// Hook centralizado para chamadas à API do backend.
// Mantém estado de loading/error e evita repetição nos componentes.

import { useState, useEffect, useCallback } from 'react'

const BASE = '/api'

export function usePipeline(filters) {
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  const params = new URLSearchParams()
  if (filters.agent)   params.set('agent',   filters.agent)
  if (filters.manager) params.set('manager', filters.manager)
  if (filters.region)  params.set('region',  filters.region)
  if (filters.stage)   params.set('stage',   filters.stage)
  if (filters.product) params.set('product', filters.product)
  params.set('limit', '500')

  const url = `${BASE}/pipeline?${params.toString()}`

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    fetch(url)
      .then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        return r.json()
      })
      .then(d => { if (!cancelled) { setData(d); setLoading(false) } })
      .catch(e => { if (!cancelled) { setError(e.message); setLoading(false) } })

    return () => { cancelled = true }
  }, [url])

  return { data, loading, error }
}

export function useFilters() {
  const [filters, setFilters] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${BASE}/filters`)
      .then(r => r.json())
      .then(d => { setFilters(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return { filters, loading }
}

export function useSummary(filters) {
  const [summary, setSummary] = useState(null)

  const params = new URLSearchParams()
  if (filters.agent)   params.set('agent',   filters.agent)
  if (filters.manager) params.set('manager', filters.manager)
  if (filters.region)  params.set('region',  filters.region)

  useEffect(() => {
    fetch(`${BASE}/summary?${params.toString()}`)
      .then(r => r.json())
      .then(setSummary)
      .catch(() => {})
  }, [params.toString()])

  return summary
}