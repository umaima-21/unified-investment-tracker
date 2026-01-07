import { useState } from 'react'
import { useTransactions, useCreateTransaction } from '@/hooks/use-transactions'
import { useAssets } from '@/hooks/use-assets'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Plus } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'

export function TransactionsPage() {
  const [assetFilter, setAssetFilter] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const { data: transactions, isLoading, error } = useTransactions(assetFilter || undefined, typeFilter || undefined)
  const { data: assets, isLoading: assetsLoading } = useAssets()
  const createTransaction = useCreateTransaction()

  // Debug logging
  console.log('Transactions data:', transactions)
  console.log('Assets data:', assets)

  const [formData, setFormData] = useState({
    asset_id: '',
    transaction_type: 'BUY',
    transaction_date: new Date().toISOString().split('T')[0],
    units: '',
    price: '',
    amount: '',
    description: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await createTransaction.mutateAsync({
        asset_id: formData.asset_id,
        transaction_type: formData.transaction_type,
        transaction_date: new Date(formData.transaction_date).toISOString(),
        units: formData.units ? parseFloat(formData.units) : undefined,
        price: formData.price ? parseFloat(formData.price) : undefined,
        amount: parseFloat(formData.amount),
        description: formData.description || undefined,
      })
      setIsDialogOpen(false)
      setFormData({
        asset_id: '',
        transaction_type: 'BUY',
        transaction_date: new Date().toISOString().split('T')[0],
        units: '',
        price: '',
        amount: '',
        description: '',
      })
    } catch (error) {
      // Error handled by mutation
    }
  }

  if (isLoading || assetsLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Transactions</h1>
          <p className="text-muted-foreground">
            View and manage your investment transactions
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
          <h1 className="text-3xl font-bold tracking-tight">Transactions</h1>
          <p className="text-muted-foreground">
            View and manage your investment transactions
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading transactions</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Transactions</h1>
          <p className="text-muted-foreground">
            View and manage your investment transactions
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Add Transaction
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Add Transaction</DialogTitle>
              <DialogDescription>
                Record a new investment transaction
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="asset_id">Asset</Label>
                  <Select
                    value={formData.asset_id}
                    onValueChange={(value) => setFormData({ ...formData, asset_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select asset" />
                    </SelectTrigger>
                    <SelectContent>
                      {assets?.map((asset) => (
                        <SelectItem key={asset.asset_id} value={asset.asset_id}>
                          {asset.name} ({asset.asset_type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="transaction_type">Type</Label>
                  <Select
                    value={formData.transaction_type}
                    onValueChange={(value) => setFormData({ ...formData, transaction_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BUY">Buy</SelectItem>
                      <SelectItem value="SELL">Sell</SelectItem>
                      <SelectItem value="DIVIDEND">Dividend</SelectItem>
                      <SelectItem value="INTEREST">Interest</SelectItem>
                      <SelectItem value="REDEMPTION">Redemption</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="transaction_date">Date</Label>
                  <Input
                    id="transaction_date"
                    type="date"
                    value={formData.transaction_date}
                    onChange={(e) => setFormData({ ...formData, transaction_date: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="amount">Amount</Label>
                  <Input
                    id="amount"
                    type="number"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="units">Units (optional)</Label>
                  <Input
                    id="units"
                    type="number"
                    step="0.0001"
                    value={formData.units}
                    onChange={(e) => setFormData({ ...formData, units: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="price">Price (optional)</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description (optional)</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={createTransaction.isPending}>
                  {createTransaction.isPending ? 'Creating...' : 'Create Transaction'}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="flex gap-4">
        <Select value={assetFilter || 'all'} onValueChange={(value) => setAssetFilter(value === 'all' ? '' : value)}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by asset" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Assets</SelectItem>
            {assets?.map((asset) => (
              <SelectItem key={asset.asset_id} value={asset.asset_id}>
                {asset.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={typeFilter || 'all'} onValueChange={(value) => setTypeFilter(value === 'all' ? '' : value)}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="Filter by type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="BUY">Buy</SelectItem>
            <SelectItem value="SELL">Sell</SelectItem>
            <SelectItem value="DIVIDEND">Dividend</SelectItem>
            <SelectItem value="INTEREST">Interest</SelectItem>
            <SelectItem value="REDEMPTION">Redemption</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {!transactions || (Array.isArray(transactions) && transactions.length === 0) ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground mb-4">No transactions found</p>
            <p className="text-sm text-muted-foreground mb-4">
              Start tracking your investments by adding your first transaction
            </p>
            <Button onClick={() => setIsDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Transaction
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {(Array.isArray(transactions) ? transactions : []).map((transaction) => (
            <Card key={transaction.transaction_id}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold">
                      {transaction.asset?.name || 'Unknown Asset'}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {formatDate(transaction.transaction_date)} • {transaction.transaction_type}
                    </div>
                    {transaction.description && (
                      <div className="text-sm text-muted-foreground mt-1">
                        {transaction.description}
                      </div>
                    )}
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold">
                      {formatCurrency(transaction.amount)}
                    </div>
                    {transaction.units && (
                      <div className="text-sm text-muted-foreground">
                        {transaction.units.toLocaleString()} units
                      </div>
                    )}
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

