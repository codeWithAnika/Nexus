import { useEffect, useMemo, useRef, useState } from 'react'
import CytoscapeComponent from 'react-cytoscapejs'
import { Activity, BrainCircuit, Filter, Maximize2, RefreshCw, Search, ZoomIn, ZoomOut } from 'lucide-react'
import Shell from '../components/layout/Shell'
import { useActiveCase } from '../context/ActiveCaseContext'
import { getEntities, getEntity, getEntityIdentifiers, getEntityMentions } from '../services/entitiesApi'
import { getRelationships } from '../services/relationshipsApi'
import { explainEntity, getIntelligenceGraph, runIntelligence } from '../services/intelligenceApi'

const COLORS = { PERSON: '#e88935', POLICE_STATION: '#35c6d9', STATUTE: '#a78bfa', LOCATION: '#3ecf8e', ORGANIZATION: '#e4ae45', OTHER: '#75829c' }
const list = (response) => Array.isArray(response) ? response : response?.items || []

export default function NetworkLive() {
  const { activeCase } = useActiveCase()
  const cyRef = useRef(null)
  const [graph, setGraph] = useState({ nodes: [], edges: [], total_nodes: 0, total_edges: 0 })
  const [entityTotal, setEntityTotal] = useState(0)
  const [selected, setSelected] = useState(null)
  const [search, setSearch] = useState('')
  const [type, setType] = useState('ALL')
  const [relationship, setRelationship] = useState('ALL')
  const [layout, setLayout] = useState('cose')
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')

  async function loadGraph() {
    if (!activeCase) return
    setLoading(true)
    try {
      const [nextGraph, entityResult] = await Promise.all([getIntelligenceGraph(activeCase.id, 200), getEntities(activeCase.id, { limit: 1 })])
      setGraph(nextGraph)
      setEntityTotal(Number(entityResult?.total || 0))
      setError('')
    } catch (requestError) { setError(requestError.message || 'Unable to load live graph.') }
    finally { setLoading(false) }
  }
  useEffect(() => { loadGraph() }, [activeCase?.id])

  async function selectNode(id) {
    try {
      const [entity, mentions, identifiers, relationships, explanation] = await Promise.all([getEntity(id), getEntityMentions(id), getEntityIdentifiers(id), getRelationships({ entity_id: id, limit: 100 }), explainEntity(id)])
      setSelected({ entity, mentions: list(mentions), identifiers: list(identifiers), relationships: list(relationships), explanation })
    } catch (requestError) { setError(requestError.message || 'Unable to load entity intelligence.') }
  }

  async function executePipeline() {
    if (!activeCase) return
    setRunning(true); setError('')
    try { await runIntelligence(activeCase.id); await loadGraph() } catch (requestError) { setError(requestError.message || 'Intelligence execution failed.') }
    finally { setRunning(false) }
  }

  const types = [...new Set(graph.nodes.map((node) => node.type))]
  const relationships = [...new Set(graph.edges.map((edge) => edge.type))]
  const visibleNodes = useMemo(() => graph.nodes.filter((node) => (type === 'ALL' || node.type === type) && (!search || node.label.toLowerCase().includes(search.toLowerCase()))), [graph.nodes, type, search])
  const visibleIds = new Set(visibleNodes.map((node) => String(node.id)))
  const visibleEdges = graph.edges.filter((edge) => visibleIds.has(String(edge.source)) && visibleIds.has(String(edge.target)) && (relationship === 'ALL' || edge.type === relationship))
  const elements = [...visibleNodes.map((node) => ({ data: { id: String(node.id), label: node.label, type: node.type, confidence: node.confidence } })), ...visibleEdges.map((edge) => ({ data: { id: `edge-${edge.id}`, source: String(edge.source), target: String(edge.target), type: edge.type, confidence: edge.confidence, description: edge.description } }))]
  const stylesheet = [{ selector: 'node', style: { 'background-color': (node) => COLORS[node.data('type')] || COLORS.OTHER, label: 'data(label)', color: '#dbe4ff', 'font-size': 8, 'text-valign': 'bottom', 'text-margin-y': 7, width: 22, height: 22, 'border-width': 2, 'border-color': '#080b16' } }, { selector: 'edge', style: { width: 1.2, 'line-color': '#4e5a88', 'target-arrow-color': '#4e5a88', 'target-arrow-shape': 'triangle', opacity: 0.7 } }, { selector: '.dim', style: { opacity: 0.12 } }, { selector: '.selected', style: { 'border-color': '#fff', 'border-width': 4 } }]

  return <Shell title="Network Intelligence" subtitle={activeCase ? `${activeCase.title} · LIVE DATA` : 'Loading active case'} noPad>
    <div className="h-full flex flex-col"><div className="px-5 py-3 border-b border-base-border flex flex-wrap items-center gap-2"><div className="flex items-center gap-2 bg-base-800 border border-base-border rounded-lg px-3 py-2 flex-1 min-w-[180px]"><Search size={14} className="text-ink-500" /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search entities..." className="bg-transparent text-xs text-ink-100 outline-none flex-1" /></div><select value={type} onChange={(event) => setType(event.target.value)} className="bg-base-800 border border-base-border rounded-lg text-xs text-ink-300 px-2 py-2"><option value="ALL">All entity types</option>{types.map((item) => <option key={item}>{item}</option>)}</select><select value={relationship} onChange={(event) => setRelationship(event.target.value)} className="bg-base-800 border border-base-border rounded-lg text-xs text-ink-300 px-2 py-2"><option value="ALL">All relationships</option>{relationships.map((item) => <option key={item}>{item}</option>)}</select><select value={layout} onChange={(event) => { setLayout(event.target.value); cyRef.current?.layout({ name: event.target.value, animate: false }).run() }} className="bg-base-800 border border-base-border rounded-lg text-xs text-ink-300 px-2 py-2"><option value="cose">Cose layout</option><option value="concentric">Concentric layout</option></select><button title="Fit graph" onClick={() => cyRef.current?.fit(undefined, 40)} className="p-2 rounded-lg border border-base-border text-ink-300"><Maximize2 size={14} /></button><button title="Zoom in" onClick={() => cyRef.current?.zoom(cyRef.current.zoom() + 0.2)} className="p-2 rounded-lg border border-base-border text-ink-300"><ZoomIn size={14} /></button><button title="Zoom out" onClick={() => cyRef.current?.zoom(Math.max(0.2, cyRef.current.zoom() - 0.2))} className="p-2 rounded-lg border border-base-border text-ink-300"><ZoomOut size={14} /></button><button onClick={loadGraph} className="p-2 rounded-lg border border-base-border text-ink-300" title="Reload graph"><RefreshCw size={14} /></button><button disabled={running} onClick={executePipeline} className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-xs text-white disabled:opacity-50"><BrainCircuit size={14} /> {running ? 'Running...' : 'Run Intelligence'}</button></div>
    {error && <div className="mx-5 mt-3 flex items-center justify-between rounded-lg border border-risk-high/30 bg-risk-highSoft/20 px-3 py-2 text-xs text-risk-high"><span>{error}</span><button onClick={loadGraph}><RefreshCw size={13} /></button></div>}
    <div className="px-5 py-2 flex items-center justify-between text-[10px] font-mono text-ink-500"><span>Showing {visibleNodes.length} of {entityTotal || graph.total_nodes} entities · {visibleEdges.length} relationships</span><span className="text-risk-medium">Decision-support indicators — not findings of guilt.</span></div>
    <div className="flex-1 min-h-0 flex"><div className="flex-1 min-w-0 relative">{loading ? <div className="absolute inset-0 grid place-items-center text-sm text-ink-500"><Activity className="animate-pulse mr-2" /> Loading live graph...</div> : <CytoscapeComponent elements={elements} layout={{ name: layout, animate: false, padding: 40 }} stylesheet={stylesheet} style={{ width: '100%', height: '100%' }} cy={(cy) => { cyRef.current = cy; cy.on('tap', 'node', (event) => { cy.elements().removeClass('selected dim'); const node = event.target; node.addClass('selected'); selectNode(Number(node.id())) }) }} />}</div>{selected && <aside className="w-[330px] shrink-0 border-l border-base-border bg-base-900 p-5 overflow-auto"><button onClick={() => setSelected(null)} className="text-xs text-ink-500 hover:text-ink-100 mb-4">Close entity</button><p className="label-eyebrow">ENTITY INTELLIGENCE</p><h2 className="font-display text-lg font-semibold text-ink-100 mt-1">{selected.entity.name}</h2><p className="text-xs text-accent mt-1">{selected.entity.entity_type} · confidence {selected.entity.confidence ?? '—'}</p><div className="grid grid-cols-2 gap-3 my-5"><div><span className="label-eyebrow">RISK</span><strong className="block text-ink-100 mt-1">{selected.explanation?.risk_score ?? '—'}</strong></div><div><span className="label-eyebrow">LEVEL</span><strong className="block text-ink-100 mt-1">{selected.explanation?.risk_level || '—'}</strong></div></div><p className="text-xs text-ink-300 leading-relaxed">{selected.explanation?.explanation || 'No explanation available.'}</p><h3 className="label-eyebrow mt-5 mb-2">IDENTIFIERS</h3>{selected.identifiers.length ? selected.identifiers.map((item) => <p key={item.id} className="text-xs text-ink-300">{item.identifier_type}: {item.identifier_value}</p>) : <p className="text-xs text-ink-500">None recorded</p>}<h3 className="label-eyebrow mt-5 mb-2">OCR MENTIONS</h3>{selected.mentions.slice(0, 8).map((item) => <div key={item.id} className="border-b border-base-border py-2 text-xs"><strong className="text-ink-200">{item.matched_text}</strong><span className="block text-ink-500">chars {item.start_char}–{item.end_char} · bbox [{item.bbox_x1}, {item.bbox_y1}, {item.bbox_x2}, {item.bbox_y2}]</span></div>)}</aside>}</div><div className="px-5 py-2 border-t border-base-border flex flex-wrap gap-3 text-[10px] text-ink-500">{Object.entries(COLORS).map(([key, color]) => <span key={key} className="flex items-center gap-1"><i className="w-2 h-2 rounded-full" style={{ background: color }} />{key}</span>)}</div></div>
  </Shell>
}
