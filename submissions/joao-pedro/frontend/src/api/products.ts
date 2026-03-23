import { apiFetch } from './client'
import type { Product, ProductFilters } from '@/types'

export const fetchProducts = (filters?: ProductFilters): Promise<Product[]> =>
  apiFetch<Product[]>('/products', filters as Record<string, unknown>)
