import { useQuery } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import type { Asset } from '@/types'

export function useAssets(assetType?: string) {
  return useQuery<Asset[]>({
    queryKey: ['assets', assetType],
    queryFn: async () => {
      const { data } = await api.get(endpoints.assets.list, {
        params: assetType ? { asset_type: assetType } : {},
      })
      return data
    },
  })
}

export function useAsset(assetId: string) {
  return useQuery<Asset>({
    queryKey: ['assets', assetId],
    queryFn: async () => {
      const { data } = await api.get(endpoints.assets.get(assetId))
      return data
    },
    enabled: !!assetId,
  })
}

