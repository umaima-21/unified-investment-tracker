import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider, useAuth } from '@/contexts/auth-context'
import { MainLayout } from '@/components/layout/main-layout'
import { ProtectedRoute } from '@/components/protected-route'
import { ErrorBoundary } from '@/components/error-boundary'
import { Toaster } from '@/components/ui/toaster'
import { LoginPage } from '@/pages/login'
import { DashboardPage } from '@/pages/dashboard'
import { HoldingsPage } from '@/pages/holdings'
import { TransactionsPage } from '@/pages/transactions'
import { MutualFundsPage } from '@/pages/mutual-funds'
import { ETFsPage } from '@/pages/etfs'
import { StocksPage } from '@/pages/stocks'
import { CryptoPage } from '@/pages/crypto'
import { FixedDepositsPage } from '@/pages/fixed-deposits'
import { PPFAccountsPage } from '@/pages/ppf-accounts'
import { EPFAccountsPage } from '@/pages/epf-accounts'
import { USStocksPage } from '@/pages/us-stocks'
import { UnlistedSharesPage } from '@/pages/unlisted-shares'
import { LiquidPage } from '@/pages/liquid'
import { InsurancePage } from '@/pages/insurance'
import { HealthInsurancePage } from '@/pages/health-insurance'
import { OtherAssetsPage } from '@/pages/other-assets'
import { AssetsPage } from '@/pages/assets'
import { DematAccountsPage } from '@/pages/demat-accounts'
import { DataValidationPage } from '@/pages/data-validation'
import { useEffect } from 'react'
import { api, endpoints } from '@/lib/api'
import { useToast } from '@/components/ui/use-toast'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function AppRoutes() {
  const { isAuthenticated } = useAuth()
  const { toast } = useToast()

  // Auto-import CAS JSON data on app load
  useEffect(() => {
    const autoImportData = async () => {
      if (!isAuthenticated) return

      try {
        // Check if we've already imported (using localStorage flag)
        const hasImported = localStorage.getItem('cas_data_imported')
        
        if (hasImported) {
          console.log('CAS data already imported, skipping auto-import')
          return
        }

        console.log('Auto-importing CAS data from data folder...')
        
        const { data } = await api.post(endpoints.mutualFunds.autoImportCasJson)
        
          if (data.success) {
            const mfCount = data.mutual_funds_imported || 0
            const equityCount = data.equities_imported || 0
            const etfCount = data.demat_mf_imported || 0
            const unlistedCount = data.unlisted_shares_imported || 0
            const totalCount = mfCount + equityCount + etfCount + unlistedCount
            
            if (totalCount > 0) {
              const parts = []
              if (mfCount > 0) parts.push(`${mfCount} mutual funds`)
              if (equityCount > 0) parts.push(`${equityCount} stocks`)
              if (etfCount > 0) parts.push(`${etfCount} ETFs`)
              if (unlistedCount > 0) parts.push(`${unlistedCount} unlisted shares`)
              
              toast({
                title: 'Portfolio Data Loaded',
                description: `Successfully imported: ${parts.join(', ')}`,
              })
            
            // Mark as imported
            localStorage.setItem('cas_data_imported', 'true')
            localStorage.setItem('cas_import_date', new Date().toISOString())
          } else {
            console.log('No CAS data file found or already imported')
          }
        } else if (data.message && !data.message.includes('No CAS JSON file found')) {
          console.warn('Auto-import result:', data.message)
        }
      } catch (error: any) {
        console.error('Auto-import failed:', error)
        // Don't show error toast for auto-import failures to avoid annoying users
      }
    }

    autoImportData()
    
    // Auto-import insurance JSON data on app load
    const autoImportInsurance = async () => {
      if (!isAuthenticated) return

      try {
        // Check if we've already imported (using localStorage flag)
        const hasImported = localStorage.getItem('insurance_data_imported')
        
        if (hasImported) {
          console.log('Insurance data already imported, skipping auto-import')
          return
        }

        console.log('Auto-importing insurance data from data folder...')
        
        const { data } = await api.post(endpoints.insurance.autoImportJson)
        
        if (data.success && data.policies_imported > 0) {
          toast({
            title: 'Insurance Data Loaded',
            description: `Successfully imported ${data.policies_imported} insurance policy/policies (including health insurance)`,
          })
        
          // Mark as imported
          localStorage.setItem('insurance_data_imported', 'true')
          localStorage.setItem('insurance_import_date', new Date().toISOString())
        } else {
          console.log('No insurance data file found or already imported')
        }
      } catch (error: any) {
        console.error('Auto-import insurance failed:', error)
        // Don't show error toast for auto-import failures to avoid annoying users
      }
    }

    autoImportInsurance()
    
    // Auto-import other assets JSON data on app load
    const autoImportOtherAssets = async () => {
      if (!isAuthenticated) return

      try {
        // Check if we've already imported (using localStorage flag)
        const hasImported = localStorage.getItem('other_assets_data_imported')
        
        if (hasImported) {
          console.log('Other assets data already imported, skipping auto-import')
          return
        }

        console.log('Auto-importing other assets data from data folder...')
        
        const { data } = await api.post(endpoints.otherAssets.autoImportJson)
        
        if (data.success && data.assets_imported > 0) {
          toast({
            title: 'Other Assets Data Loaded',
            description: `Successfully imported ${data.assets_imported} other asset(s)`,
          })
        
          // Mark as imported
          localStorage.setItem('other_assets_data_imported', 'true')
          localStorage.setItem('other_assets_import_date', new Date().toISOString())
        } else {
          console.log('No other assets data file found or already imported')
        }
      } catch (error: any) {
        console.error('Auto-import other assets failed:', error)
        // Don't show error toast for auto-import failures to avoid annoying users
      }
    }

    autoImportOtherAssets()
  }, [isAuthenticated, toast])

  return (
    <Routes>
      <Route path="/login" element={isAuthenticated ? <Navigate to="/" replace /> : <LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <DashboardPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/holdings"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <HoldingsPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/transactions"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <TransactionsPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/mutual-funds"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <MutualFundsPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/etfs"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <ETFsPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/stocks"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <StocksPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/crypto"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <CryptoPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/fixed-deposits"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <FixedDepositsPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/ppf-accounts"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <PPFAccountsPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/epf-accounts"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <EPFAccountsPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/us-stocks"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <USStocksPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/unlisted-shares"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <UnlistedSharesPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/liquid"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <LiquidPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/insurance"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <InsurancePage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/health-insurance"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <HealthInsurancePage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/other-assets"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <OtherAssetsPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/assets"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <AssetsPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/demat-accounts"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <DematAccountsPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route
        path="/data-validation"
        element={
          <ProtectedRoute>
            <ErrorBoundary>
              <MainLayout>
                <DataValidationPage />
              </MainLayout>
            </ErrorBoundary>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <BrowserRouter>
            <AppRoutes />
            <Toaster />
          </BrowserRouter>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App

