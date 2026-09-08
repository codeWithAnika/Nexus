import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutGrid, FolderKanban, Radar, Bell, FileBarChart, LogOut, Share2, Database } from 'lucide-react'
import { alerts } from '../../data/mockData'

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Command Center', icon: LayoutGrid },
  { to: '/cases', label: 'Cases', icon: FolderKanban },
  { to: '/investigation/network', label: 'Investigation', icon: Radar },
  { to: '/alerts', label: 'Alerts', icon: Bell, badge: alerts.filter((a) => a.status === 'active').length },
  { to: '/reports//network', label: 'Reports', icon: FileBarChart },
  { to: '/data-explorer', label: 'Data Explorer', icon: Database },
]
import { formatRole, getInitials, useAuth } from '../../context/AuthContext'

export default function Sidebar() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-[220px] shrink-0 h-full bg-base-900 border-r border-base-border flex flex-col">
      <div className="h-16 flex items-center gap-2.5 px-5 border-b border-base-border">
        <div className="w-8 h-8 rounded-md bg-accent/15 border border-accent/30 flex items-center justify-center">
          <Share2 size={16} className="text-accent" />
        </div>
        <div>
          <div className="font-display font-bold tracking-wide text-[15px] leading-none">NEXUS</div>
          <div className="text-[10px] text-ink-500 font-mono mt-0.5">v2.4.1</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon, badge }) => (
          <NavLink
            key={label}
            to={to}
            className={({ isActive }) =>
              `flex items-center justify-between gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-accent/10 text-accent border border-accent/20'
                  : 'text-ink-300 border border-transparent hover:bg-base-800 hover:text-ink-100'
              }`
            }
          >
            <span className="flex items-center gap-2.5">
              <Icon size={17} />
              {label}
            </span>
            {!!badge && (
              <span className="text-[10px] font-mono bg-risk-highSoft text-risk-high px-1.5 py-0.5 rounded-full">
                {badge}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-base-border">
        <div className="flex items-center gap-2.5 px-2 py-2 mb-1">
          <div className="w-8 h-8 rounded-full bg-base-700 border border-base-border flex items-center justify-center text-xs font-semibold text-ink-100">
            {getInitials(user?.full_name || '')}
          </div>
          <div className="min-w-0">
            <div className="text-xs font-medium text-ink-100 truncate" title={user?.username}>{user?.full_name || 'Loading user...'}</div>
            <div className="text-[10px] text-ink-500 font-mono">{formatRole(user?.role)}</div>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-ink-500 hover:text-risk-high hover:bg-risk-highSoft/40 transition-colors"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  )
}
