import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, GitCompareArrows, ArrowRight, Loader2 } from 'lucide-react'
import { entities, getEntity, RELATIONSHIP_TYPES } from '../../data/mockData'
import { ENTITY_ICONS, entityColor } from '../../utils/entityVisuals'
import api from '../../services/api'

export default function DiscoverConnectionModal({ open, onClose, onResult }) {
  const [entityA, setEntityA] = useState('')
  const [entityB, setEntityB] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [hasSearched, setHasSearched] = useState(false)
  const [error, setError] = useState('')

  async function handleDiscover() {
    if (!entityA || !entityB) {
      setError('Select both entities to discover a connection.')
      return
    }
    if (entityA === entityB) {
      setError('Choose two different entities.')
      return
    }
    setError('')
    setLoading(true)
    setResult(null)
    const found = await api.discoverConnection(entityA, entityB)
    setLoading(false)
    setHasSearched(true)
    setResult(found)
    onResult(found)
  }

  function handleClose() {
    setResult(null)
    setHasSearched(false)
    setEntityA('')
    setEntityB('')
    setError('')
    onClose()
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            onClick={(e) => e.stopPropagation()}
            className="panel w-full max-w-lg max-h-[85vh] overflow-y-auto"
          >
            <div className="p-5 border-b border-base-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <GitCompareArrows size={17} className="text-accent" />
                <h3 className="font-display text-base font-semibold text-ink-100">Discover Hidden Connection</h3>
              </div>
              <button onClick={handleClose} className="text-ink-500 hover:text-ink-100">
                <X size={18} />
              </button>
            </div>

            <div className="p-5 space-y-4">
              <p className="text-xs text-ink-500">
                Select two entities to find the shortest indirect path connecting them through the network,
                even when no direct relationship is recorded.
              </p>

              <div className="grid grid-cols-1 gap-3">
                <div>
                  <label className="text-xs text-ink-300 mb-1.5 block">Entity A</label>
                  <select
                    value={entityA}
                    onChange={(e) => setEntityA(e.target.value)}
                    className="w-full bg-base-800 border border-base-border rounded-lg px-3 py-2 text-sm text-ink-100 outline-none focus:border-accent/60"
                  >
                    <option value="">Select entity…</option>
                    {entities.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs text-ink-300 mb-1.5 block">Entity B</label>
                  <select
                    value={entityB}
                    onChange={(e) => setEntityB(e.target.value)}
                    className="w-full bg-base-800 border border-base-border rounded-lg px-3 py-2 text-sm text-ink-100 outline-none focus:border-accent/60"
                  >
                    <option value="">Select entity…</option>
                    {entities.map((e) => (
                      <option key={e.id} value={e.id}>
                        {e.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {error && <p className="text-xs text-risk-high">{error}</p>}

              <button
                onClick={handleDiscover}
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accent-soft text-base-950 font-semibold text-sm rounded-lg py-2.5 transition-colors disabled:opacity-60"
              >
                {loading ? <Loader2 size={15} className="animate-spin" /> : <GitCompareArrows size={15} />}
                {loading ? 'Analyzing network…' : 'Discover connection'}
              </button>

              {!loading && hasSearched && result && (
                <div className="rounded-lg bg-risk-lowSoft border border-risk-low/30 p-4">
                  <p className="text-xs font-semibold text-risk-low mb-1">Hidden Connection Discovered</p>
                  <p className="text-xs text-ink-300 mb-3">
                    {result.path.length - 2} intermediary {result.path.length - 2 === 1 ? 'entity' : 'entities'} ·
                    connection strength {result.edges.length <= 2 ? 'strong' : result.edges.length <= 4 ? 'moderate' : 'weak'}
                  </p>
                  <div className="flex flex-wrap items-center gap-1.5">
                    {result.path.map((id, i) => {
                      const e = getEntity(id)
                      const Icon = ENTITY_ICONS[e.type]
                      return (
                        <span key={id} className="flex items-center gap-1.5">
                          <span
                            className="flex items-center gap-1.5 text-[11px] px-2 py-1 rounded-md bg-base-800 border border-base-border text-ink-100"
                          >
                            <Icon size={11} style={{ color: entityColor(e.type) }} />
                            {e.name}
                          </span>
                          {i < result.path.length - 1 && <ArrowRight size={11} className="text-ink-500" />}
                        </span>
                      )
                    })}
                  </div>
                  <div className="mt-3 pt-3 border-t border-risk-low/20 space-y-1">
                    {result.edges.map((edge, i) => (
                      <p key={i} className="text-[11px] text-ink-500">
                        Step {i + 1}: <span className="text-ink-300">{RELATIONSHIP_TYPES[edge.type]}</span>
                        {edge.evidence?.length ? ` · evidence ${edge.evidence.join(', ')}` : ''}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {!loading && hasSearched && !result && (
                <div className="rounded-lg bg-base-800 border border-base-border p-4 text-center">
                  <p className="text-xs text-ink-500">No connection path found between these entities in the current network.</p>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
