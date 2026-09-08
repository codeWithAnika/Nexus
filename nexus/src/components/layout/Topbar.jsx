import { Search, ShieldCheck } from 'lucide-react'
import CaseSwitcher from '../common/CaseSwitcher'
import useBackendStatus from '../../hooks/useBackendStatus'
import { formatRole, getInitials, useAuth } from '../../context/AuthContext'

export default function Topbar({ title, subtitle, right }) {
  const { user, loading } = useAuth()
  const { apiOnline, databaseReady } = useBackendStatus()
  return (
    <header className="h-16 shrink-0 border-b border-base-border bg-base-900/70 backdrop-blur px-6 flex items-center justify-between">
      <div>
        <h1 className="font-display font-semibold text-lg text-ink-100 leading-none">{title}</h1>
        {subtitle && <p className="text-xs text-ink-500 mt-1">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-4">
        <CaseSwitcher />
        {right}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-base-800 border border-base-border text-ink-500 text-xs w-56">
          <Search size={14} />
          <span>Search entities, cases…</span>
        </div>
        <div className={`flex items-center gap-1.5 text-xs font-mono ${apiOnline && databaseReady ? 'text-risk-low' : 'text-risk-medium'}`}>
          <ShieldCheck size={14} />
          {apiOnline ? 'API ONLINE' : 'API OFFLINE'} · {databaseReady ? 'DB READY' : 'DB NOT READY'}
        </div>
      </div>
      <div className="hidden lg:flex items-center gap-2 border-l border-base-border pl-4" title={user?.username || 'User profile'}>
        <div className="w-7 h-7 rounded-full bg-base-700 flex items-center justify-center text-[10px] font-semibold text-ink-100">{loading ? <span className="w-3 h-2 rounded bg-ink-500/40 animate-pulse" /> : getInitials(user?.full_name || '')}</div>
        <div className="min-w-0"><strong className="block text-xs text-ink-100 truncate max-w-28">{loading ? <span className="inline-block w-20 h-2 rounded bg-ink-500/40 animate-pulse" /> : user?.full_name}</strong><span className="block text-[10px] text-ink-500">{loading ? 'Loading...' : formatRole(user?.role)}</span></div>
      </div>
    </header>
  )
}
