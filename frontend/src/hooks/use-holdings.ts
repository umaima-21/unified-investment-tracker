import { useQuery } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import type { Holding, HoldingsSummary } from '@/types'

export function useHoldings(assetType?: string) {
  return useQuery<Holding[]>({
    queryKey: ['holdings', assetType],
    queryFn: async () => {
      try {
        const { data } = await api.get(endpoints.holdings.list, {
          params: assetType ? { asset_type: assetType } : {},
        })
        return data || []
      } catch (err: any) {
        console.error('Error fetching holdings:', err)
        throw err
      }
    },
    retry: 1,
  })
}

export function useHoldingsSummary() {
  return useQuery<HoldingsSummary>({
    queryKey: ['holdings', 'summary'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.holdings.summary)
      return data
    },
  })
}

