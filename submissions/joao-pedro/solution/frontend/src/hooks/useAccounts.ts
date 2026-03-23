import { useQuery } from '@tanstack/react-query'
import { fetchAccounts } from '@/api/accounts'
import type { AccountFilters } from '@/types'

export function useAccounts(filters?: AccountFilters) {
  return useQuery({
    queryKey: ['accounts', filters],
    queryFn: () => fetchAccounts(filters),
  })
}
