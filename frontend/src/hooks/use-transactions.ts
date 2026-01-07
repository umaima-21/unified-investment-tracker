import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import type { Transaction } from '@/types'
import { useToast } from '@/components/ui/use-toast'

export function useTransactions(assetId?: string, transactionType?: string, limit: number = 100) {
  return useQuery<Transaction[]>({
    queryKey: ['transactions', assetId, transactionType, limit],
    queryFn: async () => {
      try {
        const { data } = await api.get(endpoints.transactions.list, {
          params: {
            asset_id: assetId,
            transaction_type: transactionType,
            limit,
          },
        })
        return data || []
      } catch (err: any) {
        console.error('Error fetching transactions:', err)
        throw err
      }
    },
    retry: 1,
  })
}

export function useCreateTransaction() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (transaction: {
      asset_id: string
      transaction_type: string
      transaction_date: string
      units?: number
      price?: number
      amount: number
      description?: string
      reference_id?: string
    }) => {
      const { data } = await api.post(endpoints.transactions.create, transaction)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: 'Transaction created successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to create transaction',
        variant: 'destructive',
      })
    },
  })
}

