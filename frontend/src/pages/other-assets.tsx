import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { Plus, Upload, Briefcase, Calendar, DollarSign, Percent, FileText, Trash2, RefreshCw, Lock } from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'

export function OtherAssetsPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isAddOpen, setIsAddOpen] = useState(false)

  const { data: holdings, isLoading, error } = useQuery({
    queryKey: ['otherAssets', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.otherAssets.holdings)
      return data
    },
  })

  const clearAllMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.delete(endpoints.otherAssets.clearAll)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['otherAssets'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: data.message || `Cleared ${data.deleted_count || 0} other asset(s)`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to clear other assets',
        variant: 'destructive',
      })
    },
  })

  const importJsonMutation = useMutation({
    mutationFn: async (jsonFilePath: string) => {
      const { data } = await api.post(endpoints.otherAssets.importJson, {
        json_file_path: jsonFilePath,
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['otherAssets'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: data.message || `Imported ${data.imported_count || 0} other asset(s) successfully`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import other assets from JSON',
        variant: 'destructive',
      })
    },
  })

  const handleLoad = () => {
    importJsonMutation.mutate('data/other_assets.json')
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Other Assets</h1>
          <p className="text-muted-foreground">
            Manage your other investment assets
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
          <h1 className="text-3xl font-bold tracking-tight">Other Assets</h1>
          <p className="text-muted-foreground">
            Manage your other investment assets
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading other assets</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Other Assets</h1>
          <p className="text-muted-foreground">
            Manage your other investment assets
          </p>
        </div>
        <div className="flex gap-2">
          {holdings && Array.isArray(holdings) && holdings.length > 0 && (
            <Button
              variant="outline"
              onClick={() => {
                if (confirm('Are you sure you want to delete all other assets? This action cannot be undone.')) {
                  clearAllMutation.mutate()
                }
              }}
              disabled={clearAllMutation.isPending || importJsonMutation.isPending}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className={`mr-2 h-4 w-4 ${clearAllMutation.isPending ? 'animate-spin' : ''}`} />
              Clear All
            </Button>
          )}
          <Button
            variant="outline"
            onClick={handleLoad}
            disabled={clearAllMutation.isPending || importJsonMutation.isPending}
            title="Import data from data/other_assets.json file"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${importJsonMutation.isPending ? 'animate-spin' : ''}`} />
            Load from Data Folder
          </Button>
        </div>
      </div>

      {holdings && holdings.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground">No other assets found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Click "Load from Data Folder" to load your other asset data
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {holdings?.map((asset: any) => (
            <Card key={asset.id} className="overflow-hidden">
              <CardHeader className="border-b bg-muted/30">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Briefcase className="h-5 w-5 text-muted-foreground" />
                      <CardTitle className="text-xl">
                        {asset.name || 'Other Asset'}
                      </CardTitle>
                    </div>
                    {asset.description && (
                      <CardDescription>{asset.description}</CardDescription>
                    )}
                  </div>
                  <div className="text-right">
                    {asset.current_value > 0 && (
                      <div className="text-3xl font-bold text-primary">
                        {formatCurrency(asset.current_value)}
                      </div>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  {asset.date_of_investment && (
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Investment Date
                      </div>
                      <div className="font-medium text-sm">
                        {formatDate(asset.date_of_investment)}
                      </div>
                    </div>
                  )}
                  {asset.expected_returns_date && (
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Expected Returns Date
                      </div>
                      <div className="font-medium text-sm">
                        {formatDate(asset.expected_returns_date)}
                      </div>
                    </div>
                  )}
                  {asset.lock_in_end_date && (
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Lock className="h-3 w-3" />
                        Lock-in End Date
                      </div>
                      <div className="font-medium text-sm">
                        {formatDate(asset.lock_in_end_date)}
                      </div>
                    </div>
                  )}
                  {asset.interest && (
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Percent className="h-3 w-3" />
                        Interest Rate
                      </div>
                      <div className="font-medium text-sm">{asset.interest}%</div>
                    </div>
                  )}
                </div>

                <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-900">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <div className="text-xs text-muted-foreground">Amount Invested</div>
                      <div className="text-lg font-bold mt-1">
                        {formatCurrency(asset.invested_amount || 0)}
                      </div>
                    </div>
                    {asset.returns && asset.returns > 0 && (
                      <div>
                        <div className="text-xs text-muted-foreground">Expected Returns</div>
                        <div className="text-lg font-bold text-green-600 dark:text-green-400 mt-1">
                          {formatCurrency(asset.returns)}
                        </div>
                      </div>
                    )}
                    {asset.current_value > asset.invested_amount && (
                      <div>
                        <div className="text-xs text-muted-foreground">Current Value</div>
                        <div className="text-lg font-bold text-blue-600 dark:text-blue-400 mt-1">
                          {formatCurrency(asset.current_value)}
                        </div>
                      </div>
                    )}
                    {asset.unrealized_gain_percentage !== undefined && asset.unrealized_gain_percentage !== 0 && (
                      <div>
                        <div className="text-xs text-muted-foreground">Gain %</div>
                        <div className={`text-lg font-bold mt-1 ${
                          asset.unrealized_gain_percentage >= 0 
                            ? 'text-green-600 dark:text-green-400' 
                            : 'text-red-600 dark:text-red-400'
                        }`}>
                          {asset.unrealized_gain_percentage.toFixed(2)}%
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {(asset.lock_in || asset.terms) && (
                  <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                    <div className="flex items-start gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground mt-0.5" />
                      <div className="space-y-2">
                        {asset.lock_in && (
                          <div>
                            <div className="text-xs text-muted-foreground mb-1">Lock-in Period</div>
                            <div className="text-sm font-medium">{asset.lock_in}</div>
                          </div>
                        )}
                        {asset.terms && (
                          <div>
                            <div className="text-xs text-muted-foreground mb-1">Terms</div>
                            <div className="text-sm">{asset.terms}</div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

