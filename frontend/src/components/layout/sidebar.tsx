import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Wallet, 
  TrendingUp, 
  FileText, 
  PieChart,
  Coins,
  Building2,
  Settings,
  LogOut,
  Landmark,
  CheckSquare,
  PiggyBank,
  Briefcase,
  LineChart,
  Globe
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/contexts/auth-context'
import { Button } from '@/components/ui/button'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Holdings', href: '/holdings', icon: Wallet },
  { name: 'Demat Accounts', href: '/demat-accounts', icon: Landmark },
  { name: 'Transactions', href: '/transactions', icon: FileText },
  { name: 'Mutual Funds', href: '/mutual-funds', icon: PieChart },
  { name: 'ETFs', href: '/etfs', icon: LineChart },
  { name: 'Stocks', href: '/stocks', icon: TrendingUp },
  { name: 'Crypto', href: '/crypto', icon: Coins },
  { name: 'Fixed Deposits', href: '/fixed-deposits', icon: Building2 },
  { name: 'PPF Accounts', href: '/ppf-accounts', icon: PiggyBank },
  { name: 'EPF Accounts', href: '/epf-accounts', icon: Briefcase },
  { name: 'US Stocks', href: '/us-stocks', icon: Globe },
  { name: 'Liquid', href: '/liquid', icon: Wallet },
  { name: 'Data Validation', href: '/data-validation', icon: CheckSquare },
  { name: 'Assets', href: '/assets', icon: Settings },
]

export function Sidebar() {
  const location = useLocation()
  const { logout, user } = useAuth()

  return (
    <div className="flex h-screen w-64 flex-col bg-card border-r">
      <div className="flex h-16 items-center border-b px-6">
        <h1 className="text-xl font-bold">Investment Tracker</h1>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          return (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.name}
            </Link>
          )
        })}
      </nav>
      <div className="border-t p-4">
        <div className="mb-2 px-3 text-sm text-muted-foreground">
          {user && <div className="font-medium text-foreground">{user}</div>}
        </div>
        <Button
          variant="ghost"
          className="w-full justify-start"
          onClick={logout}
        >
          <LogOut className="mr-2 h-4 w-4" />
          Logout
        </Button>
      </div>
    </div>
  )
}

