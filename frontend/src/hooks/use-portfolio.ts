import { useQuery } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import type { PortfolioSummary, PortfolioHistory } from '@/types'

export function usePortfolioSummary() {
  return useQuery<PortfolioSummary>({
    queryKey: ['portfolio', 'summary'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.portfolio.summary)
      return data
    },
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function usePortfolioPerformance(assetId?: string) {
  return useQuery({
    queryKey: ['portfolio', 'performance', assetId],
    queryFn: async () => {
      const { data } = await api.get(endpoints.portfolio.performance, {
        params: assetId ? { asset_id: assetId } : {},
      })
      return data
    },
  })
}

export function usePortfolioAllocation() {
  return useQuery({
    queryKey: ['portfolio', 'allocation'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.portfolio.allocation)
      return data
    },
  })
}

export function usePortfolioHistory(days: number = 30) {
  return useQuery<PortfolioHistory[]>({
    queryKey: ['portfolio', 'history', days],
    queryFn: async () => {
      const { data } = await api.get(endpoints.portfolio.history, {
        params: { days },
      })
      return data
    },
  })
}

