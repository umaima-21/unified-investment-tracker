import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'
import { Upload, Wallet, Building2 } from 'lucide-react'
import { formatCurrency } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'

export function LiquidPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: holdings, isLoading, error } = useQuery({
    queryKey: ['liquid', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.liquid.holdings)
      return data
    },
  })

  const importJsonMutation = useMutation({
    mutationFn: async (jsonFilePath: string) => {
      const { data } = await api.post(endpoints.liquid.importJson, {
        json_file_path: jsonFilePath,
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['liquid'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: data.message || `Imported ${data.imported_count || 0} liquid account(s) successfully`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import liquid accounts from JSON',
        variant: 'destructive',
      })
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Liquid Accounts</h1>
          <p className="text-muted-foreground">
            Manage your savings and liquid accounts
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
          <h1 className="text-3xl font-bold tracking-tight">Liquid Accounts</h1>
          <p className="text-muted-foreground">
            Manage your savings and liquid accounts
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading liquid accounts</p>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error ? error.message : 'Failed to fetch data. Please check if the backend is running.'}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const totalValue = holdings?.reduce((sum: number, h: any) => sum + (h.market_value || 0), 0) || 0

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Liquid Accounts</h1>
          <p className="text-muted-foreground">
            Manage your savings and liquid accounts
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => importJsonMutation.mutate('data/liquid.json')}
            disabled={importJsonMutation.isPending}
          >
            <Upload className={`mr-2 h-4 w-4 ${importJsonMutation.isPending ? 'animate-spin' : ''}`} />
            Import from JSON
          </Button>
        </div>
      </div>

      {/* Summary Card */}
      {holdings && holdings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Wallet className="h-5 w-5" />
              Portfolio Summary
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Total Accounts</div>
                <div className="text-2xl font-bold mt-1">{holdings.length}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Total Value</div>
                <div className="text-2xl font-bold mt-1">{formatCurrency(totalValue)}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Average per Account</div>
                <div className="text-2xl font-bold mt-1">
                  {formatCurrency(holdings.length > 0 ? totalValue / holdings.length : 0)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {holdings && holdings.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground">No liquid account holdings found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Click "Import from JSON" to load your liquid account data
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {holdings?.map((holding: any) => (
            <Card key={holding.id}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Building2 className="h-5 w-5 text-purple-600" />
                      {holding.account_name || 'Liquid Account'}
                    </CardTitle>
                    <CardDescription>
                      {holding.account_number && `Account: ${holding.account_number} • `}
                      {holding.account_type || 'Savings Account'}
                    </CardDescription>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold">
                      {formatCurrency(holding.market_value || 0)}
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <div className="text-muted-foreground">Account Number</div>
                    <div className="font-medium">{holding.account_number || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Account Type</div>
                    <div className="font-medium">{holding.account_type || 'Savings Account'}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Balance</div>
                    <div className="font-medium">{formatCurrency(holding.market_value || 0)}</div>
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

