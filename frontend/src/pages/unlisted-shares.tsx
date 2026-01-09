import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'
import { Upload, TrendingUp, TrendingDown, Building2 } from 'lucide-react'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

export function UnlistedSharesPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: holdings, isLoading, error } = useQuery({
    queryKey: ['unlisted-shares', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.unlistedShares.holdings)
      return data
    },
  })

  const importJsonMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.unlistedShares.importJson, null, {
        params: { json_file_path: 'data/cas_api.json' },
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['unlisted-shares'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: data.message || `Imported ${data.unlisted_shares_imported || 0} unlisted share(s) successfully`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import unlisted shares from JSON',
        variant: 'destructive',
      })
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Unlisted Shares</h1>
          <p className="text-muted-foreground">
            Manage your unlisted share investments
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
          <h1 className="text-3xl font-bold tracking-tight">Unlisted Shares</h1>
          <p className="text-muted-foreground">
            Manage your unlisted share investments
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading unlisted shares</p>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error ? error.message : 'Failed to fetch data. Please check if the backend is running.'}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const totalInvested = holdings?.reduce((sum: number, h: any) => sum + (h.invested_amount || 0), 0) || 0
  const totalValue = holdings?.reduce((sum: number, h: any) => sum + (h.current_value || 0), 0) || 0
  const totalGain = holdings?.reduce((sum: number, h: any) => sum + (h.unrealized_gain || 0), 0) || 0
  const totalGainPercentage = totalInvested > 0 ? (totalGain / totalInvested) * 100 : 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Unlisted Shares</h1>
          <p className="text-muted-foreground">
            Manage your unlisted share investments
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => importJsonMutation.mutate()}
            disabled={importJsonMutation.isPending}
          >
            <Upload className="mr-2 h-4 w-4" />
            {importJsonMutation.isPending ? 'Importing...' : 'Load from Data Folder'}
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Invested</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalInvested)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Current Value</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalValue)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Gain/Loss</CardTitle>
            {totalGain >= 0 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-red-600" />
            )}
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${totalGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatCurrency(totalGain)}
            </div>
            <p className={`text-xs mt-1 ${totalGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercentage(totalGainPercentage)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Holdings */}
      {holdings && holdings.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <Building2 className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-2">No unlisted shares found</p>
            <p className="text-sm text-muted-foreground">
              Click "Load from Data Folder" to import unlisted shares from cas_api.json
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {holdings?.map((holding: any) => {
            const gain = holding.unrealized_gain || 0
            const gainPercentage = holding.unrealized_gain_percentage || 0
            const currentPricePerUnit = holding.latest_price || (holding.current_value && holding.quantity ? holding.current_value / holding.quantity : 0)
            const purchasePricePerUnit = holding.avg_price || 0

            return (
              <Card key={holding.holding_id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg flex items-center gap-2">
                        <Building2 className="h-5 w-5 text-amber-600" />
                        {holding.asset?.name || 'Unknown'}
                      </CardTitle>
                      <CardDescription>
                        {holding.asset?.isin && `ISIN: ${holding.asset.isin}`}
                      </CardDescription>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold">
                        {formatCurrency(holding.current_value || 0)}
                      </div>
                      <div className={`text-sm font-medium mt-1 ${gainPercentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercentage(gainPercentage)}
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Units</div>
                      <div className="font-medium">{holding.quantity?.toFixed(2) || '0.00'}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Purchase Price/Unit</div>
                      <div className="font-medium">{formatCurrency(purchasePricePerUnit)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Invested Amount</div>
                      <div className="font-medium">{formatCurrency(holding.invested_amount || 0)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Current Price/Unit</div>
                      <div className="font-medium">{formatCurrency(currentPricePerUnit)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Current Value</div>
                      <div className="font-medium">{formatCurrency(holding.current_value || 0)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Gain/Loss</div>
                      <div className={`font-medium ${gain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(gain)}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Gain/Loss %</div>
                      <div className={`font-medium ${gainPercentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercentage(gainPercentage)}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}

