import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, FileText, Network, X } from 'lucide-react'
import { ENTITY_ICONS, entityColor, entityLabel } from '../../utils/entityVisuals'
import RiskBadge from '../common/RiskBadge'
import { RELATIONSHIP_TYPES } from '../../data/mockData'

function riskInsights(entity) {
  const insights = []
  if (entity.connections >= 6) insights.push('Connected to an unusually high number of distinct entities.')
  if (entity.tags?.includes('bridge-entity')) insights.push('Acts as a bridge between two otherwise separate network communities.')
  if (entity.tags?.includes('structuring-pattern')) insights.push('Receives deposits structured to stay below reporting thresholds.')
  if (entity.tags?.includes('shell-indicators')) insights.push('Shows minimal operational footprint relative to declared transaction volume.')
  if (entity.tags?.includes('rapid-movement')) insights.push('Funds moved onward shortly after arrival, a pattern consistent with layering.')
  if (entity.tags?.includes('unregistered')) insights.push('No KYC or registration record found for this identifier.')
  if (entity.riskLevel === 'high' && insights.length === 0) insights.push('Multiple weak signals combine to place this entity in the high-risk band.')
  if (insights.length === 0) insights.push('No strong risk indicators identified; retained for network context.')
  return insights
}

export default function EntityPanel({ entity, onClose, onSelectRelated }) {
  return (
    <AnimatePresence mode="wait">
      {entity ? (
        <motion.div
          key={entity.id}
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 12 }}
          transition={{ duration: 0.2 }}
          className="w-[320px] shrink-0 h-full border-l border-base-border bg-base-900 overflow-y-auto"
        >
          <div className="p-4 border-b border-base-border flex items-start justify-between">
            <div>
              <p className="label-eyebrow mb-1">ENTITY PROFILE</p>
              <h3 className="font-display text-base font-semibold text-ink-100">{entity.name}</h3>
              <p className="text-xs text-ink-500 mt-0.5">{entity.role}</p>
            </div>
            <button onClick={onClose} className="text-ink-500 hover:text-ink-100">
              <X size={16} />
            </button>
          </div>

          <div className="p-4 border-b border-base-border grid grid-cols-2 gap-3">
            <div>
              <p className="text-[10px] text-ink-500 font-mono mb-1">TYPE</p>
              <div className="flex items-center gap-1.5 text-sm text-ink-100">
                {(() => {
                  const Icon = ENTITY_ICONS[entity.type]
                  return <Icon size={14} style={{ color: entityColor(entity.type) }} />
                })()}
                {entityLabel(entity.type)}
              </div>
            </div>
            <div>
              <p className="text-[10px] text-ink-500 font-mono mb-1">RISK SCORE</p>
              <div className="text-sm text-ink-100 font-mono">{entity.riskScore}/100</div>
            </div>
            <div className="col-span-2">
              <RiskBadge level={entity.riskLevel} />
            </div>
          </div>

          <div className="p-4 border-b border-base-border">
            <p className="label-eyebrow mb-2 flex items-center gap-1.5">
              <Network size={12} /> RELATIONSHIPS ({entity.relationships?.length ?? entity.connections})
            </p>
            <div className="space-y-1.5">
              {(entity.connected || []).map((c) => (
                <button
                  key={c.id}
                  onClick={() => onSelectRelated(c.id)}
                  className="w-full flex items-center justify-between px-2.5 py-2 rounded-md hover:bg-base-800 transition-colors text-left"
                >
                  <span className="flex items-center gap-2 text-xs text-ink-100 min-w-0">
                    <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: entityColor(c.type) }} />
                    <span className="truncate">{c.name}</span>
                  </span>
                  <RiskBadge level={c.riskLevel} dot={false} className="!py-0 !px-1.5 shrink-0" />
                </button>
              ))}
            </div>
          </div>

          <div className="p-4 border-b border-base-border">
            <p className="label-eyebrow mb-2">KEY OBSERVATION</p>
            <p className="text-sm text-ink-300 leading-relaxed">{entity.observation}</p>
          </div>

          <div className="p-4 border-b border-base-border">
            <p className="label-eyebrow mb-2 flex items-center gap-1.5">
              <Sparkles size={12} className="text-accent" /> AI INTELLIGENCE INSIGHT
            </p>
            <div className="rounded-lg bg-accent/5 border border-accent/20 p-3">
              <p className="text-xs text-ink-500 mb-2">Why was this flagged?</p>
              <ul className="space-y-1.5">
                {riskInsights(entity).map((insight, i) => (
                  <li key={i} className="text-xs text-ink-100 flex gap-2 leading-relaxed">
                    <span className="text-accent shrink-0">✓</span>
                    {insight}
                  </li>
                ))}
              </ul>
              <p className="text-[11px] text-ink-500 mt-3 italic">
                These indicators suggest a pattern that warrants further investigation. They are not a determination of guilt.
              </p>
            </div>
          </div>

          <div className="p-4">
            <p className="label-eyebrow mb-2 flex items-center gap-1.5">
              <FileText size={12} /> SUPPORTING EVIDENCE
            </p>
            <div className="flex flex-wrap gap-1.5">
              {entity.evidence?.map((e) => (
                <span key={e} className="text-[11px] font-mono px-2 py-1 rounded-md bg-base-800 border border-base-border text-ink-300">
                  {e}
                </span>
              ))}
            </div>
          </div>
        </motion.div>
      ) : (
        <div className="w-[320px] shrink-0 h-full border-l border-base-border bg-base-900 flex flex-col items-center justify-center text-center px-8">
          <Network size={28} className="text-ink-500 mb-3" />
          <p className="text-sm text-ink-300 font-medium mb-1">No entity selected</p>
          <p className="text-xs text-ink-500">Click any node in the network graph to view its profile, risk score, and relationships.</p>
        </div>
      )}
    </AnimatePresence>
  )
}

RELATIONSHIP_TYPES // referenced for future relationship-label rendering
