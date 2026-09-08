import { useNavigate } from 'react-router-dom'
import { ChevronRight } from 'lucide-react'
import RiskBadge from '../common/RiskBadge'

export default function RecentCases({ cases }) {
  const navigate = useNavigate()
  return (
    <div className="panel p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-display text-sm font-semibold text-ink-100">Recent Investigations</h3>
        <button onClick={() => navigate('/cases')} className="text-xs text-accent hover:text-accent-soft">
          View all
        </button>
      </div>
      <div className="space-y-1">
        {cases.map((c) => (
          <button
            key={c.id}
            onClick={() => navigate(`/investigation/${c.id}`)}
            className="w-full flex items-center justify-between gap-3 px-3 py-3 rounded-lg hover:bg-base-800 transition-colors text-left"
          >
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-ink-100 truncate">{c.name}</span>
                <RiskBadge level={c.riskLevel} dot={false} className="!py-0" />
              </div>
              <p className="text-xs text-ink-500 mt-0.5 truncate">{c.id} · {c.entityCount} entities · updated {c.lastUpdated}</p>
            </div>
            <ChevronRight size={16} className="text-ink-500 shrink-0" />
          </button>
        ))}
      </div>
    </div>
  )
}
