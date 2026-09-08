import { Search, RotateCcw, GitCompareArrows } from 'lucide-react'
import { ENTITY_TYPES } from '../../data/mockData'
import { ENTITY_ICONS } from '../../utils/entityVisuals'
import RiskBadge from '../common/RiskBadge'

const RISK_LEVELS = ['high', 'medium', 'low']

export default function LeftPanel({
  caseInfo,
  typeFilter,
  setTypeFilter,
  riskFilter,
  setRiskFilter,
  searchTerm,
  setSearchTerm,
  onReset,
  onOpenDiscover,
}) {
  function toggleType(type) {
    setTypeFilter((prev) => (prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]))
  }
  function toggleRisk(level) {
    setRiskFilter((prev) => (prev.includes(level) ? prev.filter((l) => l !== level) : [...prev, level]))
  }

  return (
    <div className="w-[260px] shrink-0 h-full border-r border-base-border bg-base-900 flex flex-col overflow-y-auto">
      <div className="p-4 border-b border-base-border">
        <p className="label-eyebrow mb-1">CASE</p>
        <h3 className="font-display text-sm font-semibold text-ink-100">{caseInfo.name}</h3>
        <p className="text-xs text-ink-500 mt-1">{caseInfo.id}</p>
        <div className="flex items-center gap-2 mt-2">
          <RiskBadge level={caseInfo.riskLevel} />
        </div>
      </div>

      <div className="p-4 border-b border-base-border">
        <div className="flex items-center gap-2 bg-base-800 border border-base-border rounded-lg px-2.5 py-2">
          <Search size={14} className="text-ink-500" />
          <input
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search entities…"
            className="bg-transparent text-xs text-ink-100 placeholder:text-ink-500 outline-none flex-1"
          />
        </div>
      </div>

      <div className="p-4 border-b border-base-border">
        <p className="label-eyebrow mb-2.5">ENTITY TYPE</p>
        <div className="space-y-1">
          {Object.entries(ENTITY_TYPES).map(([key, val]) => {
            const Icon = ENTITY_ICONS[key]
            const active = typeFilter.length === 0 || typeFilter.includes(key)
            return (
              <button
                key={key}
                onClick={() => toggleType(key)}
                className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-md text-xs transition-colors ${
                  active ? 'text-ink-100 bg-base-800' : 'text-ink-500'
                }`}
              >
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: val.color }} />
                <Icon size={13} />
                {val.label}
              </button>
            )
          })}
        </div>
      </div>

      <div className="p-4 border-b border-base-border">
        <p className="label-eyebrow mb-2.5">RISK LEVEL</p>
        <div className="flex flex-col gap-1.5">
          {RISK_LEVELS.map((level) => (
            <button
              key={level}
              onClick={() => toggleRisk(level)}
              className={`text-left px-2.5 py-1.5 rounded-md transition-colors ${
                riskFilter.length === 0 || riskFilter.includes(level) ? 'bg-base-800' : 'opacity-40'
              }`}
            >
              <RiskBadge level={level} />
            </button>
          ))}
        </div>
      </div>

      <div className="p-4 space-y-2">
        <p className="label-eyebrow mb-1">CONTROLS</p>
        <button
          onClick={onReset}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-base-border text-xs text-ink-300 hover:text-ink-100 hover:border-accent/40 transition-colors"
        >
          <RotateCcw size={13} />
          Reset graph
        </button>
        <button
          onClick={onOpenDiscover}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-accent/10 border border-accent/30 text-xs text-accent hover:bg-accent/15 transition-colors"
        >
          <GitCompareArrows size={13} />
          Discover connection
        </button>
      </div>
    </div>
  )
}
