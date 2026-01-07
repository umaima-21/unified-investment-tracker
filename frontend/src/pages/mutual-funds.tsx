import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, endpoints } from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useToast } from '@/components/ui/use-toast'
import { Upload, Plus, RefreshCw, Trash2, AlertTriangle, Edit2 } from 'lucide-react'
import { formatCurrency, formatPercentage } from '@/lib/utils'
import { Skeleton } from '@/components/ui/skeleton'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'

export function MutualFundsPage() {
  const { toast } = useToast()
  const queryClient = useQueryClient()
  const [isUploadOpen, setIsUploadOpen] = useState(false)
  const [isAddOpen, setIsAddOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [password, setPassword] = useState('')
  const [deleteHoldingId, setDeleteHoldingId] = useState<string | null>(null)
  const [showDeleteAllDialog, setShowDeleteAllDialog] = useState(false)
  const [editingHolding, setEditingHolding] = useState<any>(null)
  const [editInvestedAmount, setEditInvestedAmount] = useState('')
  const [editingAsset, setEditingAsset] = useState<any>(null)
  const [editAssetName, setEditAssetName] = useState('')
  const [editPlanType, setEditPlanType] = useState('')
  const [editOptionType, setEditOptionType] = useState('')

  const { data: holdings, isLoading, error } = useQuery({
    queryKey: ['mutual-funds', 'holdings'],
    queryFn: async () => {
      try {
        const { data } = await api.get(endpoints.mutualFunds.holdings)
        console.log('MF Holdings response:', data)
        return data || []
      } catch (err: any) {
        console.error('Error fetching MF holdings:', err)
        throw err
      }
    },
    retry: 1,
  })

  const { data: searchResults } = useQuery({
    queryKey: ['mutual-funds', 'search', searchQuery],
    queryFn: async () => {
      if (searchQuery.length < 3) return { results: [] }
      const { data } = await api.get(endpoints.mutualFunds.search, {
        params: { q: searchQuery },
      })
      return data
    },
    enabled: searchQuery.length >= 3,
  })

  const uploadCasMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const { data } = await api.post(endpoints.mutualFunds.importCas, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['mutual-funds'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      setIsUploadOpen(false)
      setSelectedFile(null)
      setPassword('')
      
      const holdingsImported = data?.holdings_imported || 0
      const transactionsImported = data?.transactions_imported || 0
      
      toast({
        title: 'Success',
        description: `CAS file imported successfully: ${holdingsImported} holdings, ${transactionsImported} transactions`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import CAS file',
        variant: 'destructive',
      })
    },
  })

  const uploadCasJsonMutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const { data } = await api.post(endpoints.mutualFunds.importCasJson, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['mutual-funds'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      setIsUploadOpen(false)
      setSelectedFile(null)
      
      const mfImported = data?.mutual_funds_imported || 0
      const equitiesImported = data?.equities_imported || 0
      const etfsImported = data?.demat_mf_imported || 0
      
      toast({
        title: 'Success',
        description: `CAS JSON imported: ${mfImported} MFs, ${equitiesImported} stocks, ${etfsImported} ETFs`,
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import CAS JSON',
        variant: 'destructive',
      })
    },
  })

  const updateNavMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.mutualFunds.updateNav)
      return data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mutual-funds'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      toast({
        title: 'Success',
        description: 'NAV prices updated successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update NAV prices',
        variant: 'destructive',
      })
    },
  })

  const autoImportMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(endpoints.mutualFunds.autoImportCasJson)
      return data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['mutual-funds'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      queryClient.invalidateQueries({ queryKey: ['transactions'] })
      
      const mfCount = data?.mutual_funds_imported || 0
      const equityCount = data?.equities_imported || 0
      const etfCount = data?.demat_mf_imported || 0
      
      toast({
        title: 'Success',
        description: `Imported from data folder: ${mfCount} MFs, ${equityCount} stocks, ${etfCount} ETFs`,
      })
      
      // Update localStorage flag
      localStorage.setItem('cas_data_imported', 'true')
      localStorage.setItem('cas_import_date', new Date().toISOString())
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to import from data folder',
        variant: 'destructive',
      })
    },
  })

  const addSchemeMutation = useMutation({
    mutationFn: async (data: { scheme_code: string; units: number; invested_amount: number }) => {
      const response = await api.post(endpoints.mutualFunds.addScheme, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mutual-funds'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      setIsAddOpen(false)
      toast({
        title: 'Success',
        description: 'Scheme added successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to add scheme',
        variant: 'destructive',
      })
    },
  })

  const deleteHoldingMutation = useMutation({
    mutationFn: async (assetId: string) => {
      const response = await api.delete(`${endpoints.mutualFunds.base}/holdings/${assetId}`)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['mutual-funds'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      setDeleteHoldingId(null)
      toast({
        title: 'Success',
        description: data?.message || 'Holding deleted successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete holding',
        variant: 'destructive',
      })
    },
  })

  const deleteAllHoldingsMutation = useMutation({
    mutationFn: async () => {
      const response = await api.delete(`${endpoints.mutualFunds.base}/holdings`)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['mutual-funds'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      setShowDeleteAllDialog(false)
      toast({
        title: 'Success',
        description: data?.message || 'All holdings deleted successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to delete all holdings',
        variant: 'destructive',
      })
    },
  })

  const updateHoldingMutation = useMutation({
    mutationFn: async ({ holdingId, investedAmount }: { holdingId: string; investedAmount: number }) => {
      const response = await api.patch(`${endpoints.mutualFunds.base}/holdings/${holdingId}`, {
        invested_amount: investedAmount,
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mutual-funds'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['portfolio'] })
      setEditingHolding(null)
      setEditInvestedAmount('')
      toast({
        title: 'Success',
        description: 'Holding updated successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update holding',
        variant: 'destructive',
      })
    },
  })

  const updateAssetMutation = useMutation({
    mutationFn: async ({ assetId, name, planType, optionType }: { assetId: string; name: string; planType: string; optionType: string }) => {
      const response = await api.patch(`/api/assets/${assetId}`, {
        name,
        plan_type: planType || null,
        option_type: optionType || null,
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mutual-funds'] })
      queryClient.invalidateQueries({ queryKey: ['holdings'] })
      queryClient.invalidateQueries({ queryKey: ['assets'] })
      setEditingAsset(null)
      setEditAssetName('')
      setEditPlanType('')
      setEditOptionType('')
      toast({
        title: 'Success',
        description: 'Asset details updated successfully',
      })
    },
    onError: (error: any) => {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update asset',
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
    
    // Check file type and use appropriate endpoint
    if (selectedFile.name.toLowerCase().endsWith('.json')) {
      uploadCasJsonMutation.mutate(formData)
    } else {
      if (password) {
        formData.append('password', password)
      }
      uploadCasMutation.mutate(formData)
    }
  }

  const handleAddScheme = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const schemeCode = formData.get('scheme_code') as string
    const units = parseFloat(formData.get('units') as string)
    const investedAmount = parseFloat(formData.get('invested_amount') as string)

    addSchemeMutation.mutate({
      scheme_code: schemeCode,
      units,
      invested_amount: investedAmount,
    })
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Mutual Funds</h1>
          <p className="text-muted-foreground">
            Manage your mutual fund investments
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
          <h1 className="text-3xl font-bold tracking-tight">Mutual Funds</h1>
          <p className="text-muted-foreground">
            Manage your mutual fund investments
          </p>
        </div>
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-destructive font-medium mb-2">Error loading mutual fund holdings</p>
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
          <h1 className="text-3xl font-bold tracking-tight">Mutual Funds</h1>
          <p className="text-muted-foreground">
            Manage your mutual fund investments
          </p>
        </div>
        <div className="flex gap-2">
          {holdings && Array.isArray(holdings) && holdings.length > 0 && (
            <Button
              variant="outline"
              onClick={() => setShowDeleteAllDialog(true)}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Clear All
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => autoImportMutation.mutate()}
            disabled={autoImportMutation.isPending}
            title="Import data from data/cas_api.json file"
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${autoImportMutation.isPending ? 'animate-spin' : ''}`} />
            Load from Data Folder
          </Button>
          <Button
            variant="outline"
            onClick={() => updateNavMutation.mutate()}
            disabled={updateNavMutation.isPending}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${updateNavMutation.isPending ? 'animate-spin' : ''}`} />
            Update NAV
          </Button>
          <Dialog open={isUploadOpen} onOpenChange={setIsUploadOpen}>
            <DialogTrigger asChild>
              <Button variant="outline">
                <Upload className="mr-2 h-4 w-4" />
                Import CAS
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Import CAS File</DialogTitle>
                <DialogDescription>
                  Upload your Consolidated Account Statement (CAS) - PDF or JSON format
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="file">CAS File (PDF or JSON)</Label>
                  <Input
                    id="file"
                    type="file"
                    accept=".pdf,.json"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Select a PDF file from NSDL/CAMS or a JSON file from CAS API
                  </p>
                </div>
                {selectedFile && !selectedFile.name.toLowerCase().endsWith('.json') && (
                  <div className="space-y-2">
                    <Label htmlFor="password">Password (for PDF only)</Label>
                    <Input
                      id="password"
                      type="password"
                      placeholder="Usually email + DOB"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                    />
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setIsUploadOpen(false)}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleFileUpload} 
                  disabled={uploadCasMutation.isPending || uploadCasJsonMutation.isPending}
                >
                  {(uploadCasMutation.isPending || uploadCasJsonMutation.isPending) ? 'Uploading...' : 'Upload'}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                Add Scheme
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Mutual Fund Scheme</DialogTitle>
                <DialogDescription>
                  Manually add a mutual fund scheme
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleAddScheme} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="search">Search Scheme</Label>
                  <Input
                    id="search"
                    placeholder="Search by scheme name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  {searchResults?.results && searchResults.results.length > 0 && (
                    <div className="border rounded-md max-h-40 overflow-y-auto">
                      {searchResults.results.map((scheme: any) => (
                        <div
                          key={scheme.schemeCode}
                          className="p-2 hover:bg-accent cursor-pointer"
                          onClick={() => {
                            const form = document.querySelector('form')
                            const input = form?.querySelector('input[name="scheme_code"]') as HTMLInputElement
                            if (input) input.value = scheme.schemeCode
                            setSearchQuery(scheme.schemeName)
                          }}
                        >
                          <div className="font-medium">{scheme.schemeName}</div>
                          <div className="text-xs text-muted-foreground">{scheme.schemeCode}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="scheme_code">Scheme Code</Label>
                  <Input
                    id="scheme_code"
                    name="scheme_code"
                    placeholder="Enter scheme code"
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="units">Units</Label>
                    <Input
                      id="units"
                      name="units"
                      type="number"
                      step="0.0001"
                      placeholder="0.0000"
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="invested_amount">Invested Amount</Label>
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
                  <Button type="submit" disabled={addSchemeMutation.isPending}>
                    {addSchemeMutation.isPending ? 'Adding...' : 'Add Scheme'}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {!holdings || (Array.isArray(holdings) && holdings.length === 0) ? (
        <Card>
          <CardContent className="py-10 text-center">
            <p className="text-muted-foreground mb-4">No mutual fund holdings found</p>
            <p className="text-sm text-muted-foreground mb-4">
              Get started by uploading a CAS file or adding a scheme manually
            </p>
            <div className="flex gap-2 justify-center">
              <Button variant="outline" onClick={() => setIsUploadOpen(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Upload CAS File
              </Button>
              <Button onClick={() => setIsAddOpen(true)}>
                <Plus className="mr-2 h-4 w-4" />
                Add Scheme
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Regular Mutual Funds Section */}
          {(() => {
            const regularMFs = (Array.isArray(holdings) ? holdings : []).filter((h: any) => {
              const folio = h.folio_number || ''
              // Exclude BO IDs (16-char folios starting with IN or 12)
              // Include all other folios (regular MF folios)
              const isBoId = (folio.startsWith('IN') && folio.length === 16) || 
                             (folio.startsWith('12') && folio.length === 16)
              return !isBoId
            })
            return regularMFs.length > 0 ? (
              <div className="space-y-4">
                <div className="flex items-center gap-2">
                  <h2 className="text-2xl font-bold">Regular Mutual Funds</h2>
                  <span className="text-sm text-muted-foreground">({regularMFs.length} schemes)</span>
                </div>
                <div className="grid gap-4">
                  {regularMFs.map((holding: any) => (
                    <Card key={holding.holding_id}>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <CardTitle className="text-lg flex items-center gap-2">
                              <span>{holding.asset?.name || 'Unknown Scheme'}</span>
                              {holding.asset?.plan_type && (
                                <span className="text-sm font-normal bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
                                  {holding.asset.plan_type}
                                </span>
                              )}
                              {holding.asset?.option_type && (
                                <span className="text-sm font-normal bg-green-100 text-green-800 px-2 py-0.5 rounded">
                                  {holding.asset.option_type}
                                </span>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 text-muted-foreground hover:text-primary"
                                onClick={() => {
                                  setEditingAsset(holding.asset)
                                  setEditAssetName(holding.asset?.name || '')
                                  setEditPlanType(holding.asset?.plan_type || '')
                                  setEditOptionType(holding.asset?.option_type || '')
                                }}
                                title="Edit fund details"
                              >
                                <Edit2 className="h-3 w-3" />
                              </Button>
                            </CardTitle>
                            <CardDescription className="space-x-3">
                              {holding.asset?.amc && (
                                <span>AMC: <span className="font-semibold">{holding.asset.amc}</span></span>
                              )}
                              {holding.asset?.scheme_code && (
                                <span>Scheme: <span className="font-mono">{holding.asset.scheme_code}</span></span>
                              )}
                              {holding.asset?.isin && (
                                <span>ISIN: <span className="font-mono">{holding.asset.isin}</span></span>
                              )}
                              {holding.folio_number && (
                                <span>Folio: <span className="font-mono">{holding.folio_number}</span></span>
                              )}
                            </CardDescription>
                          </div>
                          <div className="flex items-center gap-4">
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
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => {
                                setEditingHolding(holding)
                                setEditInvestedAmount(holding.invested_amount?.toString() || '')
                              }}
                              className="text-muted-foreground hover:text-primary"
                            >
                              <Edit2 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => setDeleteHoldingId(holding.asset?.asset_id)}
                              className="text-muted-foreground hover:text-destructive"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-6 gap-4 text-sm">
                          <div>
                            <div className="text-muted-foreground">Units</div>
                            <div className="font-medium">{holding.quantity?.toLocaleString(undefined, {maximumFractionDigits: 3}) || '0'}</div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Invested Amount</div>
                            <div className="font-medium">
                              {holding.invested_amount && holding.invested_amount > 0 
                                ? formatCurrency(holding.invested_amount) 
                                : <span className="text-muted-foreground">N/A</span>}
                            </div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Current Value</div>
                            <div className="font-medium">{formatCurrency(holding.current_value || 0)}</div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Unrealized P&L</div>
                            <div
                              className={`font-medium ${
                                holding.unrealized_gain !== null && holding.unrealized_gain !== undefined
                                  ? (holding.unrealized_gain >= 0 ? 'text-green-600' : 'text-red-600')
                                  : ''
                              }`}
                            >
                              {holding.unrealized_gain !== null && holding.unrealized_gain !== undefined 
                                ? formatCurrency(holding.unrealized_gain) 
                                : <span className="text-muted-foreground">N/A</span>}
                            </div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Returns %</div>
                            <div
                              className={`font-medium ${
                                holding.unrealized_gain_percentage !== null && holding.unrealized_gain_percentage !== undefined
                                  ? (holding.unrealized_gain_percentage >= 0 ? 'text-green-600' : 'text-red-600')
                                  : ''
                              }`}
                            >
                              {holding.unrealized_gain_percentage !== null && holding.unrealized_gain_percentage !== undefined 
                                ? formatPercentage(holding.unrealized_gain_percentage) 
                                : <span className="text-muted-foreground">N/A</span>}
                            </div>
                          </div>
                          <div>
                            <div className="text-muted-foreground">Annualized Return</div>
                            <div
                              className={`font-medium ${
                                holding.annualized_return !== null && holding.annualized_return !== undefined
                                  ? (holding.annualized_return >= 0 ? 'text-green-600' : 'text-red-600')
                                  : ''
                              }`}
                            >
                              {holding.annualized_return !== null && holding.annualized_return !== undefined 
                                ? formatPercentage(holding.annualized_return) 
                                : <span className="text-muted-foreground">N/A</span>}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            ) : null
          })()}
        </>
      )}

      {/* Delete Single Holding Confirmation */}
      <AlertDialog open={!!deleteHoldingId} onOpenChange={() => setDeleteHoldingId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Holding</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this holding? This will remove all associated transactions and price data. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteHoldingId && deleteHoldingMutation.mutate(deleteHoldingId)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Delete All Holdings Confirmation */}
      <AlertDialog open={showDeleteAllDialog} onOpenChange={setShowDeleteAllDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Delete All Holdings
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete ALL mutual fund holdings? This will remove:
              <ul className="list-disc list-inside mt-2 space-y-1">
                <li>All holdings ({holdings?.length || 0} items)</li>
                <li>All transactions</li>
                <li>All price history</li>
                <li>All associated data</li>
              </ul>
              <strong className="block mt-3 text-destructive">This action cannot be undone!</strong>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteAllHoldingsMutation.mutate()}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete All
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Edit Holding Dialog */}
      <Dialog open={!!editingHolding} onOpenChange={(open) => !open && setEditingHolding(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Holding</DialogTitle>
            <DialogDescription>
              Update the invested amount for {editingHolding?.asset?.name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit_invested">Invested Amount (₹)</Label>
              <Input
                id="edit_invested"
                type="number"
                step="0.01"
                placeholder="Enter the total invested amount"
                value={editInvestedAmount}
                onChange={(e) => setEditInvestedAmount(e.target.value)}
              />
              <p className="text-sm text-muted-foreground">
                Current Value: {formatCurrency(editingHolding?.current_value || 0)}
                {' • '}Units: {editingHolding?.quantity?.toLocaleString(undefined, { maximumFractionDigits: 3 }) || '0'}
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingHolding(null)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (editingHolding && editInvestedAmount) {
                  updateHoldingMutation.mutate({
                    holdingId: editingHolding.holding_id,
                    investedAmount: parseFloat(editInvestedAmount),
                  })
                }
              }}
              disabled={updateHoldingMutation.isPending || !editInvestedAmount}
            >
              {updateHoldingMutation.isPending ? 'Saving...' : 'Save'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Asset Dialog */}
      <Dialog open={!!editingAsset} onOpenChange={(open) => !open && setEditingAsset(null)}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Edit Fund Details</DialogTitle>
            <DialogDescription>
              Update the name and classification for this mutual fund
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="edit_name">Fund Name</Label>
              <Input
                id="edit_name"
                placeholder="e.g., Invesco India Contra Fund"
                value={editAssetName}
                onChange={(e) => setEditAssetName(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Enter the complete fund name without plan type or growth/dividend
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit_plan_type">Plan Type</Label>
                <select
                  id="edit_plan_type"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  value={editPlanType}
                  onChange={(e) => setEditPlanType(e.target.value)}
                >
                  <option value="">Select Plan Type</option>
                  <option value="Direct">Direct</option>
                  <option value="Regular">Regular</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit_option_type">Option Type</Label>
                <select
                  id="edit_option_type"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  value={editOptionType}
                  onChange={(e) => setEditOptionType(e.target.value)}
                >
                  <option value="">Select Option Type</option>
                  <option value="Growth">Growth</option>
                  <option value="IDCW">IDCW (Dividend)</option>
                  <option value="Dividend">Dividend</option>
                </select>
              </div>
            </div>
            {editingAsset?.isin && (
              <p className="text-sm text-muted-foreground">
                ISIN: <span className="font-mono">{editingAsset.isin}</span>
              </p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingAsset(null)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (editingAsset && editAssetName) {
                  updateAssetMutation.mutate({
                    assetId: editingAsset.asset_id,
                    name: editAssetName,
                    planType: editPlanType,
                    optionType: editOptionType,
                  })
                }
              }}
              disabled={updateAssetMutation.isPending || !editAssetName}
            >
              {updateAssetMutation.isPending ? 'Saving...' : 'Save'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

