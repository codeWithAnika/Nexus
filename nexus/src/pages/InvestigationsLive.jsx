import { useState } from 'react'
import { Edit3, Plus, RefreshCw, Search, Trash2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Shell from '../components/layout/Shell'
import { useActiveCase } from '../context/ActiveCaseContext'
import { createCase, deleteCase, updateCase } from '../services/casesApi'

const emptyForm = { case_number: '', title: '', description: '', status: 'OPEN', priority: 'MEDIUM', created_by: 1 }

function formatDate(value) {
  if (!value) return 'Not supplied'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function CaseModal({ record, onClose, onSaved }) {
  const [form, setForm] = useState(record ? { ...emptyForm, ...record } : emptyForm)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const isEditing = Boolean(record)
  const change = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }))

  async function submit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      if (isEditing) await updateCase(record.id, { ...form, created_by: undefined })
      else await createCase(form)
      await onSaved()
      onClose()
    } catch (requestError) {
      setError(requestError.message || 'Could not save this investigation.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={onClose}>
      <form className="panel w-full max-w-lg p-6 space-y-4" onSubmit={submit} onClick={(event) => event.stopPropagation()}>
        <div className="flex items-center justify-between"><h2 className="font-display text-lg font-semibold text-ink-100">{isEditing ? 'Edit Investigation' : 'Create Investigation'}</h2><button type="button" className="text-ink-500 hover:text-ink-100" onClick={onClose}>Close</button></div>
        {error && <div className="rounded-lg border border-risk-high/30 bg-risk-highSoft/30 px-3 py-2 text-xs text-risk-high">{error}</div>}
        <label className="block text-xs text-ink-500">Case number<input required name="case_number" value={form.case_number} onChange={change} className="mt-1 w-full bg-base-800 border border-base-border rounded-lg px-3 py-2 text-sm text-ink-100 outline-none" /></label>
        <label className="block text-xs text-ink-500">Title<input required name="title" value={form.title} onChange={change} className="mt-1 w-full bg-base-800 border border-base-border rounded-lg px-3 py-2 text-sm text-ink-100 outline-none" /></label>
        <label className="block text-xs text-ink-500">Description<textarea name="description" value={form.description || ''} onChange={change} rows="3" className="mt-1 w-full bg-base-800 border border-base-border rounded-lg px-3 py-2 text-sm text-ink-100 outline-none" /></label>
        <div className="grid grid-cols-2 gap-3"><label className="block text-xs text-ink-500">Status<select name="status" value={form.status} onChange={change} className="mt-1 w-full bg-base-800 border border-base-border rounded-lg px-3 py-2 text-sm text-ink-100 outline-none"><option value="OPEN">Open</option><option value="UNDER_INVESTIGATION">Under investigation</option><option value="CLOSED">Closed</option></select></label><label className="block text-xs text-ink-500">Priority<select name="priority" value={form.priority} onChange={change} className="mt-1 w-full bg-base-800 border border-base-border rounded-lg px-3 py-2 text-sm text-ink-100 outline-none"><option value="LOW">Low</option><option value="MEDIUM">Medium</option><option value="HIGH">High</option><option value="CRITICAL">Critical</option></select></label></div>
        <button disabled={saving} className="w-full flex items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50">{saving ? 'Saving...' : isEditing ? 'Save changes' : 'Create investigation'}</button>
      </form>
    </div>
  )
}

function statusLabel(status) { return String(status || '').replaceAll('_', ' ') || 'Unknown' }

export default function InvestigationsLive() {
  const navigate = useNavigate()
  const { cases, activeCase, selectCase, loading, error, refreshCases } = useActiveCase()
  const [query, setQuery] = useState('')
  const [modal, setModal] = useState(null)
  const [mutationError, setMutationError] = useState('')

  const visibleCases = cases.filter((item) => `${item.title} ${item.case_number} ${item.description || ''}`.toLowerCase().includes(query.toLowerCase()))
  async function removeCase(item) {
    if (!window.confirm(`Delete ${item.title}? This cannot be undone.`)) return
    setMutationError('')
    try { await deleteCase(item.id); await refreshCases() } catch (requestError) { setMutationError(requestError.message || 'Could not delete this investigation.') }
  }
  function openCase(item) { selectCase(item.id); navigate(`/network/${item.id}`) }

  return (
    <Shell title="Active Investigations" subtitle={`${cases.length} backend cases available`}>
      {(error || mutationError) && <div className="mb-4 flex items-center justify-between gap-3 rounded-lg border border-risk-high/30 bg-risk-highSoft/30 px-3 py-2 text-xs text-risk-high"><span>{mutationError || error}</span><button onClick={refreshCases} className="flex items-center gap-1 text-ink-200 hover:text-white"><RefreshCw size={13} /> Retry</button></div>}
      <div className="flex items-center justify-between gap-3 mb-5"><div className="flex items-center gap-2 bg-base-800 border border-base-border rounded-lg px-3 py-2 flex-1 max-w-xl"><Search size={15} className="text-ink-500" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search backend cases..." className="bg-transparent text-sm text-ink-100 placeholder:text-ink-500 outline-none flex-1" /></div><button onClick={() => setModal('create')} className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white"><Plus size={15} /> New investigation</button></div>
      {loading ? <div className="panel p-10 text-center text-sm text-ink-500">Loading backend cases...</div> : <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">{visibleCases.map((item) => <article key={item.id} className={`panel p-5 ${activeCase?.id === item.id ? 'border-accent/50' : ''}`}><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-mono text-accent">{item.case_number}</p><h2 className="font-display text-lg font-semibold text-ink-100 mt-1">{item.title}</h2></div><span className="text-[10px] uppercase tracking-wide text-ink-400 border border-base-border rounded px-2 py-1">{statusLabel(item.status)}</span></div><p className="text-sm text-ink-400 mt-3 min-h-10">{item.description || 'No description supplied.'}</p><div className="grid grid-cols-2 gap-3 mt-4 text-xs"><span className="text-ink-500">Priority <strong className="block text-ink-200 mt-1">{statusLabel(item.priority)}</strong></span><span className="text-ink-500">Created <strong className="block text-ink-200 mt-1">{formatDate(item.created_at)}</strong></span><span className="text-ink-500">Updated <strong className="block text-ink-200 mt-1">{formatDate(item.updated_at)}</strong></span><span className="text-ink-500">Backend ID <strong className="block text-ink-200 mt-1">{item.id}</strong></span></div><div className="flex items-center justify-end gap-2 mt-5 pt-4 border-t border-base-border"><button onClick={() => setModal(item)} className="flex items-center gap-1.5 text-xs text-ink-400 hover:text-ink-100"><Edit3 size={13} /> Edit</button><button onClick={() => removeCase(item)} className="flex items-center gap-1.5 text-xs text-risk-high hover:text-risk-high/80"><Trash2 size={13} /> Delete</button><button onClick={() => openCase(item)} className="rounded-lg bg-accent/15 border border-accent/30 px-3 py-1.5 text-xs text-accent">Open investigation</button></div></article>)}</div>}
      {!loading && visibleCases.length === 0 && <div className="panel p-10 text-center text-sm text-ink-500">No backend cases match this search.</div>}
      {modal && <CaseModal record={modal === 'create' ? null : modal} onClose={() => setModal(null)} onSaved={refreshCases} />}
    </Shell>
  )
}