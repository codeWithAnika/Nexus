import { useEffect, useState } from 'react'
import { AlertTriangle, Database, Radar, RefreshCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Shell from '../components/layout/Shell'
import StatsCards from '../components/dashboard/StatsCards'
import AlertsFeed from '../components/dashboard/AlertsFeed'
import { useActiveCase } from '../context/ActiveCaseContext'
import { getFirs } from '../services/firsApi'
import { getEntities } from '../services/entitiesApi'
import { getRelationships } from '../services/relationshipsApi'
import { getAlerts } from '../services/alertsApi'

function totalOf(response) { return Number(response?.total ?? (Array.isArray(response) ? response.length : 0)) }

export default function DashboardLive() {
  const navigate = useNavigate()
  const { activeCase } = useActiveCase()
  const [data, setData] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  async function load() {
    if (!activeCase) return
    setLoading(true)
    const results = await Promise.allSettled([
      getFirs(activeCase.id, { limit: 1 }),
      getEntities(activeCase.id, { limit: 1 }),
      getRelationships({ case_id: activeCase.id, limit: 1 }),
      getAlerts(activeCase.id, { limit: 1 }),
    ])
    const values = results.map((result) => result.status === 'fulfilled' ? result.value : null)
    const succeeded = values.filter(Boolean).length
    setData({ totalRecords: totalOf(values[0]), totalEntities: totalOf(values[1]), totalRelationships: totalOf(values[2]), activeAlerts: totalOf(values[3]), activeCases: 1, personsIdentified: '—', locationsIdentified: '—', crimeTypesIdentified: '—', evidenceSources: totalOf(values[0]), highRiskEntities: '—' })
    setAlerts(Array.isArray(values[3]) ? values[3] : values[3]?.items || [])
    setError(succeeded === 4 ? '' : succeeded ? 'Some live dashboard totals are unavailable.' : 'Backend dashboard data is unavailable.')
    setLoading(false)
  }

  useEffect(() => { load() }, [activeCase?.id])
  if (!activeCase) return <Shell title="Command Center" subtitle="Waiting for an active backend case"><div className="panel p-10 text-center text-sm text-ink-500">Loading active case...</div></Shell>

  return <Shell title="Command Center" subtitle={`${activeCase.title} · ${activeCase.case_number}`}>
    {error && <div className="mb-5 flex items-center justify-between rounded-lg border border-risk-medium/30 bg-risk-mediumSoft/20 px-3 py-2 text-xs text-risk-medium"><span>{error}</span><button onClick={load} className="flex items-center gap-1 text-ink-200"><RefreshCw size={13} /> Retry</button></div>}
    <div className="flex items-center justify-between mb-5"><div><p className="label-eyebrow">LIVE CASE OVERVIEW</p><h2 className="font-display text-xl font-semibold text-ink-100 mt-1">{activeCase.title}</h2></div><span className="text-[10px] font-mono uppercase tracking-wide px-2 py-1 rounded border border-risk-low/30 bg-risk-lowSoft text-risk-low">{loading ? 'LOADING DATA' : error ? 'PARTIAL DATA' : 'LIVE DATA'}</span></div>
    <StatsCards stats={data} />
    <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 mt-6"><div className="xl:col-span-2 panel p-5"><div className="flex items-center gap-2 mb-4"><Database size={15} className="text-accent" /><h3 className="font-display text-sm font-semibold text-ink-100">Backend data integration</h3></div><p className="text-sm text-ink-400 leading-relaxed">Live totals are scoped to the selected case. Graph analytics and risk scores are shown on the Network Intelligence page after the deterministic pipeline completes.</p><button onClick={() => navigate(`/network/${activeCase.id}`)} className="mt-5 flex items-center gap-2 rounded-lg bg-accent/15 border border-accent/30 px-3 py-2 text-xs text-accent"><Radar size={14} /> Open live network</button></div><div><AlertsFeed alerts={alerts} /><div className="mt-3 text-[10px] text-ink-500 flex items-center gap-1"><AlertTriangle size={11} /> Live alert data only</div></div></div>
  </Shell>
}
