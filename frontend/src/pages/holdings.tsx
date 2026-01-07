import { useState } from 'react'
import { useHoldings } from '@/hooks/use-holdings'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { AssetType } from '@/types'

const assetTypeLabels: Record<AssetType, string> = {
  MF: 'Mutual Funds',
  STOCK: 'Stocks',
  CRYPTO: 'Crypto',
  FD: 'Fixed Deposits',
}

export function HoldingsPage() {
  const [assetType, setAssetType] = useState<string>('all')
  const { data: holdings, isLoading, error } = useHoldings(assetType === 'all' ? undefined : assetType)

  // Debug logging
  console.log('Holdings data:', holdings)
  console.log('Holdings type:', typeof holdings)
  console.log('Is array:', Array.isArray(holdings))
  console.log('Holdings length:', holdings?.length)

  const holdingsArray = Array.isArray(holdings) ? holdings : []
  
  const groupedHoldings = holdingsArray.reduce((acc, holding) => {
    const type = holding?.asset?.asset_type || 'OTHER'
    if (!acc[type]) acc[type] = []
    acc[type].push(holding)
    return acc
  }, {} as Record<string, typeof holdingsArray>)

  console.log('Grouped holdings:', groupedHoldings)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Holdings</h1>
          <p className="text-muted-foreground">
            View and manage your investment holdings
          </p>
        </div>
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Holdings</h1>
          <p className="text-muted-foreground">
            View and manage your investment holdings
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading holdings</p>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error ? error.message : 'Failed to fetch data. Please check if the backend is running.'}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Holdings</h1>
          <p className="text-muted-foreground">
            View and manage your investment holdings
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

      {(!holdingsArray || holdingsArray.length === 0) ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground mb-4">No holdings found</p>
            <p className="text-sm text-muted-foreground mb-2">
              Holdings will appear here once you add investments.
            </p>
            <p className="text-xs text-muted-foreground">
              Try adding a transaction, importing your CAS file, or adding stocks/FDs manually.
            </p>
          </CardContent>
        </Card>
      ) : Object.keys(groupedHoldings).length > 0 ? (
        <Tabs defaultValue={Object.keys(groupedHoldings)[0] || ''} className="space-y-4">
          <TabsList>
            {Object.keys(groupedHoldings).map((type) => (
              <TabsTrigger key={type} value={type}>
                {assetTypeLabels[type as AssetType] || type} ({groupedHoldings[type]?.length || 0})
              </TabsTrigger>
            ))}
          </TabsList>

          {Object.entries(groupedHoldings).map(([type, typeHoldings]) => (
            <TabsContent key={type} value={type} className="space-y-4">
              <div className="grid gap-4">
                {(typeHoldings || []).map((holding) => (
                  <Card key={holding.holding_id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg">
                            {holding.asset?.name || 'Unknown Asset'}
                          </CardTitle>
                          <CardDescription>
                            {holding.asset?.symbol && `${holding.asset.symbol} • `}
                            Quantity: {holding.quantity.toLocaleString()}
                          </CardDescription>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold">
                            {formatCurrency(holding.current_value || 0)}
                          </div>
                          {(holding.unrealized_gain_percentage !== undefined && holding.unrealized_gain_percentage !== null) && (
                            <div
                              className={`text-sm ${
                                (holding.unrealized_gain_percentage || 0) >= 0
                                  ? 'text-green-600'
                                  : 'text-red-600'
                              }`}
                            >
                              {formatPercentage(holding.unrealized_gain_percentage)}
                            </div>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <div className="text-muted-foreground">Invested</div>
                          <div className="font-medium">
                            {formatCurrency(holding.invested_amount)}
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Current Value</div>
                          <div className="font-medium">
                            {formatCurrency(holding.current_value || 0)}
                          </div>
                        </div>
                        <div>
                          <div className="text-muted-foreground">Gain/Loss</div>
                          <div
                            className={`font-medium ${
                              (holding.unrealized_gain || 0) >= 0
                                ? 'text-green-600'
                                : 'text-red-600'
                            }`}
                          >
                            {formatCurrency(holding.unrealized_gain || 0)}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
          ))}
        </Tabs>
      ) : null}
    </div>
  )
}

