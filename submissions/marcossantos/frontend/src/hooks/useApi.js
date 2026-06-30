// hooks/useApi.js
// Hook centralizado para chamadas à API.
// Injeta o Bearer token automaticamente em todas as requisições.

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'

const BASE = '/api'

function useAuthFetch() {
  const { token, logout } = useAuth()

  return useCallback(async (url, options = {}) => {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    })

    // Token expirado — força logout
    if (res.status === 401) {
      logout()
      throw new Error('Sessão expirada. Faça login novamente.')
    }

    return res
  }, [token, logout])
}

// ---------------------------------------------------------------------------
// Pipeline
// ---------------------------------------------------------------------------

export function usePipeline(filters) {
  const authFetch = useAuthFetch()
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

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

    authFetch(url)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(d => { if (!cancelled) { setData(d); setLoading(false) } })
      .catch(e => { if (!cancelled) { setError(e.message); setLoading(false) } })

    return () => { cancelled = true }
  }, [url])

  return { data, loading, error }
}

// ---------------------------------------------------------------------------
// Filtros
// ---------------------------------------------------------------------------

export function useFilters() {
  const authFetch = useAuthFetch()
  const [filters, setFilters] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    authFetch(`${BASE}/filters`)
      .then(r => r.json())
      .then(d => { setFilters(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  return { filters, loading }
}

// ---------------------------------------------------------------------------
// Summary
// ---------------------------------------------------------------------------

export function useSummary(filters) {
  const authFetch = useAuthFetch()
  const [summary, setSummary] = useState(null)

  const params = new URLSearchParams()
  if (filters.agent)   params.set('agent',   filters.agent)
  if (filters.manager) params.set('manager', filters.manager)
  if (filters.region)  params.set('region',  filters.region)

  useEffect(() => {
    authFetch(`${BASE}/summary?${params.toString()}`)
      .then(r => r.json())
      .then(setSummary)
      .catch(() => {})
  }, [params.toString()])

  return summary
}

// ---------------------------------------------------------------------------
// Alertas
// ---------------------------------------------------------------------------

export function useAlerts() {
  const authFetch = useAuthFetch()
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)

  const fetch_ = useCallback(() => {
    setLoading(true)
    authFetch(`${BASE}/alerts`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [authFetch])

  useEffect(() => { fetch_() }, [])

  // Polling a cada 60s para novos alertas
  useEffect(() => {
    const interval = setInterval(fetch_, 60_000)
    return () => clearInterval(interval)
  }, [fetch_])

  async function dismiss(alertId) {
    await authFetch(`${BASE}/alerts/${alertId}/dismiss`, { method: 'POST' })
    fetch_()
  }

  async function dismissAll() {
    await authFetch(`${BASE}/alerts/dismiss-all`, { method: 'POST' })
    fetch_()
  }

  return { data, loading, dismiss, dismissAll, refresh: fetch_ }
}

// ---------------------------------------------------------------------------
// Notas de um deal
// ---------------------------------------------------------------------------

export function useNotes(opportunityId) {
  const authFetch = useAuthFetch()
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving,  setSaving]  = useState(false)

  const fetch_ = useCallback(() => {
    if (!opportunityId) return
    setLoading(true)
    authFetch(`${BASE}/deal/${opportunityId}/notes`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [opportunityId, authFetch])

  useEffect(() => { fetch_() }, [fetch_])

  async function addNote(content) {
    setSaving(true)
    try {
      const res = await authFetch(`${BASE}/deal/${opportunityId}/notes`, {
        method: 'POST',
        body: JSON.stringify({ content }),
      })
      if (!res.ok) throw new Error('Erro ao salvar nota.')
      await fetch_()
    } finally {
      setSaving(false)
    }
  }

  async function deleteNote(noteId) {
    await authFetch(`${BASE}/deal/${opportunityId}/notes/${noteId}`, { method: 'DELETE' })
    fetch_()
  }

  return { data, loading, saving, addNote, deleteNote, refresh: fetch_ }
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export function useAnalytics(tab) {
  const authFetch = useAuthFetch()
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    if (!tab) return
    setLoading(true)
    setData(null)
    setError(null)

    const endpoints = {
      team:    '/api/analytics/team',
      funnel:  '/api/analytics/funnel',
      at_risk: '/api/analytics/at-risk',
    }

    const url = endpoints[tab]
    if (!url) return

    authFetch(url)
      .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json() })
      .then(d  => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [tab])

  return { data, loading, error }
}