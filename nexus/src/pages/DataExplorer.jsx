import { useEffect, useMemo, useState } from 'react'
import { Database, FileText, Search, ShieldAlert, X } from 'lucide-react'
import Shell from '../components/layout/Shell'
import { entityLabel, entityColor } from '../utils/entityVisuals'
import { DATA_SOURCES, getDataset, setDataSource } from '../services/api'

function StatePanel({ title, detail, tone = 'neutral' }) {
  const color = tone === 'error' ? 'text-risk-high' : tone === 'warning' ? 'text-risk-medium' : 'text-ink-500'
  return (
    <div className="panel p-10 text-center">
      <Database size={28} className={`${color} mx-auto mb-3`} />
      <h2 className="font-display text-base font-semibold text-ink-100">{title}</h2>
      <p className="text-sm text-ink-500 mt-2 max-w-lg mx-auto">{detail}</p>
    </div>
  )
}

export default function DataExplorer() {
  const [dataset, setDataset] = useState(null)
  const [query, setQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [selectedEntity, setSelectedEntity] = useState(null)
  const [mode, setMode] = useState(DATA_SOURCES.local)

  useEffect(() => {
    getDataset(mode).then(setDataset)
  }, [mode])

  function changeMode(nextMode) {
    setDataSource(nextMode)
    setMode(nextMode)
    setSelectedEntity(null)
  }

  const filteredEntities = useMemo(() => {
    if (!dataset || !dataset.entities) return []
    const normalizedQuery = query.trim().toLowerCase()
    return dataset.entities.filter((entity) => {
      const matchesQuery = !normalizedQuery || `${entity.name} ${entity.id} ${entity.metadata.recordId}`.toLowerCase().includes(normalizedQuery)
      const matchesType = typeFilter === 'all' || entity.type === typeFilter
      const sources = entity.sourceRecords.map((record) => record.source).filter(Boolean)
      const matchesSource = sourceFilter === 'all' || sources.includes(sourceFilter)
      return matchesQuery && matchesType && matchesSource
    })
  }, [dataset, query, typeFilter, sourceFilter])

  const sources = dataset && dataset.records ? dataset.records.map((record) => record.source).filter(Boolean) : []
  const uniqueSources = [...new Set(sources)]

  if (!dataset) {
    return <Shell title="Data Explorer" subtitle="REAL DATA MODE · loading processed evidence"><StatePanel title="Loading processed dataset" detail="Reading the local evidence-processing output and preparing the normalized intelligence model." /></Shell>
  }

  if (dataset.status === 'invalid') {
    return <Shell title="Data Explorer" subtitle="REAL DATA MODE"><StatePanel title="Dataset unavailable" detail={dataset.error || 'The processed dataset could not be loaded.'} tone="error" /></Shell>
  }

  if (dataset.status === 'empty') {
    return <Shell title="Data Explorer" subtitle="REAL DATA MODE"><StatePanel title="No processed records" detail="The local processed dataset is valid but contains no records yet." tone="warning" /></Shell>
  }

  return (
    <Shell title="Data Explorer" subtitle={`${mode === DATA_SOURCES.mock ? 'DEMO MODE · fictional Operation Nexus' : 'REAL DATA MODE · local processed output'}${dataset.metadata?.recordCount ? ` · ${dataset.metadata.recordCount} processed records` : ''}`}>
      <div className="space-y-5">
        <div className="flex items-center gap-1 bg-base-800 border border-base-border rounded-lg p-1 w-fit">
          {[['local', 'REAL DATA MODE'], ['mock', 'DEMO MODE']].map(([value, label]) => (
            <button key={value} onClick={() => changeMode(value)} className={`px-3 py-1.5 rounded-md text-xs transition-colors ${mode === value ? 'bg-accent/15 text-accent' : 'text-ink-500 hover:text-ink-100'}`}>
              {label}
            </button>
          ))}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            ['Records processed', dataset.metadata.recordCount],
            ['Entities extracted', dataset.metadata.entityCount],
            ['Evidence sources', dataset.metadata.sourceCount],
            ['Relationships provided', dataset.metadata.relationshipCount],
          ].map(([label, value]) => (
            <div key={label} className="panel p-4">
              <p className="label-eyebrow">{label}</p>
              <p className="font-display text-2xl font-semibold text-ink-100 mt-2">{value}</p>
            </div>
          ))}
        </div>

        {!dataset.metadata.processingComplete && (
          <div className="flex items-start gap-3 rounded-lg border border-risk-medium/30 bg-risk-mediumSoft/30 px-4 py-3 text-xs text-risk-medium">
            <ShieldAlert size={16} className="shrink-0 mt-0.5" />
            <span>Processing incomplete: some source records contain no extracted entities. The explorer shows the output as received.</span>
          </div>
        )}
        {dataset.metadata.relationshipCount === 0 && (
          <div className="rounded-lg border border-base-border bg-base-900 px-4 py-3 text-xs text-ink-500">
            No relationships are available in the processed output. Entities below are real extracted entities; no connections are inferred or displayed as fact.
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-5">
          <section className="panel overflow-hidden">
            <div className="p-4 border-b border-base-border flex flex-wrap gap-3">
              <div className="flex items-center gap-2 bg-base-800 border border-base-border rounded-lg px-3 py-2 flex-1 min-w-[220px]">
                <Search size={15} className="text-ink-500" />
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search entities or record IDs…" className="bg-transparent text-sm text-ink-100 placeholder:text-ink-500 outline-none flex-1" />
              </div>
              <select value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)} className="bg-base-800 border border-base-border rounded-lg text-xs text-ink-300 px-3 py-2 outline-none">
                <option value="all">All entity types</option>
                {dataset.metadata.entityTypes.map((type) => <option key={type} value={type}>{entityLabel(type)}</option>)}
              </select>
              <select value={sourceFilter} onChange={(event) => setSourceFilter(event.target.value)} className="bg-base-800 border border-base-border rounded-lg text-xs text-ink-300 px-3 py-2 outline-none max-w-[230px]">
                <option value="all">All evidence sources</option>
                {uniqueSources.map((source) => <option key={source} value={source}>{source}</option>)}
              </select>
            </div>
            <div className="px-4 py-3 border-b border-base-border flex items-center justify-between">
              <span className="label-eyebrow">{filteredEntities.length} matching entities</span>
              <span className="text-[11px] text-ink-500 font-mono">SOURCE: LOCAL PROCESSED OUTPUT</span>
            </div>
            {filteredEntities.length === 0 ? (
              <div className="p-12 text-center text-sm text-ink-500">No entities found for the current filters.</div>
            ) : (
              <div className="divide-y divide-base-border max-h-[600px] overflow-y-auto">
                {filteredEntities.map((entity) => (
                  <button key={entity.id} onClick={() => setSelectedEntity(entity)} className="w-full text-left px-4 py-3 hover:bg-base-800/70 transition-colors flex items-center gap-3">
                    <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: entityColor(entity.type) }} />
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm text-ink-100 truncate">{entity.name}</span>
                      <span className="block text-xs text-ink-500 font-mono mt-0.5">{entity.id} · {entity.metadata.recordId}</span>
                    </span>
                    <span className="text-[11px] text-ink-500 shrink-0">{entityLabel(entity.type)}</span>
                  </button>
                ))}
              </div>
            )}
          </section>

          <aside className="panel min-h-[360px]">
            {!selectedEntity ? (
              <div className="h-full flex flex-col items-center justify-center text-center px-8 py-12">
                <FileText size={26} className="text-ink-500 mb-3" />
                <p className="text-sm text-ink-300 font-medium">Select an entity</p>
                <p className="text-xs text-ink-500 mt-1">Review its normalized metadata, source record, and evidence filename.</p>
              </div>
            ) : (
              <div>
                <div className="p-4 border-b border-base-border flex items-start justify-between gap-3">
                  <div>
                    <p className="label-eyebrow">REAL ENTITY</p>
                    <h2 className="font-display text-base font-semibold text-ink-100 mt-1">{selectedEntity.name}</h2>
                    <p className="text-xs text-ink-500 font-mono mt-1">{selectedEntity.id}</p>
                  </div>
                  <button onClick={() => setSelectedEntity(null)} className="text-ink-500 hover:text-ink-100"><X size={16} /></button>
                </div>
                <div className="p-4 space-y-4 text-xs">
                  <div><p className="label-eyebrow mb-1">TYPE</p><p className="text-ink-100">{entityLabel(selectedEntity.type)}</p></div>
                  <div><p className="label-eyebrow mb-1">METADATA</p><pre className="text-ink-300 bg-base-800 rounded-lg p-3 overflow-auto whitespace-pre-wrap">{JSON.stringify(selectedEntity.metadata, null, 2)}</pre></div>
                  <div><p className="label-eyebrow mb-1">SOURCE RECORDS</p><div className="space-y-1">{selectedEntity.sourceRecords.map((record) => <p key={record.id} className="text-ink-300 font-mono">{record.id} · {record.source || 'source unavailable'}</p>)}</div></div>
                  <div><p className="label-eyebrow mb-1">EVIDENCE</p><div className="flex flex-wrap gap-1.5">{selectedEntity.evidence.length ? selectedEntity.evidence.map((item) => <span key={item} className="px-2 py-1 rounded-md border border-base-border bg-base-800 text-ink-300 font-mono">{item}</span>) : <span className="text-ink-500">No evidence metadata provided.</span>}</div></div>
                </div>
              </div>
            )}
          </aside>
        </div>
      </div>
    </Shell>
  )
}
