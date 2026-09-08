import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Check, RefreshCw } from 'lucide-react'
import Shell from '../components/layout/Shell'
import { useActiveCase } from '../context/ActiveCaseContext'
import { getAlerts, updateAlertStatus } from '../services/alertsApi'

const statuses = ['OPEN', 'ACKNOWLEDGED', 'RESOLVED']
function itemsOf(response) { return Array.isArray(response) ? response : response?.items || [] }
function tone(severity) { return String(severity || 'LOW').toLowerCase() }

export default function AlertsLive() {
  const { activeCase } = useActiveCase()
  const [alerts, setAlerts] = useState([])
  const [filter, setFilter] = useState('ALL')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function load() { if (!activeCase) return; setLoading(true); try { setAlerts(itemsOf(await getAlerts(activeCase.id, { limit: 100 }))); setError('') } catch (requestError) { setError(requestError.message || 'Unable to load alerts.') } finally { setLoading(false) } }
  useEffect(() => { load() }, [activeCase?.id])
  async function changeStatus(alert, status) { const previous = alerts; setAlerts((current) => current.map((item) => item.id === alert.id ? { ...item, status } : item)); try { await updateAlertStatus(alert.id, status) } catch (requestError) { setAlerts(previous); setError(requestError.message || 'Alert update failed and was rolled back.') } }
  const filtered = useMemo(() => filter === 'ALL' ? alerts : alerts.filter((alert) => alert.status === filter), [alerts, filter])
  return <Shell title="Alert Center" subtitle={`${activeCase?.title || 'Selected case'} · live operational signals`}>
    {error && <div className="mb-4 flex items-center justify-between rounded-lg border border-risk-high/30 bg-risk-highSoft/20 px-3 py-2 text-xs text-risk-high"><span>{error}</span><button onClick={load}><RefreshCw size={13} /></button></div>}
    <div className="panel p-4 mb-5 flex items-center justify-between gap-3"><div className="flex gap-2">{['ALL', ...statuses].map((status) => <button key={status} onClick={() => setFilter(status)} className={`px-3 py-1.5 rounded-md text-xs border ${filter === status ? 'bg-accent/15 border-accent/40 text-accent' : 'border-base-border text-ink-500'}`}>{status === 'ALL' ? 'All statuses' : status}</button>)}</div><span className="text-xs text-ink-500">{alerts.filter((alert) => alert.status !== 'RESOLVED').length} open signals</span></div>
    {loading ? <div className="panel p-10 text-center text-sm text-ink-500">Loading live alerts...</div> : <div className="space-y-3">{filtered.map((alert) => <div key={alert.id} className="panel p-4 flex items-start gap-4"><div className={`w-9 h-9 rounded-lg flex items-center justify-center bg-risk-${tone(alert.severity)}Soft`}><AlertTriangle size={16} className={`text-risk-${tone(alert.severity)}`} /></div><div className="flex-1 min-w-0"><div className="flex items-center gap-2"><strong className="text-sm text-ink-100">{alert.title}</strong><span className={`text-[10px] uppercase text-risk-${tone(alert.severity)}`}>{alert.severity}</span></div><p className="text-xs text-ink-500 mt-1">{alert.description || 'No description supplied.'}</p><span className="text-[10px] text-ink-500 font-mono">{alert.alert_type} · {alert.status}</span></div><div className="flex gap-2 shrink-0">{statuses.filter((status) => status !== alert.status).map((status) => <button key={status} onClick={() => changeStatus(alert, status)} className="text-[10px] border border-base-border rounded px-2 py-1 text-ink-400 hover:text-ink-100">{status}</button>)}{alert.status === 'RESOLVED' && <Check size={15} className="text-risk-low" />}</div></div>)}</div>}
  </Shell>
}
