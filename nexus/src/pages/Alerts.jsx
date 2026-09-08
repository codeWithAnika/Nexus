import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertTriangle, AlertCircle, Clock, ArrowUpRight } from 'lucide-react'
import Shell from '../components/layout/Shell'
import { alerts as allAlerts, getEntity } from '../data/mockData'

const PRIORITY_FILTERS = ['all', 'high', 'medium', 'low']
const STATUS_FILTERS = ['all', 'active', 'resolved']

const PRIORITY_STYLE = {
  high: { icon: AlertTriangle, color: 'text-risk-high', border: 'border-risk-high/30', bg: 'bg-risk-highSoft' },
  medium: { icon: AlertCircle, color: 'text-risk-medium', border: 'border-risk-medium/30', bg: 'bg-risk-mediumSoft' },
  low: { icon: AlertCircle, color: 'text-risk-low', border: 'border-risk-low/30', bg: 'bg-risk-lowSoft' },
}

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days <= 0) return 'Today'
  if (days === 1) return '1 day ago'
  return `${days} days ago`
}

export default function Alerts() {
  const navigate = useNavigate()
  const [priority, setPriority] = useState('all')
  const [status, setStatus] = useState('all')

  const filtered = useMemo(
    () =>
      allAlerts
        .filter((a) => (priority === 'all' ? true : a.priority === priority))
        .filter((a) => (status === 'all' ? true : a.status === status))
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp)),
    [priority, status]
  )

  const counts = {
    high: allAlerts.filter((a) => a.priority === 'high' && a.status === 'active').length,
    medium: allAlerts.filter((a) => a.priority === 'medium' && a.status === 'active').length,
    low: allAlerts.filter((a) => a.priority === 'low' && a.status === 'active').length,
  }

  return (
    <Shell title="Alert Center" subtitle={`${allAlerts.filter((a) => a.status === 'active').length} active alerts across all cases`}>
      <div className="grid grid-cols-3 gap-4 mb-5">
        {['high', 'medium', 'low'].map((level) => {
          const style = PRIORITY_STYLE[level]
          const Icon = style.icon
          return (
            <div key={level} className={`panel p-4 flex items-center gap-3 ${style.border} border`}>
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${style.bg}`}>
                <Icon size={16} className={style.color} />
              </div>
              <div>
                <p className={`text-xl font-display font-semibold ${style.color}`}>{counts[level]}</p>
                <p className="text-xs text-ink-500 capitalize">{level} priority active</p>
              </div>
            </div>
          )
        })}
      </div>

      <div className="panel p-4 mb-5 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5">
          {PRIORITY_FILTERS.map((p) => (
            <button
              key={p}
              onClick={() => setPriority(p)}
              className={`px-3 py-1.5 rounded-md text-xs capitalize border transition-colors ${
                priority === p ? 'bg-accent/15 border-accent/40 text-accent' : 'border-base-border text-ink-500 hover:text-ink-100'
              }`}
            >
              {p === 'all' ? 'All priority' : p}
            </button>
          ))}
        </div>
        <div className="w-px h-5 bg-base-border" />
        <div className="flex items-center gap-1.5">
          {STATUS_FILTERS.map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={`px-3 py-1.5 rounded-md text-xs capitalize border transition-colors ${
                status === s ? 'bg-accent/15 border-accent/40 text-accent' : 'border-base-border text-ink-500 hover:text-ink-100'
              }`}
            >
              {s === 'all' ? 'All statuses' : s}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {filtered.map((a) => {
          const style = PRIORITY_STYLE[a.priority]
          const Icon = style.icon
          return (
            <div key={a.id} className="panel p-4 flex items-start gap-4">
              <div className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${style.bg}`}>
                <Icon size={16} className={style.color} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className={`text-[10px] font-semibold uppercase tracking-wide ${style.color}`}>{a.priority} priority</span>
                  <span className="text-[10px] text-ink-500 font-mono">{a.type}</span>
                  {a.status === 'resolved' && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-base-800 border border-base-border text-ink-500">
                      Resolved
                    </span>
                  )}
                </div>
                <p className="text-sm font-medium text-ink-100">{a.title}</p>
                <p className="text-xs text-ink-500 mt-1 leading-relaxed max-w-2xl">{a.description}</p>
                <div className="flex items-center gap-3 mt-2.5 flex-wrap">
                  <span className="flex items-center gap-1 text-[11px] text-ink-500">
                    <Clock size={11} /> {timeAgo(a.timestamp)}
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {a.entities.map((id) => {
                      const e = getEntity(id)
                      return (
                        <span key={id} className="text-[11px] px-1.5 py-0.5 rounded bg-base-800 border border-base-border text-ink-300">
                          {e?.name}
                        </span>
                      )
                    })}
                  </div>
                </div>
              </div>
              <button
                onClick={() => navigate(`/investigation/${a.caseId}`)}
                className="shrink-0 flex items-center gap-1 text-xs text-accent hover:text-accent-soft border border-accent/30 rounded-lg px-3 py-1.5"
              >
                View Investigation <ArrowUpRight size={12} />
              </button>
            </div>
          )
        })}
        {filtered.length === 0 && (
          <div className="panel p-10 text-center text-ink-500 text-sm">No alerts match the current filters.</div>
        )}
      </div>
    </Shell>
  )
}
