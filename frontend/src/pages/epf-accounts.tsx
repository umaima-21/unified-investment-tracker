import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { Plus, RefreshCw, Upload, Building2, User, Calendar, TrendingUp } from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'

export function EPFAccountsPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isAddOpen, setIsAddOpen] = useState(false)

  const { data: holdings, isLoading, error } = useQuery({
    queryKey: ['epf-accounts', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.epfAccounts.holdings)
      return data
    },
  })

  const updateValuesMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.epfAccounts.updateValues)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['epf-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: 'EPF Account values updated successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update EPF values',
        variant: 'destructive',
      })
    },
  })

  const importJsonMutation = useMutation({
    mutationFn: async (jsonFilePath: string) => {
      const { data } = await api.post(endpoints.epfAccounts.importJson, {
        json_file_path: jsonFilePath,
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['epf-accounts'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: data.message || `Imported ${data.imported_count || 0} EPF account(s) successfully`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import EPF accounts from JSON',
        variant: 'destructive',
      })
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">EPF Accounts</h1>
          <p className="text-muted-foreground">
            Manage your Employee Provident Fund accounts
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
          <h1 className="text-3xl font-bold tracking-tight">EPF Accounts</h1>
          <p className="text-muted-foreground">
            Manage your Employee Provident Fund accounts
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading EPF accounts</p>
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
          <h1 className="text-3xl font-bold tracking-tight">EPF Accounts</h1>
          <p className="text-muted-foreground">
            Manage your Employee Provident Fund accounts
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => importJsonMutation.mutate('data/epf_accounts.json')}
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
        </div>
      </div>

      {holdings && holdings.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground">No EPF account holdings found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Click "Import from JSON" to load your EPF account data
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {holdings?.map((holding: any) => (
            <Card key={holding.id} className="overflow-hidden">
              <CardHeader className="border-b bg-muted/30">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-5 w-5 text-muted-foreground" />
                      <CardTitle className="text-xl">
                        {holding.employer || 'EPF Account'}
                      </CardTitle>
                    </div>
                    <CardDescription className="flex items-center gap-2">
                      <User className="h-3 w-3" />
                      {holding.account_holder || 'N/A'}
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-3xl font-bold text-primary">
                      {formatCurrency(holding.total_balance || 0)}
                    </div>
                    <div className="flex items-center justify-end gap-2 mt-1">
                      <Badge variant={holding.status === 'active' ? 'default' : 'secondary'}>
                        {holding.status || 'Active'}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground">Account Number</div>
                    <div className="font-medium text-sm">{holding.account_number || 'N/A'}</div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground">UAN</div>
                    <div className="font-medium text-sm">{holding.uan || 'N/A'}</div>
                  </div>
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                      <Calendar className="h-3 w-3" />
                      Date of Joining
                    </div>
                    <div className="font-medium text-sm">
                      {holding.date_of_joining ? formatDate(holding.date_of_joining) : 'N/A'}
                    </div>
                  </div>
                  {holding.date_of_leaving && (
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Date of Leaving</div>
                      <div className="font-medium text-sm">
                        {formatDate(holding.date_of_leaving)}
                      </div>
                    </div>
                  )}
                  <div className="space-y-1">
                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" />
                      Interest Rate
                    </div>
                    <div className="font-medium text-sm">{holding.interest_rate || 0}% p.a.</div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
                  <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-blue-900 dark:text-blue-100">
                        Member Contribution
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground">Principal</span>
                          <span className="font-semibold text-blue-900 dark:text-blue-100">
                            {formatCurrency(holding.member_contribution || 0)}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground">Interest</span>
                          <span className="font-semibold text-green-600 dark:text-green-400">
                            +{formatCurrency(holding.interest_member || 0)}
                          </span>
                        </div>
                        <div className="flex justify-between items-center pt-2 border-t">
                          <span className="text-sm font-medium">Total</span>
                          <span className="font-bold text-blue-900 dark:text-blue-100">
                            {formatCurrency((holding.member_contribution || 0) + (holding.interest_member || 0))}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-purple-50 dark:bg-purple-950/20 border-purple-200 dark:border-purple-900">
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm font-medium text-purple-900 dark:text-purple-100">
                        Employer Contribution
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground">Principal</span>
                          <span className="font-semibold text-purple-900 dark:text-purple-100">
                            {formatCurrency(holding.employer_contribution || 0)}
                          </span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground">Interest</span>
                          <span className="font-semibold text-green-600 dark:text-green-400">
                            +{formatCurrency(holding.interest_employer || 0)}
                          </span>
                        </div>
                        <div className="flex justify-between items-center pt-2 border-t">
                          <span className="text-sm font-medium">Total</span>
                          <span className="font-bold text-purple-900 dark:text-purple-100">
                            {formatCurrency((holding.employer_contribution || 0) + (holding.interest_employer || 0))}
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <div className="mt-4 p-4 bg-muted/50 rounded-lg">
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-xs text-muted-foreground">Total Invested</div>
                      <div className="text-lg font-bold mt-1">
                        {formatCurrency(holding.invested_amount || 0)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Total Interest</div>
                      <div className="text-lg font-bold text-green-600 dark:text-green-400 mt-1">
                        {formatCurrency(holding.returns_absolute || 0)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">Returns</div>
                      <div className="text-lg font-bold text-green-600 dark:text-green-400 mt-1">
                        {(holding.returns_percentage || 0).toFixed(2)}%
                      </div>
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

