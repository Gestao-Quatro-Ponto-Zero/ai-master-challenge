import { useQuery } from '@tanstack/react-query'
import { fetchWonValueOverTime } from '@/api/analysis'

export function useWonValueOverTime(salesAgent: string, options?: { enabled?: boolean }) {
  const enabled =
    options?.enabled !== undefined ? options.enabled : Boolean(salesAgent)
  return useQuery({
    queryKey: ['wonValueOverTime', salesAgent],
    queryFn: () => fetchWonValueOverTime(salesAgent),
    enabled,
  })
}
