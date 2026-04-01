import { apiFetch } from './client'
import type { Manager, Seller, ManagerFilters } from '@/types'

export const fetchManagers = (filters?: ManagerFilters): Promise<Manager[]> =>
  apiFetch<Manager[]>('/managers', filters as Record<string, unknown>)

export const fetchManagerSellers = (managerName: string): Promise<Seller[]> =>
  apiFetch<Seller[]>('/sellers').then((sellers) =>
    sellers.filter((s: Seller) => s.manager === managerName)
  )
