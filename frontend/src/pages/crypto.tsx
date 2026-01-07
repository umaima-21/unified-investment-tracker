import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/components/ui/use-toast'
import { RefreshCw, Download, Upload, RotateCcw, ChevronRight, ExternalLink, Trash2 } from 'lucide-react'
import { formatCurrency, formatPercentage, formatDate } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'
import { useTransactions } from '@/hooks/use-transactions'

export function CryptoPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [fileType, setFileType] = useState<string>('auto')
  const [selectedHolding, setSelectedHolding] = useState<string | null>(null)
  const [isTransactionsDialogOpen, setIsTransactionsDialogOpen] = useState(false)

  const { data: holdings, isLoading, error } = useQuery({
    queryKey: ['crypto', 'holdings'],
    queryFn: async () => {
      try {
        const { data } = await api.get(endpoints.crypto.holdings)
        console.log('Crypto holdings response:', data)
        return data || []
      } catch (err: any) {
        console.error('Error fetching crypto holdings:', err)
        throw err
      }
    },
    retry: 1,
  })

  const syncMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.crypto.sync)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crypto'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: 'Crypto holdings synced successfully from CoinDCX',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to sync crypto holdings. Make sure CoinDCX API is configured.',
        variant: 'destructive',
      })
    },
  })

  const refreshPortfolioMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.portfolio.refresh)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      queryClient.invalidateQueries({ queryKey: ['crypto'] })
      toast({
        title: 'Success',
        description: 'Portfolio holdings refreshed successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to refresh portfolio holdings',
        variant: 'destructive',
      })
    },
  })

  const updatePricesMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.crypto.updatePrices)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crypto'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: 'Crypto prices updated successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update crypto prices',
        variant: 'destructive',
      })
    },
  })

  const uploadStatementMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const { data } = await api.post(endpoints.crypto.importStatement, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: async (data) => {
      // Invalidate all related queries
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['crypto'] }),
        queryClient.invalidateQueries({ queryKey: ['holdings'] }),
        queryClient.invalidateQueries({ queryKey: ['portfolio'] }),
        queryClient.invalidateQueries({ queryKey: ['transactions'] }),
        queryClient.invalidateQueries({ queryKey: ['assets'] }),
      ])

      setIsUploadOpen(false)
      setSelectedFile(null)
      setFileType('auto')

      const transactionsImported = data?.transactions_imported || 0
      const transactionsUpdated = data?.transactions_updated || 0
      const rowsSkipped = data?.rows_skipped || 0
      const skippedReasons = data?.skipped_reasons || {}
      const columnsFound = data?.columns_found || []

      // Use the message from backend if available
      let message = data?.message || ''

      // Add detailed diagnostics if no transactions were imported or updated
      const totalProcessed = transactionsImported + transactionsUpdated
      if (totalProcessed === 0) {
        const details: string[] = []
        if (columnsFound.length > 0) {
          details.push(`Found columns: ${columnsFound.slice(0, 5).join(', ')}${columnsFound.length > 5 ? '...' : ''}`)
        }
        if (rowsSkipped > 0) {
          const reasonStr = Object.entries(skippedReasons)
            .map(([k, v]) => `${k}: ${v}`)
            .join(', ')
          details.push(`Skipped ${rowsSkipped} rows (${reasonStr})`)
        }
        if (details.length > 0) {
          message += ` | ${details.join(' | ')}`
        }
        message += ' | Check console for details. Ensure file has: symbol/currency, date, type, quantity/amount columns.'
      }

      // Log detailed info to console for debugging
      if (totalProcessed === 0) {
        console.warn('Crypto import details:', {
          columnsFound,
          rowsSkipped,
          skippedReasons,
          fullMessage: data?.message
        })
      }

      toast({
        title: totalProcessed > 0 ? 'Success' : 'Warning - No Transactions Processed',
        description: message,
        variant: totalProcessed > 0 ? 'default' : 'destructive',
        duration: totalProcessed === 0 ? 15000 : 5000, // Show longer if no transactions
      })

      // Force refetch after a short delay
      setTimeout(() => {
        queryClient.refetchQueries({ queryKey: ['crypto', 'holdings'] })
        queryClient.refetchQueries({ queryKey: ['holdings'] })
      }, 1000)
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import crypto statement',
        variant: 'destructive',
      })
    },
  })

  const handleFileUpload = () => {
    if (!selectedFile) {
      toast({
        title: 'Error',
        description: 'Please select a file',
        variant: 'destructive',
      })
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('file_type', fileType)

    uploadStatementMutation.mutate(formData)
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cryptocurrency</h1>
          <p className="text-muted-foreground">
            Manage your cryptocurrency investments
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
          <h1 className="text-3xl font-bold tracking-tight">Cryptocurrency</h1>
          <p className="text-muted-foreground">
            Manage your cryptocurrency investments
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading crypto holdings</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Cryptocurrency</h1>
          <p className="text-muted-foreground">
            Manage your cryptocurrency investments
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refreshPortfolioMutation.mutate()}
            disabled={refreshPortfolioMutation.isPending}
          >
            <RotateCcw className={`mr-2 h-4 w-4 ${refreshPortfolioMutation.isPending ? 'animate-spin' : ''}`} />
            Refresh Holdings
          </Button>
          <Button
            variant="outline"
            onClick={() => updatePricesMutation.mutate()}
            disabled={updatePricesMutation.isPending}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${updatePricesMutation.isPending ? 'animate-spin' : ''}`} />
            Update Prices
          </Button>
          <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Upload className="mr-2 h-4 w-4" />
                Upload Statement
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Upload Crypto Statement</DialogTitle>
                <DialogDescription>
                  Upload your crypto statement file (PDF, CSV, or Excel)
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="file">Statement File</Label>
                  <Input
                    id="file"
                    type="file"
                    accept=".pdf,.csv,.xlsx,.xls"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="file_type">File Type (optional)</Label>
                  <Select value={fileType} onValueChange={setFileType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto">Auto-detect</SelectItem>
                      <SelectItem value="pdf">PDF</SelectItem>
                      <SelectItem value="csv">CSV</SelectItem>
                      <SelectItem value="excel">Excel</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsUploadOpen(false)}>
                  Cancel
                </Button>
                <Button onClick={handleFileUpload} disabled={uploadStatementMutation.isPending}>
                  {uploadStatementMutation.isPending ? 'Uploading...' : 'Upload'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Button
            variant="outline"
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
          >
            <Download className={`mr-2 h-4 w-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
            Sync from CoinDCX
          </Button>
        </div>
      </div>

      {!holdings || (Array.isArray(holdings) && holdings.length === 0) ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground mb-4">No crypto holdings found</p>
            <p className="text-sm text-muted-foreground mb-4">
              Get started by uploading your crypto statement or syncing from CoinDCX
            </p>
            <div className="flex gap-2 justify-center">
              <Button variant="outline" onClick={() => setIsUploadOpen(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Upload Statement
              </Button>
              <Button variant="outline" onClick={() => syncMutation.mutate()}>
                <Download className="mr-2 h-4 w-4" />
                Sync from CoinDCX
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-4">
              Supported formats: PDF, CSV, Excel. You can also add transactions manually.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {(Array.isArray(holdings) ? holdings : []).map((holding: any) => (
            <Card
              key={holding.holding_id}
              className="cursor-pointer hover:bg-accent/50 transition-colors"
              onClick={() => {
                setSelectedHolding(holding.asset_id)
                setIsTransactionsDialogOpen(true)
              }}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg flex items-center gap-2">
                      {holding.asset?.name || 'Unknown Crypto'}
                      <ChevronRight className="h-4 w-4 text-muted-foreground" />
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
                        className={`text-sm ${(holding.unrealized_gain_percentage || 0) >= 0
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
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Quantity</div>
                    <div className="font-medium">{holding.quantity.toLocaleString()}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Invested</div>
                    <div className="font-medium">{formatCurrency(holding.invested_amount)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Current Value</div>
                    <div className="font-medium">{formatCurrency(holding.current_value || 0)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Gain/Loss</div>
                    <div
                      className={`font-medium ${(holding.unrealized_gain || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}
                    >
                      {formatCurrency(holding.unrealized_gain || 0)}
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t text-xs text-muted-foreground flex items-center gap-1">
                  <ExternalLink className="h-3 w-3" />
                  Click to view transaction details
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Transactions Dialog */}
      <Dialog open={isTransactionsDialogOpen} onOpenChange={setIsTransactionsDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <TransactionsDialogContent assetId={selectedHolding} />
        </DialogContent>
      </Dialog>
    </div>
  )
}

// Component to display transactions for a specific asset
function TransactionsDialogContent({ assetId }: { assetId: string | null }) {
  // All hooks must be at the top, before any conditional returns
  const { data: transactions, isLoading, error } = useTransactions(assetId || undefined, undefined, 500)
  const { data: assets } = useQuery({
    queryKey: ['assets'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.assets.list)
      return data || []
    },
  })
  const queryClient = useQueryClient()
  const { toast } = useToast()

  const deleteTransactionMutation = useMutation({
    mutationFn: async (transactionId: string) => {
      const { data } = await api.delete(`/api/crypto/transactions/${transactionId}`)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['crypto'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: 'Transaction deleted successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete transaction',
        variant: 'destructive',
      })
    },
  })

  const asset = assets?.find((a: any) => a.asset_id === assetId)
  const transactionsArray = Array.isArray(transactions) ? transactions : []

  if (isLoading) {
    return (
      <div className="space-y-4">
        <DialogHeader>
          <DialogTitle>Transaction Details</DialogTitle>
          <DialogDescription>Loading transactions...</DialogDescription>
        </DialogHeader>
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
        <Skeleton className="h-20 w-full" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="space-y-4">
        <DialogHeader>
          <DialogTitle>Transaction Details</DialogTitle>
          <DialogDescription>
            Error loading transactions
          </DialogDescription>
        </DialogHeader>
        <Card>
          <CardContent className="py-6 text-center">
            <p className="text-destructive">
              {error instanceof Error ? error.message : 'Failed to load transactions'}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <DialogHeader>
        <DialogTitle>
          Transaction Details - {asset?.name || 'Unknown Asset'}
        </DialogTitle>
        <DialogDescription>
          {asset?.symbol && `${asset.symbol} • `}
          {transactionsArray.length} transaction{transactionsArray.length !== 1 ? 's' : ''} found
        </DialogDescription>
      </DialogHeader>

      {transactionsArray.length === 0 ? (
        <Card>
          <CardContent className="py-6 text-center">
            <p className="text-muted-foreground">No transactions found for this asset</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {/* Table Header - Matching Excel format */}
          <div className="grid grid-cols-11 gap-2 text-xs font-semibold text-muted-foreground border-b pb-2 sticky top-0 bg-background">
            <div>Trade ID</div>
            <div>Crypto</div>
            <div>Trade Completion Time</div>
            <div>Side</div>
            <div>Avg Price (INR)</div>
            <div>Quantity</div>
            <div>Gross Amount (INR)</div>
            <div>Fees (INR)</div>
            <div>Net Amount (INR)</div>
            <div>Description</div>
            <div className="text-right">Actions</div>
          </div>

          {/* Transaction Rows */}
          <div className="space-y-1 max-h-[60vh] overflow-y-auto">
            {transactionsArray.map((transaction: any) => {
              // Extract Trade ID from reference_id or description
              const tradeId = transaction.reference_id ||
                (transaction.description?.match(/Trade ID[:\s]+([^\s|]+)/i)?.[1]) ||
                transaction.description?.match(/([a-f0-9-]{36})/i)?.[1] ||
                transaction.transaction_id.substring(0, 8)

              // Format date and time (matching Excel format: YYYY-MM-DD HH:MM:SS)
              const dateTime = new Date(transaction.transaction_date);
              const year = dateTime.getFullYear();
              const month = String(dateTime.getMonth() + 1).padStart(2, '0');
              const day = String(dateTime.getDate()).padStart(2, '0');
              const hours = String(dateTime.getHours()).padStart(2, '0');
              const minutes = String(dateTime.getMinutes()).padStart(2, '0');
              const seconds = String(dateTime.getSeconds()).padStart(2, '0');
              const formattedDateTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;

              // Extract fees and net amount from description if available
              const feesMatch = transaction.description?.match(/Fees[:\s]+₹?([\d.]+)/i)
              const fees = feesMatch ? parseFloat(feesMatch[1]) : 0

              const netMatch = transaction.description?.match(/Net[:\s]+₹?([\d.]+)/i)
              const netAmount = netMatch ? parseFloat(netMatch[1]) : (transaction.amount || 0)

              // Gross amount is the transaction amount (or calculate from net + fees for buy, net - fees for sell)
              const grossAmount = transaction.amount || 0

              return (
                <Card key={transaction.transaction_id} className="border-l-4 border-l-primary/20 hover:bg-accent/50">
                  <CardContent className="py-2 px-3">
                    <div className="grid grid-cols-11 gap-2 text-xs items-center">
                      <div className="font-mono text-[10px] truncate" title={tradeId}>
                        {tradeId}
                      </div>
                      <div className="font-medium">
                        {asset?.symbol || 'N/A'}
                      </div>
                      <div className="font-mono text-[10px]">
                        {formattedDateTime}
                      </div>
                      <div>
                        <span
                          className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${transaction.transaction_type === 'BUY' || transaction.transaction_type === 'DEPOSIT'
                            ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                            : transaction.transaction_type === 'SELL' || transaction.transaction_type === 'WITHDRAW' || transaction.transaction_type === 'WITHDRAWAL'
                              ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                              : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                            }`}
                        >
                          {transaction.transaction_type === 'DEPOSIT' ? 'Buy' :
                            transaction.transaction_type === 'WITHDRAW' || transaction.transaction_type === 'WITHDRAWAL' ? 'Sell' :
                              transaction.transaction_type}
                        </span>
                      </div>
                      <div className="text-right">
                        {transaction.price ? formatCurrency(transaction.price) : '-'}
                      </div>
                      <div className="text-right">
                        {transaction.units ? transaction.units.toLocaleString(undefined, { maximumFractionDigits: 8 }) : '-'}
                      </div>
                      <div className="text-right font-medium">
                        {formatCurrency(grossAmount)}
                      </div>
                      <div className="text-right text-muted-foreground">
                        {fees > 0 ? formatCurrency(fees) : '-'}
                      </div>
                      <div className="text-right font-semibold">
                        {formatCurrency(netAmount)}
                      </div>
                      <div className="text-[10px] text-muted-foreground truncate" title={transaction.description}>
                        {transaction.description?.replace(/Imported from statement:.*?\(Sheet:.*?\)/i, '').trim() || '-'}
                      </div>
                      <div className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 text-destructive hover:text-destructive hover:bg-destructive/10"
                          onClick={(e) => {
                            e.stopPropagation()
                            if (confirm('Are you sure you want to delete this transaction?')) {
                              deleteTransactionMutation.mutate(transaction.transaction_id)
                            }
                          }}
                          disabled={deleteTransactionMutation.isPending}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}

