import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'
import { Upload, Globe, TrendingUp } from 'lucide-react'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

export function USStocksPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: holdings, isLoading, error } = useQuery({
    queryKey: ['us-stocks', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.usStocks.holdings)
      return data
    },
  })

  const importJsonMutation = useMutation({
    mutationFn: async (jsonFilePath: string) => {
      const { data } = await api.post(endpoints.usStocks.importJson, {
        json_file_path: jsonFilePath,
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['us-stocks'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: data.message || `Imported ${data.imported_count || 0} US stock holding(s) successfully`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import US stocks from JSON',
        variant: 'destructive',
      })
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">US Stocks</h1>
          <p className="text-muted-foreground">
            Manage your US stock investments
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
          <h1 className="text-3xl font-bold tracking-tight">US Stocks</h1>
          <p className="text-muted-foreground">
            Manage your US stock investments
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading US stocks</p>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error ? error.message : 'Failed to fetch data. Please check if the backend is running.'}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const totalInvested = holdings?.reduce((sum: number, h: any) => sum + (h.invested_amount || 0), 0) || 0
  const totalValue = holdings?.reduce((sum: number, h: any) => sum + (h.market_value || 0), 0) || 0
  const totalGain = holdings?.reduce((sum: number, h: any) => sum + (h.gain_loss || 0), 0) || 0
  const totalGainPercentage = totalInvested > 0 ? (totalGain / totalInvested) * 100 : 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">US Stocks</h1>
          <p className="text-muted-foreground">
            Manage your US stock investments
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => importJsonMutation.mutate('data/us_stocks.json')}
            disabled={importJsonMutation.isPending}
          >
            <Upload className={`mr-2 h-4 w-4 ${importJsonMutation.isPending ? 'animate-spin' : ''}`} />
            Import from JSON
          </Button>
        </div>
      </div>

      {/* Summary Card */}
      {holdings && holdings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="h-5 w-5" />
              Portfolio Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Total Invested</div>
                <div className="text-2xl font-bold mt-1">{formatCurrency(totalInvested)}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Current Value</div>
                <div className="text-2xl font-bold mt-1">{formatCurrency(totalValue)}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Total Gain/Loss</div>
                <div className={`text-2xl font-bold mt-1 ${totalGain >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(totalGain)}
                </div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Returns</div>
                <div className={`text-2xl font-bold mt-1 ${totalGainPercentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercentage(totalGainPercentage)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {holdings && holdings.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground">No US stock holdings found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Click "Import from JSON" to load your US stock data
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {holdings?.map((holding: any) => (
            <Card key={holding.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <TrendingUp className="h-5 w-5 text-blue-600" />
                      {holding.name || 'US Stock'}
                    </CardTitle>
                    <CardDescription>
                      {holding.symbol && `Symbol: ${holding.symbol}`}
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">
                      {formatCurrency(holding.market_value || 0)}
                    </div>
                    <div className={`text-sm font-medium mt-1 ${
                      (holding.gain_loss_percentage || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatPercentage(holding.gain_loss_percentage || 0)}
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Invested Amount</div>
                    <div className="font-medium">{formatCurrency(holding.invested_amount || 0)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Market Value</div>
                    <div className="font-medium">{formatCurrency(holding.market_value || 0)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Gain/Loss</div>
                    <div className={`font-medium ${(holding.gain_loss || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatCurrency(holding.gain_loss || 0)}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Returns</div>
                    <div className={`font-medium ${(holding.gain_loss_percentage || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercentage(holding.gain_loss_percentage || 0)}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

