import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#f43f5e', // rose-500
  high: '#f59e0b', // amber-500
  medium: '#fbbf24', // amber-400
  low: '#10b981', // emerald-500
  info: '#3b82f6', // blue-500
}

interface SeverityDonutProps {
  findings: { severity: string }[]
}

export default function SeverityDonut({ findings }: SeverityDonutProps) {
  const counts = findings.reduce((acc, f) => {
    acc[f.severity] = (acc[f.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const data = Object.entries(counts)
    .filter(([_, v]) => v > 0)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => {
      const order = ['critical', 'high', 'medium', 'low', 'info']
      return order.indexOf(a.name) - order.indexOf(b.name)
    })

  if (data.length === 0) return null

  return (
    <div className="flex items-center gap-6">
      <div className="w-[140px] h-[140px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={42}
              outerRadius={65}
              paddingAngle={3}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry) => (
                <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] || '#666'} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: '#020617', // slate-950
                border: '1px solid #1e293b', // slate-800
                borderRadius: '12px',
                fontSize: '12px',
                fontWeight: 'bold',
                color: '#f8fafc', // slate-50
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
              }}
              formatter={(value: any, name: any) => [value, String(name).toUpperCase()]}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="space-y-1.5">
        {data.map(({ name, value }) => (
          <div key={name} className="flex items-center gap-2.5 text-sm">
            <div
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: SEVERITY_COLORS[name] }}
            />
            <span className="text-slate-400 capitalize w-16 font-medium">{name}</span>
            <span className="font-bold text-slate-200">{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
