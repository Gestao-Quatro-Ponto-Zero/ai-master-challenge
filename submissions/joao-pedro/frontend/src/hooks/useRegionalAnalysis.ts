import { useQuery } from '@tanstack/react-query'
import { fetchRegionalAnalysis, fetchRegionalDetail } from '@/api/analysis'
import type { RegionalProductsScope } from '@/api/analysis'

export function useRegionalAnalysis(params?: { scope?: RegionalProductsScope; manager?: string }) {
  return useQuery({
    queryKey: ['regional-analysis', params?.scope ?? 'geral', params?.manager ?? null],
    queryFn: () => fetchRegionalAnalysis(params),
  })
}

export function useRegionalDetail(region: string) {
  return useQuery({
    queryKey: ['regional-detail', region],
    queryFn: () => fetchRegionalDetail(region),
    enabled: Boolean(region),
  })
}
