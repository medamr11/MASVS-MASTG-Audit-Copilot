import { useEffect, useState } from 'react'

interface ScoreGaugeProps {
  score: number
  maxScore?: number
  size?: number
  label?: string
}

export default function ScoreGauge({ score, maxScore = 10, size = 140, label = 'Overall Score' }: ScoreGaugeProps) {
  const [animatedScore, setAnimatedScore] = useState(0)
  const radius = (size - 16) / 2
  const circumference = 2 * Math.PI * radius
  const progress = animatedScore / maxScore
  const strokeDashoffset = circumference * (1 - progress)

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedScore(score), 200)
    return () => clearTimeout(timer)
  }, [score])

  const getColor = () => {
    if (score >= 7) return '#34d399' // emerald-400
    if (score >= 4) return '#fbbf24' // amber-400
    return '#fb7185' // rose-400
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="-rotate-90" width={size} height={size}>
          <circle
            className="fill-none stroke-slate-800 stroke-[6px]"
            cx={size / 2}
            cy={size / 2}
            r={radius}
          />
          <circle
            className="fill-none stroke-[6px] stroke-current transition-[stroke-dashoffset] duration-1000 ease-out stroke-linecap-round"
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={getColor()}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            style={{ filter: `drop-shadow(0 0 8px ${getColor()}40)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold" style={{ color: getColor() }}>
            {score.toFixed(1)}
          </span>
          <span className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">/ {maxScore}</span>
        </div>
      </div>
      {label && <span className="text-xs text-slate-400 font-bold uppercase tracking-widest mt-2">{label}</span>}
    </div>
  )
}
