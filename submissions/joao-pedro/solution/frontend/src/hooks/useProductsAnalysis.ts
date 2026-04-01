import { useQuery } from '@tanstack/react-query'
import { fetchProductsAnalysis } from '@/api/analysis'
import type { RegionalProductsScope } from '@/api/analysis'

export function useProductsAnalysis(params?: { scope?: RegionalProductsScope; manager?: string }) {
  return useQuery({
    queryKey: ['products-analysis', params?.scope ?? 'geral', params?.manager ?? null],
    queryFn: () => fetchProductsAnalysis(params),
  })
}
