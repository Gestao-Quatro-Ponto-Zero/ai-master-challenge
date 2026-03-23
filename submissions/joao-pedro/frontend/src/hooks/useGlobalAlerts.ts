import { useQuery } from '@tanstack/react-query'
import { fetchGlobalAlerts } from '@/api/analysis'

export function useGlobalAlerts(manager?: string) {
  return useQuery({
    queryKey: ['global-alerts', manager ?? ''],
    queryFn: () => fetchGlobalAlerts(manager ? { manager } : undefined),
  })
}
