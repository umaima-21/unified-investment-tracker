import { useHoldings } from '@/hooks/use-holdings'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'
import { Building2, TrendingUp, TrendingDown } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function DematAccountsPage() {
  const { data: holdings, isLoading } = useHoldings()

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Demat Accounts</h1>
          <p className="text-muted-foreground">
            View your demat holdings across all accounts
          </p>
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  // Group holdings by folio number (which represents demat account for stocks/ETFs)
  const dematHoldings = holdings?.filter(h => 
    h.asset?.asset_type === 'STOCK' || 
    (h.asset?.asset_type === 'MF' && h.folio_number?.startsWith('IN'))
  ) || []

  // Group by folio number (demat account)
  const accountsMap = new Map<string, any[]>()
  dematHoldings.forEach(holding => {
    const accountId = holding.folio_number || 'Unknown'
    if (!accountsMap.has(accountId)) {
      accountsMap.set(accountId, [])
    }
    accountsMap.get(accountId)?.push(holding)
  })

  const accounts = Array.from(accountsMap.entries()).map(([accountId, holdings]) => {
    const totalValue = holdings.reduce((sum, h) => sum + (h.current_value || 0), 0)
    const totalInvested = holdings.reduce((sum, h) => sum + (h.invested_amount || 0), 0)
    const totalGain = totalValue - totalInvested
    const totalGainPct = totalInvested > 0 ? (totalGain / totalInvested) * 100 : 0

    // Separate stocks and ETFs
    const stocks = holdings.filter(h => h.asset?.asset_type === 'STOCK')
    const etfs = holdings.filter(h => h.asset?.asset_type === 'MF')

    return {
      accountId,
      holdings,
      stocks,
      etfs,
      totalValue,
      totalInvested,
      totalGain,
      totalGainPct,
    }
  }).sort((a, b) => b.totalValue - a.totalValue)

  if (accounts.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Demat Accounts</h1>
          <p className="text-muted-foreground">
            View your demat holdings across all accounts
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <Building2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-2">No demat holdings found</p>
            <p className="text-sm text-muted-foreground">
              Import your CAS file to view demat holdings
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Demat Accounts</h1>
        <p className="text-muted-foreground">
          View your demat holdings across all accounts
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Accounts</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{accounts.length}</div>
            <p className="text-xs text-muted-foreground">
              {dematHoldings.length} total holdings
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(accounts.reduce((sum, a) => sum + a.totalValue, 0))}
            </div>
            <p className="text-xs text-muted-foreground">
              Across all demat accounts
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Returns</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={`text-2xl font-bold ${
              accounts.reduce((sum, a) => sum + a.totalGain, 0) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(accounts.reduce((sum, a) => sum + a.totalGain, 0))}
            </div>
            <p className={`text-xs ${
              accounts.reduce((sum, a) => sum + a.totalGain, 0) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatPercentage(
                accounts.reduce((sum, a) => sum + a.totalInvested, 0) > 0
                  ? (accounts.reduce((sum, a) => sum + a.totalGain, 0) / accounts.reduce((sum, a) => sum + a.totalInvested, 0)) * 100
                  : 0
              )}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Account Details */}
      <div className="space-y-4">
        {accounts.map((account) => (
          <Card key={account.accountId}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="h-5 w-5" />
                    Demat Account
                  </CardTitle>
                  <CardDescription className="mt-1">
                    BO ID: <span className="font-mono">{account.accountId}</span>
                  </CardDescription>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold">{formatCurrency(account.totalValue)}</div>
                  <div className={`text-sm ${
                    account.totalGainPct >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {account.totalGainPct >= 0 ? '+' : ''}{formatPercentage(account.totalGainPct)}
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="stocks" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="stocks">
                    Stocks ({account.stocks.length})
                  </TabsTrigger>
                  <TabsTrigger value="etfs">
                    ETFs ({account.etfs.length})
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="stocks" className="space-y-4 mt-4">
                  {account.stocks.length === 0 ? (
                    <p className="text-center text-muted-foreground py-4">No stocks in this account</p>
                  ) : (
                    <div className="space-y-3">
                      {account.stocks.map((holding: any) => (
                        <div key={holding.holding_id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex-1">
                            <div className="font-medium">{holding.asset?.name || 'Unknown'}</div>
                            <div className="text-sm text-muted-foreground">
                              {holding.asset?.symbol && (
                                <span className="font-mono">{holding.asset.symbol}</span>
                              )}
                              {holding.asset?.isin && (
                                <span className="ml-2">ISIN: <span className="font-mono">{holding.asset.isin}</span></span>
                              )}
                            </div>
                            <div className="text-sm text-muted-foreground mt-1">
                              Qty: {holding.quantity?.toLocaleString() || 0}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold">{formatCurrency(holding.current_value || 0)}</div>
                            {holding.unrealized_gain_percentage !== null && holding.unrealized_gain_percentage !== undefined && (
                              <div className={`text-sm flex items-center gap-1 justify-end ${
                                holding.unrealized_gain_percentage >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {holding.unrealized_gain_percentage >= 0 ? (
                                  <TrendingUp className="h-3 w-3" />
                                ) : (
                                  <TrendingDown className="h-3 w-3" />
                                )}
                                {formatPercentage(holding.unrealized_gain_percentage)}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="etfs" className="space-y-4 mt-4">
                  {account.etfs.length === 0 ? (
                    <p className="text-center text-muted-foreground py-4">No ETFs in this account</p>
                  ) : (
                    <div className="space-y-3">
                      {account.etfs.map((holding: any) => (
                        <div key={holding.holding_id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div className="flex-1">
                            <div className="font-medium">{holding.asset?.name || 'Unknown'}</div>
                            <div className="text-sm text-muted-foreground">
                              {holding.asset?.isin && (
                                <span>ISIN: <span className="font-mono">{holding.asset.isin}</span></span>
                              )}
                            </div>
                            <div className="text-sm text-muted-foreground mt-1">
                              Units: {holding.quantity?.toLocaleString(undefined, {maximumFractionDigits: 3}) || 0}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="font-bold">{formatCurrency(holding.current_value || 0)}</div>
                            {holding.unrealized_gain_percentage !== null && holding.unrealized_gain_percentage !== undefined && (
                              <div className={`text-sm flex items-center gap-1 justify-end ${
                                holding.unrealized_gain_percentage >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {holding.unrealized_gain_percentage >= 0 ? (
                                  <TrendingUp className="h-3 w-3" />
                                ) : (
                                  <TrendingDown className="h-3 w-3" />
                                )}
                                {formatPercentage(holding.unrealized_gain_percentage)}
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

