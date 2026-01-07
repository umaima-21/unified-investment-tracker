import { useAssets } from '@/hooks/use-assets'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useState } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import type { AssetType } from '@/types'

const assetTypeLabels: Record<AssetType, string> = {
  MF: 'Mutual Funds',
  STOCK: 'Stocks',
  CRYPTO: 'Crypto',
  FD: 'Fixed Deposits',
}

export function AssetsPage() {
  const [assetType, setAssetType] = useState<string>('all')
  const { data: assets, isLoading } = useAssets(assetType === 'all' ? undefined : assetType)

  const groupedAssets = assets?.reduce((acc, asset) => {
    if (!acc[asset.asset_type]) acc[asset.asset_type] = []
    acc[asset.asset_type].push(asset)
    return acc
  }, {} as Record<AssetType, typeof assets>) || {}

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Assets</h1>
          <p className="text-muted-foreground">
            View all your investment assets
          </p>
        </div>
        <Select value={assetType} onValueChange={setAssetType}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="MF">Mutual Funds</SelectItem>
            <SelectItem value="STOCK">Stocks</SelectItem>
            <SelectItem value="CRYPTO">Crypto</SelectItem>
            <SelectItem value="FD">Fixed Deposits</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {Object.keys(groupedAssets).length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground">No assets found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-6">
          {Object.entries(groupedAssets).map(([type, typeAssets]) => (
            <div key={type} className="space-y-4">
              <h2 className="text-2xl font-semibold">
                {assetTypeLabels[type as AssetType]} ({typeAssets.length})
              </h2>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {typeAssets.map((asset) => (
                  <Card key={asset.asset_id}>
                    <CardHeader>
                      <CardTitle className="text-lg">{asset.name}</CardTitle>
                      <CardDescription>
                        {asset.asset_type}
                        {asset.symbol && ` • ${asset.symbol}`}
                        {asset.exchange && ` • ${asset.exchange}`}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 text-sm">
                        {asset.isin && (
                          <div>
                            <span className="text-muted-foreground">ISIN: </span>
                            <span className="font-mono">{asset.isin}</span>
                          </div>
                        )}
                        {asset.scheme_code && (
                          <div>
                            <span className="text-muted-foreground">Scheme Code: </span>
                            <span className="font-mono">{asset.scheme_code}</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

