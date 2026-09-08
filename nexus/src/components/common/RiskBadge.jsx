const RISK_STYLES = {
  high: 'bg-risk-highSoft text-risk-high border-risk-high/30',
  medium: 'bg-risk-mediumSoft text-risk-medium border-risk-medium/30',
  low: 'bg-risk-lowSoft text-risk-low border-risk-low/30',
}

const RISK_LABEL = {
  high: 'High Risk',
  medium: 'Medium Risk',
  low: 'Low Risk',
}

export default function RiskBadge({ level, dot = true, className = '' }) {
  if (!level) return null
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-xs font-medium border ${RISK_STYLES[level]} ${className}`}
    >
      {dot && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      {RISK_LABEL[level]}
    </span>
  )
}
