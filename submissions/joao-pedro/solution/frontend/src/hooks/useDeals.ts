import { useQuery, useQueries } from '@tanstack/react-query'
import { fetchDeals, fetchDeal } from '@/api/deals'
import type { DealFilters } from '@/types'

export function useDeals(filters?: DealFilters) {
  return useQuery({
    queryKey: ['deals', filters],
    queryFn: () => fetchDeals(filters),
  })
}

export function useDeal(id: string) {
  return useQuery({
    queryKey: ['deal', id],
    queryFn: () => fetchDeal(id),
    enabled: Boolean(id),
  })
}

export function useDealBatch(ids: string[]) {
  return useQueries({
    queries: ids.map(id => ({
      queryKey: ['deal', id],
      queryFn: () => fetchDeal(id),
      enabled: Boolean(id),
    })),
  })
}
