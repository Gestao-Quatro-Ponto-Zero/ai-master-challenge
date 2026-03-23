import { useQuery } from '@tanstack/react-query'
import { fetchManagers, fetchManagerSellers } from '@/api/managers'
import type { ManagerFilters } from '@/types'

export function useManagers(filters?: ManagerFilters) {
  return useQuery({
    queryKey: ['managers', filters],
    queryFn: () => fetchManagers(filters),
  })
}

export function useManagerSellers(managerName: string) {
  return useQuery({
    queryKey: ['manager-sellers', managerName],
    queryFn: () => fetchManagerSellers(managerName),
    enabled: Boolean(managerName),
  })
}
