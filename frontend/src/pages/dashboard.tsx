import { usePortfolioSummary, usePortfolioHistory, usePortfolioAllocation } from '@/hooks/use-portfolio'
import { useHoldings } from '@/hooks/use-holdings'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { TrendingUp, TrendingDown, Wallet, DollarSign, PieChart, BarChart3, Activity, Landmark, Building2, LineChart, Globe } from 'lucide-react'
import { PortfolioChart } from '@/components/dashboard/portfolio-chart'
import { AllocationChart } from '@/components/dashboard/allocation-chart'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

function MetricCard({ 
  title, 
  value, 
  change, 
  icon: Icon 
}: { 
  title: string
  value: string
  change?: number
  icon: React.ElementType
}) {
  const isPositive = change !== undefined && change >= 0
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change !== undefined && (
          <p className={`text-xs flex items-center gap-1 mt-1 ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
            {isPositive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
            {formatPercentage(change)}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

export function DashboardPage() {
  const { data: summary, isLoading: summaryLoading } = usePortfolioSummary()
  const { data: history, isLoading: historyLoading } = usePortfolioHistory(30)
  const { data: allocation, isLoading: allocationLoading } = usePortfolioAllocation()
  const { data: holdings, isLoading: holdingsLoading } = useHoldings()

  if (summaryLoading) {
    return (
      <div className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-24" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-8 w-32" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  const returnsPercentage = summary?.returns_percentage || 0
  const totalInvested = summary?.total_invested || 0
  const totalValue = summary?.total_current_value || 0
  const totalReturns = summary?.total_returns || 0

  // Calculate asset type breakdown
  const assetAllocation = allocation?.asset_allocation || {}
  const mfAllocation = assetAllocation['MF'] || { current_value: 0, invested: 0, percentage: 0 }
  const stockAllocation = assetAllocation['STOCK'] || { current_value: 0, invested: 0, percentage: 0 }
  const cryptoAllocation = assetAllocation['CRYPTO'] || { current_value: 0, invested: 0, percentage: 0 }
  const fdAllocation = assetAllocation['FD'] || { current_value: 0, invested: 0, percentage: 0 }
  const ppfAllocation = assetAllocation['PPF'] || { current_value: 0, invested: 0, percentage: 0 }
  const epfAllocation = assetAllocation['EPF'] || { current_value: 0, invested: 0, percentage: 0 }
  
  // Get US Stocks and Liquid allocations from holdings
  const usStocksHoldings = holdings?.filter((h: any) => 
    h.asset?.asset_type === 'STOCK' && h.asset?.exchange === 'US'
  ) || []
  const usStocksAllocation = usStocksHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })
  
  const liquidHoldings = holdings?.filter((h: any) => 
    h.asset?.extra_data?.is_liquid === true
  ) || []
  const liquidAllocation = liquidHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })
  
  // Calculate percentages
  if (totalValue > 0) {
    usStocksAllocation.percentage = (usStocksAllocation.current_value / totalValue) * 100
    liquidAllocation.percentage = (liquidAllocation.current_value / totalValue) * 100
  }

  const isEtfHolding = (holding: any) => {
    const name = (holding?.asset?.name || '').toUpperCase()
    const assetType = holding?.asset?.asset_type
    const folio = holding?.folio_number || ''
    const dematFolio = ((folio.startsWith('IN') || folio.startsWith('12')) && folio.length === 16)
    
    // ETF if: name contains "ETF" OR (MF type with demat folio - demat MFs/ETFs)
    return name.includes('ETF') || (assetType === 'MF' && dematFolio)
  }

  // Separate Stocks and ETFs
  // Stocks: STOCK type that are not ETFs (by name)
  const stockHoldings = holdings?.filter(h => {
    const assetType = h.asset?.asset_type
    const name = (h.asset?.name || '').toUpperCase()
    return assetType === 'STOCK' && !name.includes('ETF')
  }) || []
  
  // ETFs: Holdings with "ETF" in name OR MF type with demat folio
  const etfHoldings = holdings?.filter(h => isEtfHolding(h)) || []

  // Calculate separate allocations for Stocks and ETFs
  const stockAllocationSeparated = stockHoldings.reduce((acc, h) => {
    const currentValue = h.current_value || 0
    const invested = h.invested_amount || 0
    acc.current_value += currentValue
    acc.invested += invested
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })

  const etfAllocation = etfHoldings.reduce((acc, h) => {
    const currentValue = h.current_value || 0
    const invested = h.invested_amount || 0
    acc.current_value += currentValue
    acc.invested += invested
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })

  // Calculate percentages
  if (totalValue > 0) {
    stockAllocationSeparated.percentage = (stockAllocationSeparated.current_value / totalValue) * 100
    etfAllocation.percentage = (etfAllocation.current_value / totalValue) * 100
  }

  // Get top performers
  const topPerformers = holdings
    ?.filter(h => h.unrealized_gain_percentage && h.current_value && h.current_value > 1000)
    ?.sort((a, b) => (b.unrealized_gain_percentage || 0) - (a.unrealized_gain_percentage || 0))
    ?.slice(0, 5) || []

  // Get top losers
  const topLosers = holdings
    ?.filter(h => h.unrealized_gain_percentage && h.unrealized_gain_percentage < 0 && h.current_value && h.current_value > 1000)
    ?.sort((a, b) => (a.unrealized_gain_percentage || 0) - (b.unrealized_gain_percentage || 0))
    ?.slice(0, 5) || []

  // Get largest holdings by value
  const largestHoldings = holdings
    ?.filter(h => h.current_value && h.current_value > 0)
    ?.sort((a, b) => (b.current_value || 0) - (a.current_value || 0))
    ?.slice(0, 5) || []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Portfolio Dashboard</h1>
        <p className="text-muted-foreground">
          Comprehensive overview of your investments
        </p>
      </div>

      {/* Main Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Invested"
          value={formatCurrency(totalInvested)}
          icon={DollarSign}
        />
        <MetricCard
          title="Current Value"
          value={formatCurrency(totalValue)}
          icon={Wallet}
        />
        <MetricCard
          title="Total Returns"
          value={formatCurrency(totalReturns)}
          change={returnsPercentage}
          icon={TrendingUp}
        />
        <MetricCard
          title="Returns %"
          value={formatPercentage(returnsPercentage)}
          change={returnsPercentage}
          icon={Activity}
        />
      </div>

      {/* Asset Type Breakdown */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Mutual Funds</CardTitle>
            <PieChart className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(mfAllocation.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(mfAllocation.percentage)} of portfolio
            </p>
            <p className={`text-xs mt-1 ${
              (mfAllocation.current_value - mfAllocation.invested) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(mfAllocation.current_value - mfAllocation.invested)} gain
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Stocks</CardTitle>
            <BarChart3 className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stockAllocationSeparated.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(stockAllocationSeparated.percentage)} of portfolio
            </p>
            <p className={`text-xs mt-1 ${
              (stockAllocationSeparated.current_value - stockAllocationSeparated.invested) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(stockAllocationSeparated.current_value - stockAllocationSeparated.invested)} gain
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ETFs</CardTitle>
            <LineChart className="h-4 w-4 text-emerald-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(etfAllocation.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(etfAllocation.percentage)} of portfolio
            </p>
            <p className={`text-xs mt-1 ${
              (etfAllocation.current_value - etfAllocation.invested) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(etfAllocation.current_value - etfAllocation.invested)} gain
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cryptocurrency</CardTitle>
            <Activity className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(cryptoAllocation.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(cryptoAllocation.percentage)} of portfolio
            </p>
            <p className={`text-xs mt-1 ${
              (cryptoAllocation.current_value - cryptoAllocation.invested) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(cryptoAllocation.current_value - cryptoAllocation.invested)} gain
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Fixed Deposits</CardTitle>
            <Wallet className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(fdAllocation.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(fdAllocation.percentage)} of portfolio
            </p>
            <p className={`text-xs mt-1 ${
              (fdAllocation.current_value - fdAllocation.invested) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(fdAllocation.current_value - fdAllocation.invested)} gain
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">PPF Accounts</CardTitle>
            <Landmark className="h-4 w-4 text-indigo-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(ppfAllocation.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(ppfAllocation.percentage)} of portfolio
            </p>
            <p className={`text-xs mt-1 ${
              (ppfAllocation.current_value - ppfAllocation.invested) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(ppfAllocation.current_value - ppfAllocation.invested)} gain
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">EPF Accounts</CardTitle>
            <Building2 className="h-4 w-4 text-teal-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(epfAllocation.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(epfAllocation.percentage)} of portfolio
            </p>
            <p className={`text-xs mt-1 ${
              (epfAllocation.current_value - epfAllocation.invested) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(epfAllocation.current_value - epfAllocation.invested)} gain
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">US Stocks</CardTitle>
            <Globe className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(usStocksAllocation.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(usStocksAllocation.percentage)} of portfolio
            </p>
            <p className={`text-xs mt-1 ${
              (usStocksAllocation.current_value - usStocksAllocation.invested) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(usStocksAllocation.current_value - usStocksAllocation.invested)} gain
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Liquid</CardTitle>
            <Wallet className="h-4 w-4 text-cyan-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(liquidAllocation.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(liquidAllocation.percentage)} of portfolio
            </p>
            <p className="text-xs mt-1 text-muted-foreground">
              No gain/loss (liquid)
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Portfolio Value Over Time</CardTitle>
            <CardDescription>Last 30 days</CardDescription>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <Skeleton className="h-[300px]" />
            ) : (
              <PortfolioChart data={history || []} />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Asset Allocation</CardTitle>
            <CardDescription>By asset type</CardDescription>
          </CardHeader>
          <CardContent>
            {allocationLoading ? (
              <Skeleton className="h-[300px]" />
            ) : (
              <AllocationChart data={allocation?.asset_allocation || {}} />
            )}
          </CardContent>
        </Card>
      </div>

      {/* Holdings Analysis */}
      <Tabs defaultValue="top-performers" className="space-y-4">
        <TabsList>
          <TabsTrigger value="top-performers">Top Performers</TabsTrigger>
          <TabsTrigger value="top-losers">Underperformers</TabsTrigger>
          <TabsTrigger value="largest">Largest Holdings</TabsTrigger>
        </TabsList>

        <TabsContent value="top-performers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top 5 Performers</CardTitle>
              <CardDescription>Holdings with highest returns</CardDescription>
            </CardHeader>
            <CardContent>
              {holdingsLoading ? (
                <Skeleton className="h-48" />
              ) : topPerformers.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No holdings data available</p>
              ) : (
                <div className="space-y-4">
                  {topPerformers.map((holding, idx) => (
                    <div key={holding.holding_id} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm text-muted-foreground">#{idx + 1}</span>
                          <span className="font-medium">{holding.asset?.name || 'Unknown'}</span>
                        </div>
                        <p className="text-sm text-muted-foreground">{holding.asset?.asset_type}</p>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">{formatCurrency(holding.current_value || 0)}</div>
                        <div className="text-green-600 text-sm font-medium">
                          +{formatPercentage(holding.unrealized_gain_percentage || 0)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="top-losers" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top 5 Underperformers</CardTitle>
              <CardDescription>Holdings with lowest returns</CardDescription>
            </CardHeader>
            <CardContent>
              {holdingsLoading ? (
                <Skeleton className="h-48" />
              ) : topLosers.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No underperforming holdings</p>
              ) : (
                <div className="space-y-4">
                  {topLosers.map((holding, idx) => (
                    <div key={holding.holding_id} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm text-muted-foreground">#{idx + 1}</span>
                          <span className="font-medium">{holding.asset?.name || 'Unknown'}</span>
                        </div>
                        <p className="text-sm text-muted-foreground">{holding.asset?.asset_type}</p>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">{formatCurrency(holding.current_value || 0)}</div>
                        <div className="text-red-600 text-sm font-medium">
                          {formatPercentage(holding.unrealized_gain_percentage || 0)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="largest" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Top 5 Largest Holdings</CardTitle>
              <CardDescription>By current value</CardDescription>
            </CardHeader>
            <CardContent>
              {holdingsLoading ? (
                <Skeleton className="h-48" />
              ) : largestHoldings.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">No holdings data available</p>
              ) : (
                <div className="space-y-4">
                  {largestHoldings.map((holding, idx) => (
                    <div key={holding.holding_id} className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm text-muted-foreground">#{idx + 1}</span>
                          <span className="font-medium">{holding.asset?.name || 'Unknown'}</span>
                        </div>
                        <p className="text-sm text-muted-foreground">{holding.asset?.asset_type}</p>
                      </div>
                      <div className="text-right">
                        <div className="font-bold">{formatCurrency(holding.current_value || 0)}</div>
                        <div className={`text-sm font-medium ${
                          (holding.unrealized_gain_percentage || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatPercentage(holding.unrealized_gain_percentage || 0)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

