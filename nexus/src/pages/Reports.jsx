import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Printer, ShieldAlert, Users, Network as NetworkIcon, Layers } from 'lucide-react'
import Shell from '../components/layout/Shell'
import RiskBadge from '../components/common/RiskBadge'
import Timeline from '../components/investigation/Timeline'
import { ENTITY_ICONS, entityColor } from '../utils/entityVisuals'
import api from '../services/api'

export default function Reports() {
  const { caseId } = useParams()
  const [report, setReport] = useState(null)

  useEffect(() => {
    api.getReport(caseId).then(setReport)
  }, [caseId])

  if (!report) {
    return (
      <Shell title="Investigation Report" subtitle="Loading…">
        <div className="panel p-10 text-center text-ink-500 text-sm">Generating report…</div>
      </Shell>
    )
  }

  const { case: c, entities, alerts, timeline } = report
  const highRisk = entities.filter((e) => e.riskLevel === 'high').sort((a, b) => b.riskScore - a.riskScore)
  const bridgeEntity = entities.find((e) => e.tags?.includes('bridge-entity'))

  return (
    <Shell
      title="Investigation Report"
      subtitle={`${c.name} · ${c.id}`}
      right={
        <button
          onClick={() => window.print()}
          className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-accent/30 bg-accent/10 text-accent hover:bg-accent/15 transition-colors"
        >
          <Printer size={13} /> Export Report
        </button>
      }
    >
      <div className="max-w-4xl mx-auto space-y-6 pb-10">
        <div className="panel p-6">
          <p className="label-eyebrow mb-2">CASE OVERVIEW</p>
          <h2 className="font-display text-xl font-semibold text-ink-100 mb-2">{c.name}</h2>
          <p className="text-sm text-ink-300 leading-relaxed mb-4">{c.description}</p>
          <div className="flex flex-wrap items-center gap-3">
            <RiskBadge level={c.riskLevel} />
            <span className="text-xs text-ink-500">Lead investigator: {c.lead}</span>
            <span className="text-xs text-ink-500">Opened {c.opened}</span>
            <span className="text-xs text-ink-500">Updated {c.lastUpdated}</span>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Entities Mapped', value: entities.length, icon: Users },
            { label: 'Relationships', value: report.relationships.length, icon: NetworkIcon },
            { label: 'High-Risk Entities', value: highRisk.length, icon: ShieldAlert },
            { label: 'Active Alerts', value: alerts.filter((a) => a.status === 'active').length, icon: Layers },
          ].map(({ label, value, icon: Icon }) => (
            <div key={label} className="panel p-4">
              <Icon size={15} className="text-accent mb-2" />
              <p className="font-display text-xl font-semibold text-ink-100">{value}</p>
              <p className="text-xs text-ink-500">{label}</p>
            </div>
          ))}
        </div>

        {bridgeEntity && (
          <div className="panel p-6">
            <p className="label-eyebrow mb-2">KEY FINDING</p>
            <h3 className="font-display text-base font-semibold text-ink-100 mb-2">Suspicious network bridge identified</h3>
            <p className="text-sm text-ink-300 leading-relaxed">
              <span className="text-ink-100 font-medium">{bridgeEntity.name}</span> {bridgeEntity.observation.toLowerCase()}
              {' '}This pattern is a recommended focus area for further review; it is not, by itself, a finding of wrongdoing.
            </p>
          </div>
        )}

        <div className="panel p-6">
          <p className="label-eyebrow mb-3">KEY ENTITIES</p>
          <div className="space-y-1">
            {highRisk.map((e) => {
              const Icon = ENTITY_ICONS[e.type]
              return (
                <div key={e.id} className="flex items-center justify-between px-3 py-2.5 rounded-lg hover:bg-base-800">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <Icon size={15} style={{ color: entityColor(e.type) }} className="shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm text-ink-100 truncate">{e.name}</p>
                      <p className="text-xs text-ink-500">{e.role}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs font-mono text-ink-500">{e.riskScore}/100</span>
                    <RiskBadge level={e.riskLevel} />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        <div className="panel p-6">
          <p className="label-eyebrow mb-4">TIMELINE SUMMARY</p>
          <Timeline events={timeline} />
        </div>

        <div className="panel p-6">
          <p className="label-eyebrow mb-3">RECOMMENDED AREAS FOR REVIEW</p>
          <ul className="space-y-2.5">
            {alerts
              .filter((a) => a.priority === 'high')
              .map((a) => (
                <li key={a.id} className="flex gap-2.5 text-sm text-ink-300">
                  <span className="text-risk-high shrink-0">→</span>
                  {a.description}
                </li>
              ))}
          </ul>
        </div>
      </div>
    </Shell>
  )
}
