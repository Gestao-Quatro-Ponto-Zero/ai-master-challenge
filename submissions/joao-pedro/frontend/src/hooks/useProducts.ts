import { useQuery } from '@tanstack/react-query'
import { fetchProducts } from '@/api/products'
import type { ProductFilters } from '@/types'

export function useProducts(filters?: ProductFilters) {
  return useQuery({
    queryKey: ['products', filters],
    queryFn: () => fetchProducts(filters),
  })
}
