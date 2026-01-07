import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { Plus, RefreshCw, Upload } from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

export function PPFAccountsPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isAddOpen, setIsAddOpen] = useState(false)

  const { data: holdings, isLoading, error } = useQuery({
    queryKey: ['ppf-accounts', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.ppfAccounts.holdings)
      return data
    },
  })

  const addPPFMutation = useMutation({
    mutationFn: async (ppfData: {
      account_number: string
      bank: string
      account_holder: string
      current_balance: number
      interest_rate: number
      opening_date: string
    }) => {
      const { data } = await api.post(endpoints.ppfAccounts.add, ppfData)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ppf-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      setIsAddOpen(false)
      toast({
        title: 'Success',
        description: 'PPF Account added successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to add PPF Account',
        variant: 'destructive',
      })
    },
  })

  const updateValuesMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.ppfAccounts.updateValues)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ppf-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: 'PPF Account values updated successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update PPF values',
        variant: 'destructive',
      })
    },
  })

  const importJsonMutation = useMutation({
    mutationFn: async (jsonFilePath: string) => {
      const { data } = await api.post(endpoints.ppfAccounts.importJson, {
        json_file_path: jsonFilePath,
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['ppf-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: `Imported ${data.imported} PPF account(s) successfully${data.failed > 0 ? ` (${data.failed} failed)` : ''}`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import PPF accounts from JSON',
        variant: 'destructive',
      })
    },
  })

  const handleAddPPF = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const accountNumber = formData.get('account_number') as string
    const bank = formData.get('bank') as string
    const accountHolder = formData.get('account_holder') as string
    const currentBalance = parseFloat(formData.get('current_balance') as string)
    const interestRate = parseFloat(formData.get('interest_rate') as string)
    const openingDate = formData.get('opening_date') as string

    addPPFMutation.mutate({
      account_number: accountNumber,
      bank,
      account_holder: accountHolder,
      current_balance: currentBalance,
      interest_rate: interestRate,
      opening_date: openingDate,
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">PPF Accounts</h1>
          <p className="text-muted-foreground">
            Manage your Public Provident Fund accounts
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
          <h1 className="text-3xl font-bold tracking-tight">PPF Accounts</h1>
          <p className="text-muted-foreground">
            Manage your Public Provident Fund accounts
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading PPF accounts</p>
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
          <h1 className="text-3xl font-bold tracking-tight">PPF Accounts</h1>
          <p className="text-muted-foreground">
            Manage your Public Provident Fund accounts
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => importJsonMutation.mutate('data/ppf_sbi.json')}
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
                Add PPF Account
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Add PPF Account</DialogTitle>
                <DialogDescription>
                  Add a new Public Provident Fund account
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleAddPPF} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="account_number">Account Number *</Label>
                    <Input
                      id="account_number"
                      name="account_number"
                      placeholder="e.g., 000000104350883O8"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bank">Bank *</Label>
                    <Input
                      id="bank"
                      name="bank"
                      placeholder="e.g., State Bank of India"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="account_holder">Account Holder *</Label>
                  <Input
                    id="account_holder"
                    name="account_holder"
                    placeholder="e.g., Mrs. UMAIMA HUSEINI SURTI"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="current_balance">Current Balance (₹) *</Label>
                    <Input
                      id="current_balance"
                      name="current_balance"
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
                      placeholder="7.1"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="opening_date">Opening Date *</Label>
                  <Input
                    id="opening_date"
                    name="opening_date"
                    type="date"
                    required
                  />
                </div>
                <DialogFooter>
                  <Button variant="outline" type="button" onClick={() => setIsAddOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={addPPFMutation.isPending}>
                    {addPPFMutation.isPending ? 'Adding...' : 'Add PPF Account'}
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
            <p className="text-muted-foreground">No PPF account holdings found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Click "Import from JSON" to load your PPF account data or "Add PPF Account" to manually add one
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
                      {holding.asset?.name || 'PPF Account'}
                    </CardTitle>
                    <CardDescription>
                      {holding.asset?.symbol && `Account: ${holding.asset.symbol} • `}
                      {holding.account_holder || 'N/A'}
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">
                      {formatCurrency(holding.current_value || holding.invested_amount || 0)}
                    </div>
                    {holding.interest_rate && (
                      <div className="text-sm text-muted-foreground">
                        Interest Rate: {holding.interest_rate}%
                      </div>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Bank</div>
                    <div className="font-medium">{holding.bank || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Opening Date</div>
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
                  <div>
                    <div className="text-muted-foreground">Status</div>
                    <div className="font-medium capitalize">
                      {holding.status || 'Active'}
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

