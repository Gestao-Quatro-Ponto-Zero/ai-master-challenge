import { useQuery } from '@tanstack/react-query'
import { fetchTransferAnalysis } from '@/api/analysis'

export function useTransferAnalysis() {
  return useQuery({
    queryKey: ['transfer-analysis'],
    queryFn: fetchTransferAnalysis,
  })
}
