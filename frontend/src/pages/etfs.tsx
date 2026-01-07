import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { endpoints, api } from '@/lib/api'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { AlertCircle, LineChart, RefreshCw } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { useToast } from '@/components/ui/use-toast'

type Holding = {
  holding_id: string
  folio_number?: string
  quantity?: number
  invested_amount?: number
  current_value?: number
  unrealized_gain?: number
  unrealized_gain_percentage?: number
  annualized_return?: number
  asset?: {
    name?: string
    isin?: string
    asset_type?: string
  }
}

const isEtfHolding = (holding: Holding) => {
  const name = (holding.asset?.name || '').toUpperCase()
  const folio = holding.folio_number || ''
  const dematFolio = ((folio.startsWith('IN') || folio.startsWith('12')) && folio.length === 16)
  return name.includes('ETF') || dematFolio
}

export function ETFsPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  
  const { data: holdings, isLoading, error } = useQuery<Holding[]>({
    queryKey: ['etfs', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.mutualFunds.holdings)
      return data || []
    },
    retry: 1,
  })

  const recalculateMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.mutualFunds.recalculate)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['etfs', 'holdings'] })
      toast({
        title: 'Success',
        description: 'Holdings recalculated successfully. Invested amounts and returns have been updated.',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to recalculate holdings',
        variant: 'destructive',
      })
    },
  })

  const etfHoldings = (Array.isArray(holdings) ? holdings : []).filter(isEtfHolding).map((holding) => {
    // Calculate missing values if not provided by backend
    const invested = Number(holding.invested_amount) || 0
    const current = Number(holding.current_value) || 0
    
    // Create a new object with calculated values
    const enrichedHolding = { ...holding }
    
    // Calculate unrealized gain if missing (allow negative values for losses)
    if ((enrichedHolding.unrealized_gain === null || enrichedHolding.unrealized_gain === undefined) && invested > 0) {
      enrichedHolding.unrealized_gain = current - invested
    }
    
    // Calculate returns percentage if missing
    if ((enrichedHolding.unrealized_gain_percentage === null || enrichedHolding.unrealized_gain_percentage === undefined) && invested > 0) {
      enrichedHolding.unrealized_gain_percentage = ((current - invested) / invested) * 100
    }
    
    return enrichedHolding
  })

  const totalInvested = etfHoldings.reduce((sum, h) => sum + (Number(h.invested_amount) || 0), 0)
  const totalCurrent = etfHoldings.reduce((sum, h) => sum + (Number(h.current_value) || 0), 0)
  const totalGain = totalCurrent - totalInvested
  const totalGainPct = totalInvested > 0 ? (totalGain / totalInvested) * 100 : 0

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-24" />
        <Skeleton className="h-48" />
      </div>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>Failed to load ETF holdings.</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <LineChart className="h-6 w-6 text-emerald-600" />
            ETFs
          </h1>
          <p className="text-muted-foreground">
            Exchange Traded Funds & demat mutual fund units
          </p>
        </div>
        <Button
          onClick={() => recalculateMutation.mutate()}
          disabled={recalculateMutation.isPending}
          variant="outline"
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${recalculateMutation.isPending ? 'animate-spin' : ''}`} />
          Recalculate Holdings
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Total Current Value</CardTitle>
            <CardDescription>All ETF holdings</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-bold">{formatCurrency(totalCurrent)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Total Invested</CardTitle>
            <CardDescription>Cost basis</CardDescription>
          </CardHeader>
          <CardContent className="text-2xl font-bold">{formatCurrency(totalInvested)}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Unrealized P&L</CardTitle>
            <CardDescription>Value - Invested</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalGain)}</div>
            <div className={totalGain >= 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
              {formatPercentage(totalGainPct)}
            </div>
          </CardContent>
        </Card>
      </div>

      {etfHoldings.length === 0 ? (
        <p className="text-muted-foreground">No ETF holdings found.</p>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <h2 className="text-2xl font-bold">ETFs & Demat Mutual Funds</h2>
            <span className="text-sm text-muted-foreground">({etfHoldings.length} holdings)</span>
          </div>
          <div className="grid gap-4">
            {etfHoldings.map((holding) => (
              <Card key={holding.holding_id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">
                        {holding.asset?.name || 'Unknown'}
                      </CardTitle>
                      <CardDescription className="space-x-3">
                        {holding.asset?.isin && (
                          <span>ISIN: <span className="font-mono">{holding.asset.isin}</span></span>
                        )}
                        {holding.folio_number && (
                          <span>BO ID: <span className="font-mono">{holding.folio_number}</span></span>
                        )}
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
                  <div className="grid grid-cols-6 gap-4 text-sm">
                    <div>
                      <div className="text-muted-foreground">Units</div>
                      <div className="font-medium">{holding.quantity || 0}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Invested Amount</div>
                      <div className="font-medium">{formatCurrency(holding.invested_amount || 0)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Current Value</div>
                      <div className="font-medium">{formatCurrency(holding.current_value || 0)}</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Unrealized P&L</div>
                      <div
                        className={`font-medium ${
                          holding.unrealized_gain !== null && holding.unrealized_gain !== undefined
                            ? (holding.unrealized_gain >= 0 ? 'text-green-600' : 'text-red-600')
                            : ''
                        }`}
                      >
                        {holding.unrealized_gain !== null && holding.unrealized_gain !== undefined 
                          ? formatCurrency(holding.unrealized_gain) 
                          : <span className="text-muted-foreground">N/A</span>}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Returns %</div>
                      <div
                        className={`font-medium ${
                          holding.unrealized_gain_percentage !== null && holding.unrealized_gain_percentage !== undefined
                            ? (holding.unrealized_gain_percentage >= 0 ? 'text-green-600' : 'text-red-600')
                            : ''
                        }`}
                      >
                        {holding.unrealized_gain_percentage !== null && holding.unrealized_gain_percentage !== undefined 
                          ? formatPercentage(holding.unrealized_gain_percentage) 
                          : <span className="text-muted-foreground">N/A</span>}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground">Annualized Return</div>
                      <div
                        className={`font-medium ${
                          holding.annualized_return !== null && holding.annualized_return !== undefined
                            ? (holding.annualized_return >= 0 ? 'text-green-600' : 'text-red-600')
                            : ''
                        }`}
                      >
                        {holding.annualized_return !== null && holding.annualized_return !== undefined 
                          ? formatPercentage(holding.annualized_return) 
                          : <span className="text-muted-foreground">N/A</span>}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

