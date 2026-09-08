import { useNavigate } from 'react-router-dom'
import { AlertTriangle, AlertCircle } from 'lucide-react'

const PRIORITY_STYLE = {
  high: {
    icon: AlertTriangle,
    color: 'text-risk-high',
    bg: 'bg-risk-highSoft',
  },
  medium: {
    icon: AlertCircle,
    color: 'text-risk-medium',
    bg: 'bg-risk-mediumSoft',
  },
  low: {
    icon: AlertCircle,
    color: 'text-risk-low',
    bg: 'bg-risk-lowSoft',
  },
}

export default function AlertsFeed({ alerts = [] }) {
  const navigate = useNavigate()

  // Prevent .slice() or .map() errors when API data is undefined.
  const safeAlerts = Array.isArray(alerts) ? alerts : []

  return (
    <div className="panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-display text-sm font-semibold text-ink-100">
          Priority Alerts
        </h3>

        <button
          type="button"
          onClick={() => navigate('/alerts')}
          className="text-xs text-accent transition-colors hover:text-accent-soft"
        >
          View all
        </button>
      </div>

      {safeAlerts.length === 0 ? (
        <div className="rounded-lg border border-white/10 p-4 text-center">
          <AlertCircle
            size={20}
            className="mx-auto mb-2 text-ink-400"
          />

          <p className="text-sm text-ink-300">
            No active alerts
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {safeAlerts.slice(0, 4).map((alert, index) => {
            /*
             * Backend may return:
             * HIGH, High, high, or severity instead of priority.
             */
            const priority = String(
              alert?.priority ?? alert?.severity ?? 'medium',
            )
              .trim()
              .toLowerCase()

            // Unknown values safely use the medium design.
            const style =
              PRIORITY_STYLE[priority] ?? PRIORITY_STYLE.medium

            const Icon = style.icon ?? AlertCircle

            return (
              <div
                key={alert?.id ?? `alert-${index}`}
                className={`flex gap-3 rounded-lg p-3 ${style.bg}`}
              >
                <Icon
                  size={16}
                  className={`${style.color} mt-0.5 shrink-0`}
                  aria-hidden="true"
                />

                <div className="min-w-0">
                  <p
                    className={`text-xs font-semibold uppercase tracking-wide ${style.color}`}
                  >
                    {priority} priority
                  </p>

                  <p className="mt-0.5 text-sm leading-snug text-ink-100">
                    {alert?.title ??
                      alert?.message ??
                      alert?.description ??
                      'Intelligence alert'}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}