import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { getCases } from '../services/casesApi'

const ActiveCaseContext = createContext(null)
const STORAGE_KEY = 'nexus_active_case_id'

export function ActiveCaseProvider({ children }) {
  const [cases, setCases] = useState([])
  const [activeCaseId, setActiveCaseId] = useState(() => localStorage.getItem(STORAGE_KEY))
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function refreshCases() {
    setLoading(true)
    try {
      const nextCases = await getCases()
      setCases(Array.isArray(nextCases) ? nextCases : [])
      setError('')
      setActiveCaseId((currentId) => {
        const restored = nextCases.find((item) => String(item.id) === String(currentId))
        return String(restored?.id || nextCases[0]?.id || '')
      })
    } catch (requestError) {
      setError(requestError.message || 'Unable to load cases.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refreshCases() }, [])

  useEffect(() => {
    if (activeCaseId) localStorage.setItem(STORAGE_KEY, activeCaseId)
    else localStorage.removeItem(STORAGE_KEY)
  }, [activeCaseId])

  const selectCase = useCallback((caseId) => {
    const selected = cases.find((item) => String(item.id) === String(caseId))
    if (selected) setActiveCaseId(String(selected.id))
  }, [cases])

  const activeCase = useMemo(
    () => cases.find((item) => String(item.id) === String(activeCaseId)) || cases[0] || null,
    [cases, activeCaseId],
  )

  const value = useMemo(() => ({ cases, activeCase, selectCase, loading, error, refreshCases }), [cases, activeCase, selectCase, loading, error])
  return <ActiveCaseContext.Provider value={value}>{children}</ActiveCaseContext.Provider>
}

export function useActiveCase() {
  const context = useContext(ActiveCaseContext)
  if (!context) throw new Error('useActiveCase must be used inside ActiveCaseProvider')
  return context
}