import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { formatCurrency } from '@/lib/utils'

interface AllocationChartProps {
  data: Record<string, {
    invested: number
    current_value: number
    percentage: number
  }>
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#6366f1', '#14b8a6']

export function AllocationChart({ data }: AllocationChartProps) {
  const chartData = Object.entries(data).map(([name, value]) => ({
    name,
    value: value.current_value,
    percentage: value.percentage,
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
          outerRadius={100}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value: number) => formatCurrency(value)} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}

