import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { formatCurrency, formatDate } from '@/lib/utils'

interface PortfolioChartProps {
  data: Array<{
    date: string
    total_value?: number
    total_current_value?: number
    total_invested: number
    returns?: number
  }>
}

export function PortfolioChart({ data }: PortfolioChartProps) {
  const chartData = data.map((item) => ({
    date: formatDate(item.date),
    value: item.total_current_value || item.total_value || 0,
    invested: item.total_invested,
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}K`} />
        <Tooltip
          formatter={(value: number) => formatCurrency(value)}
          labelStyle={{ color: '#000' }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="value"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          name="Current Value"
        />
        <Line
          type="monotone"
          dataKey="invested"
          stroke="hsl(var(--muted-foreground))"
          strokeWidth={2}
          strokeDasharray="5 5"
          name="Invested"
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

