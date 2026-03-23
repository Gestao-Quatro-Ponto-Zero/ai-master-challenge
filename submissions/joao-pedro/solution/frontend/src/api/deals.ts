import { apiFetch } from './client'
import type { Deal, ScoreResult, DealFilters } from '@/types'

export const fetchDeals = (filters?: DealFilters): Promise<Deal[]> =>
  apiFetch<Deal[]>('/deals', filters as Record<string, unknown>)

export const fetchDeal = (id: string): Promise<ScoreResult> =>
  apiFetch<ScoreResult>(`/deals/${encodeURIComponent(id)}`)
