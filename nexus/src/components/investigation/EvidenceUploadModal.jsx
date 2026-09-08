import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, UploadCloud, FileCheck2, Check } from 'lucide-react'

const STAGES = [
  'File uploaded',
  'Validating data',
  'Extracting entities',
  'Discovering relationships',
  'Building network',
  'Analyzing patterns',
  'Generating insights',
  'Analysis complete',
]

export default function EvidenceUploadModal({ open, onClose }) {
  const [fileName, setFileName] = useState(null)
  const [stageIndex, setStageIndex] = useState(-1)

  useEffect(() => {
    if (!open) {
      setFileName(null)
      setStageIndex(-1)
    }
  }, [open])

  useEffect(() => {
    if (stageIndex < 0 || stageIndex >= STAGES.length - 1) return
    const t = setTimeout(() => setStageIndex((i) => i + 1), 550)
    return () => clearTimeout(t)
  }, [stageIndex])

  function simulateUpload(name) {
    setFileName(name)
    setStageIndex(0)
  }

  const done = stageIndex === STAGES.length - 1

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            onClick={(e) => e.stopPropagation()}
            className="panel w-full max-w-md"
          >
            <div className="p-5 border-b border-base-border flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <UploadCloud size={17} className="text-accent" />
                <h3 className="font-display text-base font-semibold text-ink-100">Upload Evidence</h3>
              </div>
              <button onClick={onClose} className="text-ink-500 hover:text-ink-100">
                <X size={18} />
              </button>
            </div>

            <div className="p-5">
              {stageIndex < 0 && (
                <div className="space-y-3">
                  <p className="text-xs text-ink-500">Supported formats: CSV, JSON, TXT. Files are processed locally for this prototype.</p>
                  {['call_records_aug.csv', 'financial_filings.json', 'field_notes.txt'].map((name) => (
                    <button
                      key={name}
                      onClick={() => simulateUpload(name)}
                      className="w-full flex items-center gap-3 px-3.5 py-3 rounded-lg border border-dashed border-base-border hover:border-accent/40 hover:bg-accent/5 transition-colors text-left"
                    >
                      <FileCheck2 size={16} className="text-accent" />
                      <span className="text-sm text-ink-100">{name}</span>
                    </button>
                  ))}
                </div>
              )}

              {stageIndex >= 0 && (
                <div>
                  <p className="text-xs text-ink-500 mb-4 font-mono truncate">{fileName}</p>
                  <div className="space-y-2.5">
                    {STAGES.map((stage, i) => (
                      <div key={stage} className="flex items-center gap-3">
                        <div
                          className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 border ${
                            i < stageIndex
                              ? 'bg-risk-low border-risk-low'
                              : i === stageIndex
                              ? 'border-accent pulse-ring'
                              : 'border-base-border'
                          }`}
                        >
                          {i < stageIndex && <Check size={12} className="text-base-950" />}
                          {i === stageIndex && <span className="w-2 h-2 rounded-full bg-accent" />}
                        </div>
                        <span className={`text-sm ${i <= stageIndex ? 'text-ink-100' : 'text-ink-500'}`}>{stage}</span>
                      </div>
                    ))}
                  </div>

                  {done && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="mt-5 p-3 rounded-lg bg-risk-lowSoft border border-risk-low/30 text-xs text-risk-low"
                    >
                      4 new entities and 6 new relationships identified and merged into Operation Nexus.
                    </motion.div>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
