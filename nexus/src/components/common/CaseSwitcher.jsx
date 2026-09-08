import { ChevronDown } from 'lucide-react'
import { useActiveCase } from '../../context/ActiveCaseContext'

export default function CaseSwitcher({ compact = false }) {
  const { cases, activeCase, selectCase, loading } = useActiveCase()
  return (
    <label className={compact ? 'case-select-wrap' : 'flex items-center gap-2'}>
      {!compact && <span className="text-[10px] uppercase tracking-[0.14em] text-ink-500">Active case</span>}
      <span className={compact ? 'case-select' : 'relative flex items-center'}>
        <select
          aria-label="Select active case"
          value={activeCase?.id || ''}
          onChange={(event) => selectCase(event.target.value)}
          disabled={loading || cases.length === 0}
          className={compact ? 'appearance-none bg-transparent pr-6 outline-none' : 'appearance-none bg-base-800 border border-base-border rounded-lg text-xs text-ink-200 px-3 py-2 pr-8 outline-none'}
        >
          {cases.length === 0 && <option value="">{loading ? 'Loading cases...' : 'No cases available'}</option>}
          {cases.map((item) => <option key={item.id} value={item.id}>{item.title} · {item.case_number}</option>)}
        </select>
        {compact && <ChevronDown size={15} className="pointer-events-none absolute right-0" />}
      </span>
    </label>
  )
}