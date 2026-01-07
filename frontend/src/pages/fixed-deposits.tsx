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
import { Plus, RefreshCw, Upload } from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

export function FixedDepositsPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isAddOpen, setIsAddOpen] = useState(false)

  const { data: holdings, isLoading, error } = useQuery({
    queryKey: ['fixed-deposits', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.fixedDeposits.holdings)
      return data
    },
  })

  const addFDMutation = useMutation({
    mutationFn: async (fdData: {
      name: string
      bank: string
      principal: number
      interest_rate: number
      start_date: string
      maturity_date: string
      compounding_frequency: string
    }) => {
      const { data } = await api.post(endpoints.fixedDeposits.add, fdData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fixed-deposits'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      setIsAddOpen(false)
      toast({
        title: 'Success',
        description: 'Fixed Deposit added successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to add Fixed Deposit',
        variant: 'destructive',
      })
    },
  })

  const updateValuesMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.fixedDeposits.updateValues)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fixed-deposits'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: 'Fixed Deposit values updated successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update FD values',
        variant: 'destructive',
      })
    },
  })

  const importJsonMutation = useMutation({
    mutationFn: async (jsonFilePath: string) => {
      const { data } = await api.post(endpoints.fixedDeposits.importJson, {
        json_file_path: jsonFilePath,
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['fixed-deposits'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: `Imported ${data.imported} FD(s) successfully${data.failed > 0 ? ` (${data.failed} failed)` : ''}`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import FDs from JSON',
        variant: 'destructive',
      })
    },
  })

  const handleAddFD = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const name = formData.get('name') as string
    const bank = formData.get('bank') as string
    const principal = parseFloat(formData.get('principal') as string)
    const interestRate = parseFloat(formData.get('interest_rate') as string)
    const startDate = formData.get('start_date') as string
    const maturityDate = formData.get('maturity_date') as string
    const compoundingFrequency = formData.get('compounding_frequency') as string

    addFDMutation.mutate({
      name,
      bank,
      principal,
      interest_rate: interestRate,
      start_date: startDate,
      maturity_date: maturityDate,
      compounding_frequency: compoundingFrequency,
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Fixed Deposits</h1>
          <p className="text-muted-foreground">
            Manage your fixed deposit investments
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
          <h1 className="text-3xl font-bold tracking-tight">Fixed Deposits</h1>
          <p className="text-muted-foreground">
            Manage your fixed deposit investments
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading fixed deposits</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Fixed Deposits</h1>
          <p className="text-muted-foreground">
            Manage your fixed deposit investments
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => importJsonMutation.mutate('data/fd_icici.json')}
            disabled={importJsonMutation.isPending}
          >
            <Upload className={`mr-2 h-4 w-4 ${importJsonMutation.isPending ? 'animate-spin' : ''}`} />
            Import from JSON
          </Button>
          <Button
            variant="outline"
            onClick={() => updateValuesMutation.mutate()}
            disabled={updateValuesMutation.isPending}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${updateValuesMutation.isPending ? 'animate-spin' : ''}`} />
            Update Values
          </Button>
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Fixed Deposit
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add Fixed Deposit</DialogTitle>
                <DialogDescription>
                  Add a new fixed deposit investment
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleAddFD} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">FD Name *</Label>
                    <Input
                      id="name"
                      name="name"
                      placeholder="e.g., FD-001"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bank">Bank/Institution *</Label>
                    <Input
                      id="bank"
                      name="bank"
                      placeholder="e.g., HDFC Bank"
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="principal">Principal Amount (₹) *</Label>
                    <Input
                      id="principal"
                      name="principal"
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="interest_rate">Interest Rate (%) *</Label>
                    <Input
                      id="interest_rate"
                      name="interest_rate"
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      required
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="start_date">Start Date *</Label>
                    <Input
                      id="start_date"
                      name="start_date"
                      type="date"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="maturity_date">Maturity Date *</Label>
                    <Input
                      id="maturity_date"
                      name="maturity_date"
                      type="date"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="compounding_frequency">Compounding Frequency</Label>
                  <Select name="compounding_frequency" defaultValue="quarterly">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="monthly">Monthly</SelectItem>
                      <SelectItem value="quarterly">Quarterly</SelectItem>
                      <SelectItem value="half-yearly">Half-Yearly</SelectItem>
                      <SelectItem value="yearly">Yearly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <DialogFooter>
                  <Button variant="outline" type="button" onClick={() => setIsAddOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={addFDMutation.isPending}>
                    {addFDMutation.isPending ? 'Adding...' : 'Add Fixed Deposit'}
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
            <p className="text-muted-foreground">No fixed deposit holdings found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Click "Add Fixed Deposit" to start tracking your FD investments
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
                      {holding.asset?.name || 'Unknown FD'}
                    </CardTitle>
                    <CardDescription>
                      {holding.asset?.symbol && `${holding.asset.symbol} • `}
                      {holding.maturity_date && `Matures: ${formatDate(holding.maturity_date)}`}
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">
                      {formatCurrency(holding.current_value || holding.invested_amount || 0)}
                    </div>
                    {holding.interest_rate && (
                      <div className="text-sm text-muted-foreground">
                        Rate: {holding.interest_rate}%
                      </div>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Principal</div>
                    <div className="font-medium">{formatCurrency(holding.invested_amount || 0)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Current Value</div>
                    <div className="font-medium">{formatCurrency(holding.current_value || holding.invested_amount || 0)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Start Date</div>
                    <div className="font-medium">
                      {holding.start_date ? formatDate(holding.start_date) : 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Maturity Date</div>
                    <div className="font-medium">
                      {holding.maturity_date ? formatDate(holding.maturity_date) : 'N/A'}
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

