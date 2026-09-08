import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, ArrowUpDown, ChevronRight } from 'lucide-react'
import Shell from '../components/layout/Shell'
import RiskBadge from '../components/common/RiskBadge'
import { cases } from '../data/mockData'

const RISK_FILTERS = ['all', 'high', 'medium', 'low']
const STATUS_FILTERS = ['all', 'Active', 'Under Review', 'Closed']
const SORT_OPTIONS = [
  { key: 'lastUpdated', label: 'Last Updated' },
  { key: 'entityCount', label: 'Entity Count' },
  { key: 'alertCount', label: 'Alert Count' },
]

export default function Cases() {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sortKey, setSortKey] = useState('lastUpdated')

  const filtered = useMemo(() => {
    return cases
      .filter((c) => (riskFilter === 'all' ? true : c.riskLevel === riskFilter))
      .filter((c) => (statusFilter === 'all' ? true : c.status === statusFilter))
      .filter((c) =>
        query.trim() === ''
          ? true
          : `${c.name} ${c.id} ${c.description}`.toLowerCase().includes(query.toLowerCase())
      )
      .sort((a, b) => (a[sortKey] > b[sortKey] ? -1 : 1))
  }, [query, riskFilter, statusFilter, sortKey])

  return (
    <Shell title="Case Management" subtitle={`${cases.length} investigations on file`}>
      <div className="panel p-4 mb-5 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 bg-base-800 border border-base-border rounded-lg px-3 py-2 flex-1 min-w-[220px]">
          <Search size={15} className="text-ink-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by case name, ID, or description…"
            className="bg-transparent text-sm text-ink-100 placeholder:text-ink-500 outline-none flex-1"
          />
        </div>

        <div className="flex items-center gap-1.5">
          {RISK_FILTERS.map((r) => (
            <button
              key={r}
              onClick={() => setRiskFilter(r)}
              className={`px-3 py-1.5 rounded-md text-xs capitalize border transition-colors ${
                riskFilter === r
                  ? 'bg-accent/15 border-accent/40 text-accent'
                  : 'border-base-border text-ink-500 hover:text-ink-100'
              }`}
            >
              {r === 'all' ? 'All risk' : r}
            </button>
          ))}
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-base-800 border border-base-border rounded-md text-xs text-ink-300 px-2.5 py-2 outline-none"
        >
          {STATUS_FILTERS.map((s) => (
            <option key={s} value={s}>
              {s === 'all' ? 'All statuses' : s}
            </option>
          ))}
        </select>

        <div className="flex items-center gap-1.5 text-xs text-ink-500">
          <ArrowUpDown size={13} />
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value)}
            className="bg-base-800 border border-base-border rounded-md text-xs text-ink-300 px-2 py-1.5 outline-none"
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.key} value={o.key}>
                Sort: {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="panel overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-ink-500 text-xs border-b border-base-border">
              <th className="px-5 py-3 font-medium">Case</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Risk</th>
              <th className="px-5 py-3 font-medium">Entities</th>
              <th className="px-5 py-3 font-medium">Alerts</th>
              <th className="px-5 py-3 font-medium">Updated</th>
              <th className="px-5 py-3" />
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr
                key={c.id}
                onClick={() => navigate(`/investigation/${c.id}`)}
                className="border-b border-base-border last:border-0 hover:bg-base-800 cursor-pointer transition-colors"
              >
                <td className="px-5 py-4">
                  <div className="font-medium text-ink-100">{c.name}</div>
                  <div className="text-xs text-ink-500 mt-0.5">{c.id}</div>
                </td>
                <td className="px-5 py-4">
                  <span
                    className={`text-xs px-2 py-1 rounded-md border ${
                      c.status === 'Active'
                        ? 'text-accent border-accent/30 bg-accent/10'
                        : c.status === 'Closed'
                        ? 'text-ink-500 border-base-border bg-base-800'
                        : 'text-risk-medium border-risk-medium/30 bg-risk-mediumSoft'
                    }`}
                  >
                    {c.status}
                  </span>
                </td>
                <td className="px-5 py-4">
                  <RiskBadge level={c.riskLevel} />
                </td>
                <td className="px-5 py-4 text-ink-300">{c.entityCount}</td>
                <td className="px-5 py-4 text-ink-300">{c.alertCount}</td>
                <td className="px-5 py-4 text-ink-500 text-xs font-mono">{c.lastUpdated}</td>
                <td className="px-5 py-4">
                  <ChevronRight size={16} className="text-ink-500" />
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-5 py-12 text-center text-ink-500 text-sm">
                  No cases match the current filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Shell>
  )
}
