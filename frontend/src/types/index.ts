export type AssetType = 'MF' | 'STOCK' | 'CRYPTO' | 'FD'

export interface Asset {
  asset_id: string
  asset_type: AssetType
  name: string
  symbol?: string
  isin?: string
  scheme_code?: string
  exchange?: string
}

export interface Holding {
  holding_id: string
  asset_id: string
  quantity: number
  invested_amount: number
  current_value?: number
  unrealized_gain?: number
  unrealized_gain_percentage?: number
  asset?: Asset
}

export interface Transaction {
  transaction_id: string
  asset_id: string
  transaction_type: 'BUY' | 'SELL' | 'DIVIDEND' | 'INTEREST' | 'REDEMPTION'
  transaction_date: string
  units?: number
  price?: number
  amount: number
  description?: string
  reference_id?: string
  asset?: Asset
}

export interface PortfolioSummary {
  total_invested: number
  total_current_value: number
  total_returns: number
  returns_percentage: number
  asset_allocation: Record<AssetType, {
    invested: number
    current_value: number
    percentage: number
  }>
}

export interface PortfolioHistory {
  date: string
  total_value?: number
  total_current_value?: number
  total_invested: number
  returns?: number
  returns_percentage?: number
}

export interface HoldingsSummary {
  total_holdings: number
  by_type: Record<AssetType, {
    count: number
    total_invested: number
    total_current_value: number
  }>
}

