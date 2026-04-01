import { apiFetch } from './client'
import type { Account, AccountFilters } from '@/types'

export const fetchAccounts = (filters?: AccountFilters): Promise<Account[]> =>
  apiFetch<Account[]>('/accounts', filters as Record<string, unknown>)
