import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowUpRight } from 'lucide-react'
import { entityColor } from '../../utils/entityVisuals'
import { getDataset } from '../../services/api'

// A deterministic, lightweight radial layout — decorative summary, not the
// full analytical graph (that lives in the Investigation workspace).
const RADIUS = 90
const CENTER = 110

export default function NetworkOverview() {
  const navigate = useNavigate()
  const [dataset, setDataset] = useState(null)

  useEffect(() => {
    getDataset('local').then(setDataset)
  }, [])

  if (!dataset || dataset.status !== 'ready') {
    return <div className="panel p-5 h-full flex items-center justify-center text-xs text-ink-500">Loading real network summary…</div>
  }

  const entities = dataset.entities
  const relationships = dataset.relationships
  const nodes = entities.slice(0, 14)
  const angleStep = (2 * Math.PI) / nodes.length
  const positioned = nodes.map((n, i) => ({
    ...n,
    x: CENTER + RADIUS * Math.cos(i * angleStep - Math.PI / 2),
    y: CENTER + RADIUS * Math.sin(i * angleStep - Math.PI / 2),
  }))
  const posMap = Object.fromEntries(positioned.map((n) => [n.id, n]))
  const edges = relationships.filter((r) => posMap[r.source] && posMap[r.target]).slice(0, 20)

  return (
    <div className="panel p-5 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-display text-sm font-semibold text-ink-100">Network Overview</h3>
        <button
          onClick={() => navigate('/investigation//network')}
          className="text-xs text-accent hover:text-accent-soft flex items-center gap-1"
        >
          Open workspace <ArrowUpRight size={13} />
        </button>
      </div>
      <div className="flex-1 flex items-center justify-center">
        <svg viewBox="0 0 220 220" className="w-full max-w-[240px]">
          {edges.map((e) => {
            const a = posMap[e.source]
            const b = posMap[e.target]
            return <line key={e.id} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#233047" strokeWidth={1} />
          })}
          {positioned.map((n) => (
            <circle
              key={n.id}
              cx={n.x}
              cy={n.y}
              r={n.riskLevel === 'high' ? 4.5 : 3.5}
              fill={entityColor(n.type)}
              opacity={n.riskLevel === 'high' ? 1 : 0.75}
            />
          ))}
        </svg>
      </div>
      <p className="text-xs text-ink-500 text-center">REAL DATA MODE · {entities.length} entities mapped</p>
    </div>
  )
}
