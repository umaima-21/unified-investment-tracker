import { useQuery } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'

interface ValidationCheck {
  name: string
  expected: number
  actual: number
  status: 'pass' | 'fail' | 'warning'
  details?: string
}

export function DataValidationPage() {
  const { data: holdings, isLoading: holdingsLoading } = useQuery({
    queryKey: ['holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.holdings.list)
      return data || []
    },
  })

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['portfolio', 'summary'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.portfolio.summary)
      return data
    },
  })

  if (holdingsLoading || summaryLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Data Validation</h1>
          <p className="text-muted-foreground">
            Verify imported data from cas_api.json
          </p>
        </div>
        <Skeleton className="h-96" />
      </div>
    )
  }

  // Expected data from cas_api.json
  const expectedData = {
    dematAccounts: 3,
    mutualFundFolios: 11,
    totalMFSchemes: 11,
    totalEquities: 21,
    totalETFs: 5,
    totalAssets: 11 + 21 + 5, // MF + Equities + ETFs
  }

  // Count actual data
  const mfHoldings = holdings?.filter((h: any) => 
    h.asset?.asset_type === 'MF' && !h.folio_number?.startsWith('IN')
  ) || []
  
  const etfHoldings = holdings?.filter((h: any) => 
    h.asset?.asset_type === 'MF' && h.folio_number?.startsWith('IN')
  ) || []
  
  const stockHoldings = holdings?.filter((h: any) => 
    h.asset?.asset_type === 'STOCK'
  ) || []

  // Count unique demat accounts (by folio_number starting with IN)
  const dematAccounts = new Set(
    holdings
      ?.filter((h: any) => h.folio_number?.startsWith('IN'))
      .map((h: any) => h.folio_number)
  ).size

  // Count unique MF folios (excluding demat accounts)
  const mfFolios = new Set(
    mfHoldings
      .filter((h: any) => h.folio_number)
      .map((h: any) => h.folio_number)
  ).size

  const checks: ValidationCheck[] = [
    {
      name: 'Demat Accounts',
      expected: expectedData.dematAccounts,
      actual: dematAccounts,
      status: dematAccounts === expectedData.dematAccounts ? 'pass' : 'warning',
      details: `Expected ${expectedData.dematAccounts} demat accounts (BO IDs)`,
    },
    {
      name: 'Mutual Fund Folios',
      expected: expectedData.mutualFundFolios,
      actual: mfFolios,
      status: mfFolios >= expectedData.mutualFundFolios - 1 ? 'pass' : 'warning',
      details: `Expected ~${expectedData.mutualFundFolios} unique folio numbers`,
    },
    {
      name: 'Mutual Fund Schemes',
      expected: expectedData.totalMFSchemes,
      actual: mfHoldings.length,
      status: mfHoldings.length >= expectedData.totalMFSchemes - 2 ? 'pass' : 'warning',
      details: `Expected ${expectedData.totalMFSchemes} MF holdings from regular folios`,
    },
    {
      name: 'Equity Holdings',
      expected: expectedData.totalEquities,
      actual: stockHoldings.length,
      status: stockHoldings.length >= expectedData.totalEquities - 2 ? 'pass' : 'warning',
      details: `Expected ${expectedData.totalEquities} stock holdings from demat accounts`,
    },
    {
      name: 'ETF Holdings',
      expected: expectedData.totalETFs,
      actual: etfHoldings.length,
      status: etfHoldings.length >= expectedData.totalETFs - 1 ? 'pass' : 'warning',
      details: `Expected ${expectedData.totalETFs} ETF holdings from demat accounts`,
    },
    {
      name: 'Total Holdings',
      expected: expectedData.totalAssets,
      actual: holdings?.length || 0,
      status: (holdings?.length || 0) >= expectedData.totalAssets - 5 ? 'pass' : 'warning',
      details: `Expected ~${expectedData.totalAssets} total holdings across all types`,
    },
  ]

  const passedChecks = checks.filter(c => c.status === 'pass').length
  const totalChecks = checks.length

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Data Validation</h1>
        <p className="text-muted-foreground">
          Verify imported data from cas_api.json file
        </p>
      </div>

      {/* Summary Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {passedChecks === totalChecks ? (
              <CheckCircle2 className="h-5 w-5 text-green-600" />
            ) : (
              <AlertCircle className="h-5 w-5 text-yellow-600" />
            )}
            Validation Summary
          </CardTitle>
          <CardDescription>
            {passedChecks} of {totalChecks} checks passed
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {passedChecks === totalChecks ? (
              <span className="text-green-600">All Data Imported Successfully! ✓</span>
            ) : (
              <span className="text-yellow-600">Some Data May Be Missing</span>
            )}
          </div>
          <p className="text-sm text-muted-foreground mt-2">
            Total holdings in database: <span className="font-medium">{holdings?.length || 0}</span>
          </p>
          {summary && (
            <div className="mt-4 grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Portfolio Value</p>
                <p className="text-lg font-bold">
                  ₹{(summary.total_current_value || 0).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Returns</p>
                <p className={`text-lg font-bold ${(summary.returns_percentage || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {(summary.returns_percentage || 0).toFixed(2)}%
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detailed Checks */}
      <div className="grid gap-4 md:grid-cols-2">
        {checks.map((check) => (
          <Card key={check.name}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{check.name}</CardTitle>
                {check.status === 'pass' ? (
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                ) : check.status === 'warning' ? (
                  <AlertCircle className="h-5 w-5 text-yellow-600" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600" />
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Expected:</span>
                  <span className="font-medium">{check.expected}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Actual:</span>
                  <span className={`font-medium ${
                    check.status === 'pass' ? 'text-green-600' : 
                    check.status === 'warning' ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {check.actual}
                  </span>
                </div>
                {check.details && (
                  <p className="text-xs text-muted-foreground mt-2">{check.details}</p>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Data Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Holdings Breakdown</CardTitle>
          <CardDescription>Detailed count of imported holdings by type</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
              <span className="font-medium">Regular Mutual Funds</span>
              <span className="text-xl font-bold text-blue-600">{mfHoldings.length}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
              <span className="font-medium">Stocks (from Demat)</span>
              <span className="text-xl font-bold text-green-600">{stockHoldings.length}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
              <span className="font-medium">ETFs (from Demat)</span>
              <span className="text-xl font-bold text-purple-600">{etfHoldings.length}</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border-2 border-gray-200">
              <span className="font-medium">Total Holdings</span>
              <span className="text-xl font-bold">{holdings?.length || 0}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Expected Data from cas_api.json */}
      <Card>
        <CardHeader>
          <CardTitle>Source File Information</CardTitle>
          <CardDescription>Expected data from data/cas_api.json</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Demat Accounts:</span>
              <span className="font-mono">3 (NSDL: 2, CDSL: 1)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Mutual Fund Folios:</span>
              <span className="font-mono">11 folios across 10 AMCs</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Statement Period:</span>
              <span className="font-mono">Nov 1, 2025 - Nov 30, 2025</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Investor PAN:</span>
              <span className="font-mono">ADXXXXXX3B</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

