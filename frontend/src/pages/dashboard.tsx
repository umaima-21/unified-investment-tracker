import { usePortfolioSummary, usePortfolioHistory, usePortfolioAllocation } from '@/hooks/use-portfolio'
import { useHoldings } from '@/hooks/use-holdings'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { TrendingUp, TrendingDown, Wallet, DollarSign, PieChart, BarChart3, Activity, Landmark, Building2, LineChart, Globe, Shield, Package } from 'lucide-react'
import { PortfolioChart } from '@/components/dashboard/portfolio-chart'
import { AllocationChart } from '@/components/dashboard/allocation-chart'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useQuery } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'

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
  
  // Get insurance holdings (payouts, not included in Current Value)
  const { data: insuranceHoldings, isLoading: insuranceLoading } = useQuery({
    queryKey: ['insurance', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.insurance.holdings)
      return data || []
    },
  })

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
  const totalReturns = summary?.total_returns || 0

  // Calculate asset type breakdown from holdings to ensure consistency
  const assetAllocation = allocation?.asset_allocation || {}
  
  // Helper function to check if holding is ETF
  const isEtfHolding = (holding: any) => {
    const name = (holding?.asset?.name || '').toUpperCase()
    const assetType = holding?.asset?.asset_type
    const folio = holding?.folio_number || ''
    const dematFolio = ((folio.startsWith('IN') || folio.startsWith('12')) && folio.length === 16)
    
    // ETF if: name contains "ETF" OR (MF type with demat folio - demat MFs/ETFs)
    // Note: STOCK type with "ETF" in name should also be considered ETF
    return name.includes('ETF') || (assetType === 'MF' && dematFolio)
  }

  // Calculate all allocations from holdings to ensure consistency
  // Mutual Funds: MF type that are NOT ETFs
  const mfHoldings = holdings?.filter((h: any) => 
    h.asset?.asset_type === 'MF' && !isEtfHolding(h)
  ) || []
  const mfAllocation = mfHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })

  // Stocks: STOCK type that are not ETFs and not US stocks
  const stockHoldings = holdings?.filter((h: any) => {
    const assetType = h.asset?.asset_type
    const name = (h.asset?.name || '').toUpperCase()
    const exchange = h.asset?.exchange
    return assetType === 'STOCK' && !name.includes('ETF') && exchange !== 'US'
  }) || []
  const stockAllocationSeparated = stockHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })

  // ETFs: Holdings with "ETF" in name OR MF type with demat folio
  // Exclude US stocks (they have their own category)
  const etfHoldings = holdings?.filter((h: any) => 
    isEtfHolding(h) && !(h.asset?.asset_type === 'STOCK' && h.asset?.exchange === 'US')
  ) || []
  const etfAllocation = etfHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })

  // Crypto
  const cryptoHoldings = holdings?.filter((h: any) => h.asset?.asset_type === 'CRYPTO') || []
  const cryptoAllocation = cryptoHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })

  // Fixed Deposits: FD type that are NOT liquid accounts
  const fdHoldings = holdings?.filter((h: any) => 
    h.asset?.asset_type === 'FD' && !h.asset?.extra_data?.is_liquid
  ) || []
  const fdAllocation = fdHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })

  // PPF Accounts
  const ppfHoldings = holdings?.filter((h: any) => h.asset?.asset_type === 'PPF') || []
  const ppfAllocation = ppfHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })

  // EPF Accounts
  const epfHoldings = holdings?.filter((h: any) => h.asset?.asset_type === 'EPF') || []
  const epfAllocation = epfHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })

  // US Stocks: STOCK type with US exchange, excluding ETFs
  const usStocksHoldings = holdings?.filter((h: any) => {
    const assetType = h.asset?.asset_type
    const exchange = h.asset?.exchange
    const name = (h.asset?.name || '').toUpperCase()
    return assetType === 'STOCK' && exchange === 'US' && !name.includes('ETF')
  }) || []
  const usStocksAllocation = usStocksHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })
  
  // Liquid Accounts
  const liquidHoldings = holdings?.filter((h: any) => 
    h.asset?.extra_data?.is_liquid === true
  ) || []
  const liquidAllocation = liquidHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })
  
  // Unlisted Shares
  const unlistedSharesHoldings = holdings?.filter((h: any) => 
    h.asset?.asset_type === 'UNLISTED'
  ) || []
  const unlistedSharesAllocation = unlistedSharesHoldings.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })
  
  // Other Assets
  const otherAssetsHoldingsFromDb = holdings?.filter((h: any) => 
    h.asset?.asset_type === 'OTHER'
  ) || []
  const otherAssetsAllocation = otherAssetsHoldingsFromDb.reduce((acc: any, h: any) => {
    acc.current_value += h.current_value || 0
    acc.invested += h.invested_amount || 0
    return acc
  }, { current_value: 0, invested: 0, percentage: 0 })
  
  // Insurance Policies (payouts - NOT included in Current Value)
  const insuranceAllocation = (insuranceHoldings || []).reduce((acc: any, policy: any) => {
    acc.sum_assured += policy.sum_assured_value || 0
    acc.premium += policy.invested_amount || 0
    acc.annual_premium += policy.annual_premium || 0
    acc.count += 1
    return acc
  }, { sum_assured: 0, premium: 0, annual_premium: 0, count: 0 })

  // Calculate total from all individual allocations to ensure consistency
  // NOTE: Insurance is NOT included in total value as it's a payout, not an investment
  const totalValue = 
    mfAllocation.current_value +
    stockAllocationSeparated.current_value +
    etfAllocation.current_value +
    cryptoAllocation.current_value +
    fdAllocation.current_value +
    ppfAllocation.current_value +
    epfAllocation.current_value +
    usStocksAllocation.current_value +
    liquidAllocation.current_value +
    unlistedSharesAllocation.current_value +
    otherAssetsAllocation.current_value

  // Validation: Check if all holdings are accounted for
  const allCategorizedHoldings = [
    ...mfHoldings,
    ...stockHoldings,
    ...etfHoldings,
    ...cryptoHoldings,
    ...fdHoldings,
    ...ppfHoldings,
    ...epfHoldings,
    ...usStocksHoldings,
    ...liquidHoldings,
    ...unlistedSharesHoldings,
    ...otherAssetsHoldingsFromDb
  ]
  
  // Find uncategorized holdings (for debugging)
  // Exclude insurance and other assets from uncategorized check as they're handled separately
  const uncategorizedHoldings = holdings?.filter((h: any) => {
    const holdingId = h.holding_id
    const assetType = h.asset?.asset_type
    // Skip insurance and other assets as they're handled separately
    if (assetType === 'INSURANCE' || assetType === 'OTHER') return false
    return !allCategorizedHoldings.some((c: any) => c.holding_id === holdingId)
  }) || []
  
  // Calculate total from ALL holdings (including any uncategorized)
  const totalValueFromAllHoldings = holdings?.reduce((sum: number, h: any) => {
    return sum + (h.current_value || 0)
  }, 0) || 0

  // If there's a mismatch, log it for debugging
  if (Math.abs(totalValue - totalValueFromAllHoldings) > 0.01) {
    console.warn('Dashboard calculation mismatch:', {
      totalFromCategories: totalValue,
      totalFromAllHoldings: totalValueFromAllHoldings,
      difference: totalValueFromAllHoldings - totalValue,
      uncategorizedCount: uncategorizedHoldings.length,
      uncategorizedHoldings: uncategorizedHoldings.map((h: any) => ({
        id: h.holding_id,
        name: h.asset?.name,
        type: h.asset?.asset_type,
        exchange: h.asset?.exchange,
        is_liquid: h.asset?.extra_data?.is_liquid,
        current_value: h.current_value
      }))
    })
  }

  // Use the total from all holdings to ensure accuracy
  const finalTotalValue = totalValueFromAllHoldings > 0 ? totalValueFromAllHoldings : totalValue

  // Calculate percentages based on the final total
  if (finalTotalValue > 0) {
    mfAllocation.percentage = (mfAllocation.current_value / finalTotalValue) * 100
    stockAllocationSeparated.percentage = (stockAllocationSeparated.current_value / finalTotalValue) * 100
    etfAllocation.percentage = (etfAllocation.current_value / finalTotalValue) * 100
    cryptoAllocation.percentage = (cryptoAllocation.current_value / finalTotalValue) * 100
    fdAllocation.percentage = (fdAllocation.current_value / finalTotalValue) * 100
    ppfAllocation.percentage = (ppfAllocation.current_value / finalTotalValue) * 100
    epfAllocation.percentage = (epfAllocation.current_value / finalTotalValue) * 100
    usStocksAllocation.percentage = (usStocksAllocation.current_value / finalTotalValue) * 100
    liquidAllocation.percentage = (liquidAllocation.current_value / finalTotalValue) * 100
    unlistedSharesAllocation.percentage = (unlistedSharesAllocation.current_value / finalTotalValue) * 100
    otherAssetsAllocation.percentage = (otherAssetsAllocation.current_value / finalTotalValue) * 100
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
          value={formatCurrency(finalTotalValue)}
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
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
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
            <CardTitle className="text-sm font-medium">Unlisted Shares</CardTitle>
            <Building2 className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(unlistedSharesAllocation.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(unlistedSharesAllocation.percentage)} of portfolio
            </p>
            <p className={`text-xs mt-1 ${
              (unlistedSharesAllocation.current_value - unlistedSharesAllocation.invested) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(unlistedSharesAllocation.current_value - unlistedSharesAllocation.invested)} gain
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

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Other Assets</CardTitle>
            <Package className="h-4 w-4 text-slate-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(otherAssetsAllocation.current_value)}</div>
            <p className="text-xs text-muted-foreground">
              {formatPercentage(otherAssetsAllocation.percentage)} of portfolio
            </p>
            <p className={`text-xs mt-1 ${
              (otherAssetsAllocation.current_value - otherAssetsAllocation.invested) >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatCurrency(otherAssetsAllocation.current_value - otherAssetsAllocation.invested)} gain
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Insurance Policies Section (Payouts - Not included in Current Value) */}
      {insuranceAllocation.count > 0 && (
        <Card className="border-2 border-amber-200 bg-amber-50/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-amber-600" />
              Insurance Policies (Payouts)
            </CardTitle>
            <CardDescription>
              These are payout policies and are not included in Current Value calculation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Policies</p>
                <p className="text-2xl font-bold">{insuranceAllocation.count}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Sum Assured</p>
                <p className="text-2xl font-bold">{formatCurrency(insuranceAllocation.sum_assured)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Annual Premium</p>
                <p className="text-2xl font-bold">{formatCurrency(insuranceAllocation.annual_premium)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Premium Paid</p>
                <p className="text-2xl font-bold">{formatCurrency(insuranceAllocation.premium)}</p>
              </div>
            </div>
            {insuranceLoading ? (
              <Skeleton className="h-32 mt-4" />
            ) : (
              <div className="mt-4 space-y-2">
                {insuranceHoldings?.slice(0, 5).map((policy: any) => (
                  <div key={policy.id} className="flex items-center justify-between p-2 bg-white rounded border">
                    <div className="flex-1">
                      <p className="font-medium">{policy.name}</p>
                      {policy.policy_number && (
                        <p className="text-sm text-muted-foreground">Policy: {policy.policy_number}</p>
                      )}
                      {policy.policy_type && (
                        <p className="text-xs text-muted-foreground">Type: {policy.policy_type}</p>
                      )}
                    </div>
                    <div className="text-right">
                      {policy.sum_assured_value > 0 && (
                        <p className="font-semibold">{formatCurrency(policy.sum_assured_value)}</p>
                      )}
                      <p className="text-sm text-muted-foreground">Annual: {formatCurrency(policy.annual_premium || 0)}</p>
                      <p className="text-xs text-muted-foreground">Paid: {formatCurrency(policy.invested_amount || 0)}</p>
                    </div>
                  </div>
                ))}
                {insuranceHoldings && insuranceHoldings.length > 5 && (
                  <p className="text-sm text-muted-foreground text-center">
                    + {insuranceHoldings.length - 5} more policies
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}

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

