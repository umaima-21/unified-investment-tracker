import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useToast } from '@/components/ui/use-toast'
import { Heart, Calendar, User, FileText, RefreshCw } from 'lucide-react'
import { formatCurrency, formatDate } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'

export function HealthInsurancePage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  const { data: allHoldings, isLoading, error } = useQuery({
    queryKey: ['insurance', 'holdings'],
    queryFn: async () => {
      const { data } = await api.get(endpoints.insurance.holdings)
      return data
    },
  })

  // Filter for health insurance policies only
  const holdings = allHoldings?.filter((policy: any) => 
    policy.policy_type === 'Health Insurance'
  ) || []

  const importJsonMutation = useMutation({
    mutationFn: async (jsonFilePath: string) => {
      const { data } = await api.post(endpoints.insurance.importJson, {
        json_file_path: jsonFilePath,
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['insurance'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: data.message || `Imported ${data.imported_count || 0} health insurance policy/policies successfully`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import health insurance policies from JSON',
        variant: 'destructive',
      })
    },
  })

  const handleLoad = () => {
    importJsonMutation.mutate('data/health_insurance.json')
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Health Insurance</h1>
          <p className="text-muted-foreground">
            Manage your health insurance policies (payouts - not included in portfolio value)
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
          <h1 className="text-3xl font-bold tracking-tight">Health Insurance</h1>
          <p className="text-muted-foreground">
            Manage your health insurance policies (payouts - not included in portfolio value)
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading health insurance policies</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Health Insurance</h1>
          <p className="text-muted-foreground">
            Manage your health insurance policies (payouts - not included in portfolio value)
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleLoad}
            disabled={importJsonMutation.isPending}
            title="Import data from data/health_insurance.json file"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${importJsonMutation.isPending ? 'animate-spin' : ''}`} />
            Load from Data Folder
          </Button>
        </div>
      </div>

      {holdings && holdings.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground">No health insurance policies found</p>
            <p className="text-sm text-muted-foreground mt-2">
              Click "Load from Data Folder" to load your health insurance policy data
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {holdings?.map((policy: any) => (
            <Card key={policy.id} className="overflow-hidden">
              <CardHeader className="border-b bg-red-50 dark:bg-red-950/20">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Heart className="h-5 w-5 text-red-600" />
                      <CardTitle className="text-xl">
                        {policy.name || 'Health Insurance Policy'}
                      </CardTitle>
                    </div>
                    {policy.description && (
                      <CardDescription>{policy.description}</CardDescription>
                    )}
                  </div>
                  <div className="text-right">
                    {policy.sum_assured_value > 0 && (
                      <div className="text-3xl font-bold text-red-600">
                        {formatCurrency(policy.sum_assured_value)}
                      </div>
                    )}
                    <div className="flex items-center justify-end gap-2 mt-1">
                      <Badge variant="destructive">
                        Health Insurance
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  {policy.policy_number && (
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Policy Number</div>
                      <div className="font-medium text-sm">{policy.policy_number}</div>
                    </div>
                  )}
                  {policy.date_of_investment && (
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        Start Date
                      </div>
                      <div className="font-medium text-sm">
                        {formatDate(policy.date_of_investment)}
                      </div>
                    </div>
                  )}
                  {policy.date_of_maturity && (
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        End Date
                      </div>
                      <div className="font-medium text-sm">
                        {formatDate(policy.date_of_maturity)}
                      </div>
                    </div>
                  )}
                  {policy.duration_years && (
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground">Duration</div>
                      <div className="font-medium text-sm">{policy.duration_years} {policy.duration_years === 1 ? 'year' : 'years'}</div>
                    </div>
                  )}
                  {policy.nominee && (
                    <div className="space-y-1">
                      <div className="text-xs text-muted-foreground flex items-center gap-1">
                        <User className="h-3 w-3" />
                        Nominee
                      </div>
                      <div className="font-medium text-sm">{policy.nominee}</div>
                    </div>
                  )}
                </div>

                <div className="mt-4 p-4 bg-red-50 dark:bg-red-950/20 rounded-lg border border-red-200 dark:border-red-900">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-xs text-muted-foreground">Premium Paid</div>
                      <div className="text-lg font-bold mt-1">
                        {formatCurrency(policy.invested_amount || 0)}
                      </div>
                    </div>
                    {policy.sum_assured_value > 0 && (
                      <div>
                        <div className="text-xs text-muted-foreground">Sum Insured</div>
                        <div className="text-lg font-bold text-red-600 dark:text-red-400 mt-1">
                          {formatCurrency(policy.sum_assured_value)}
                        </div>
                      </div>
                    )}
                    {policy.annual_premium > 0 && (
                      <div>
                        <div className="text-xs text-muted-foreground">Annual Premium</div>
                        <div className="text-lg font-bold text-blue-600 dark:text-blue-400 mt-1">
                          {formatCurrency(policy.annual_premium)}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="mt-3 pt-3 border-t border-red-200 dark:border-red-800 text-center">
                    <p className="text-xs text-muted-foreground">
                      Note: Health insurance policies are payouts and are not included in portfolio Current Value calculation
                    </p>
                  </div>
                </div>

                {policy.comments && (
                  <div className="mt-4 p-3 bg-muted/50 rounded-lg">
                    <div className="flex items-start gap-2">
                      <FileText className="h-4 w-4 text-muted-foreground mt-0.5" />
                      <div>
                        <div className="text-xs text-muted-foreground mb-1">Policy Details</div>
                        <div className="text-sm">{policy.comments}</div>
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

