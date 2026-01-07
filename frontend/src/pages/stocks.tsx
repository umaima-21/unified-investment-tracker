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
import { Plus, RefreshCw } from 'lucide-react'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

export function StocksPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isAddOpen, setIsAddOpen] = useState(false)

  const { data: holdings, isLoading, error } = useQuery({
    queryKey: ['stocks', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.stocks.holdings)
      return data
    },
  })

  const addStockMutation = useMutation({
    mutationFn: async (stockData: {
      symbol: string
      name: string
      quantity: number
      invested_amount: number
      exchange: string
      isin?: string
    }) => {
      const { data } = await api.post(endpoints.stocks.add, stockData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stocks'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      setIsAddOpen(false)
      toast({
        title: 'Success',
        description: 'Stock added successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to add stock',
        variant: 'destructive',
      })
    },
  })

  const updatePricesMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.stocks.updatePrices)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['stocks'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: 'Stock prices updated successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update prices',
        variant: 'destructive',
      })
    },
  })

  const handleAddStock = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const symbol = formData.get('symbol') as string
    const name = formData.get('name') as string
    const quantity = parseFloat(formData.get('quantity') as string)
    const investedAmount = parseFloat(formData.get('invested_amount') as string)
    const exchange = formData.get('exchange') as string
    const isin = formData.get('isin') as string

    addStockMutation.mutate({
      symbol: symbol.toUpperCase(),
      name,
      quantity,
      invested_amount: investedAmount,
      exchange,
      isin: isin || undefined,
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Stocks</h1>
          <p className="text-muted-foreground">
            Manage your stock investments
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
          <h1 className="text-3xl font-bold tracking-tight">Stocks</h1>
          <p className="text-muted-foreground">
            Manage your stock investments
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading stocks</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Stocks</h1>
          <p className="text-muted-foreground">
            Manage your stock investments
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => updatePricesMutation.mutate()}
            disabled={updatePricesMutation.isPending}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${updatePricesMutation.isPending ? 'animate-spin' : ''}`} />
            Update Prices
          </Button>
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Stock
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add Stock</DialogTitle>
                <DialogDescription>
                  Manually add a stock holding
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleAddStock} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="symbol">Stock Symbol *</Label>
                    <Input
                      id="symbol"
                      name="symbol"
                      placeholder="e.g., RELIANCE, TCS"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="name">Company Name *</Label>
                    <Input
                      id="name"
                      name="name"
                      placeholder="e.g., Reliance Industries Ltd"
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="exchange">Exchange</Label>
                    <Select name="exchange" defaultValue="NSE">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="NSE">NSE</SelectItem>
                        <SelectItem value="BSE">BSE</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="isin">ISIN (optional)</Label>
                    <Input
                      id="isin"
                      name="isin"
                      placeholder="e.g., INE467B01029"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="quantity">Quantity *</Label>
                    <Input
                      id="quantity"
                      name="quantity"
                      type="number"
                      step="0.01"
                      placeholder="0"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="invested_amount">Invested Amount (₹) *</Label>
                    <Input
                      id="invested_amount"
                      name="invested_amount"
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      required
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" type="button" onClick={() => setIsAddOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={addStockMutation.isPending}>
                    {addStockMutation.isPending ? 'Adding...' : 'Add Stock'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {holdings && holdings.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground">No stock holdings found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Click "Add Stock" to start tracking your stock investments
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {holdings?.map((holding: any) => (
            <Card key={holding.holding_id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">
                      {holding.asset?.name || 'Unknown Stock'}
                    </CardTitle>
                    <CardDescription>
                      {holding.asset?.symbol && `${holding.asset.symbol} • `}
                      {holding.asset?.exchange && `${holding.asset.exchange} • `}
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
                      className={`font-medium ${
                        (holding.unrealized_gain || 0) >= 0 ? 'text-green-600' : 'text-red-600'
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
      )}
    </div>
  )
}

