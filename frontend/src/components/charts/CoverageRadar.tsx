import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts'

interface CoverageRadarProps {
  categories: {
    category: string
    score: number
    tested: number
    failed: number
    passed: number
  }[]
}

export default function CoverageRadar({ categories }: CoverageRadarProps) {
  const data = categories.map(c => ({
    category: c.category.replace('MASVS-', ''),
    score: c.score,
    fullMark: 10,
  }))

  if (data.length === 0) return null

  return (
    <div className="w-full h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="72%" data={data}>
          <PolarGrid
            stroke="#1e293b" // slate-800
            strokeDasharray="3 3"
          />
          <PolarAngleAxis
            dataKey="category"
            tick={{ fill: '#94a3b8', fontSize: 11, fontWeight: 700 }} // slate-400
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 10]}
            tick={{ fill: '#64748b', fontSize: 10 }} // slate-500
            axisLine={false}
          />
          <Radar
            name="Score"
            dataKey="score"
            stroke="#22d3ee" // cyan-400
            fill="rgba(34, 211, 238, 0.15)"
            strokeWidth={2}
            dot={{ fill: '#22d3ee', r: 3.5 }}
          />
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
            formatter={(value: any) => [`${Number(value).toFixed(1)}/10`, 'Score']}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
