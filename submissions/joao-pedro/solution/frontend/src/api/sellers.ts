import { apiFetch } from './client'
import type { Seller, SellerFilters } from '@/types'

export const fetchSellers = (filters?: SellerFilters): Promise<Seller[]> =>
  apiFetch<Seller[]>('/sellers', filters as Record<string, unknown>)

export const fetchSeller = (name: string): Promise<Seller> =>
  apiFetch<Seller>(`/sellers/${encodeURIComponent(name)}`)
