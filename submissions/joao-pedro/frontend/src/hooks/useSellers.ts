import { useQuery } from '@tanstack/react-query'
import { fetchSellers, fetchSeller } from '@/api/sellers'
import type { SellerFilters } from '@/types'

export function useSellers(filters?: SellerFilters) {
  return useQuery({
    queryKey: ['sellers', filters],
    queryFn: () => fetchSellers(filters),
  })
}

export function useSeller(name: string) {
  return useQuery({
    queryKey: ['seller', name],
    queryFn: () => fetchSeller(name),
    enabled: Boolean(name),
  })
}
