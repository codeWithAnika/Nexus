import { FolderKanban, Share2, Link2, ShieldAlert, BellRing, Database, MapPin, UserRound, FileWarning } from 'lucide-react'
import { motion } from 'framer-motion'

const CARDS = [
  { key: 'activeCases', label: 'Active Cases', icon: FolderKanban, accent: 'text-accent' },
  { key: 'totalRecords', label: 'Records Processed', icon: Database, accent: 'text-accent' },
  { key: 'totalEntities', label: 'Total Entities', icon: Share2, accent: 'text-accent' },
  { key: 'personsIdentified', label: 'Persons Identified', icon: UserRound, accent: 'text-accent' },
  { key: 'locationsIdentified', label: 'Locations Identified', icon: MapPin, accent: 'text-accent' },
  { key: 'crimeTypesIdentified', label: 'Crime Types', icon: FileWarning, accent: 'text-accent' },
  { key: 'evidenceSources', label: 'Evidence Sources', icon: Database, accent: 'text-accent' },
  { key: 'totalRelationships', label: 'Relationships', icon: Link2, accent: 'text-accent' },
  { key: 'highRiskEntities', label: 'High-Risk Entities', icon: ShieldAlert, accent: 'text-risk-high' },
  { key: 'activeAlerts', label: 'Active Alerts', icon: BellRing, accent: 'text-risk-medium' },
]

export default function StatsCards({ stats }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
      {CARDS.map(({ key, label, icon: Icon, accent }, i) => (
        <motion.div
          key={key}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.05, duration: 0.25 }}
          className="panel p-4"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="label-eyebrow">{label}</span>
            <Icon size={16} className={accent} />
          </div>
          <div className="font-display text-2xl font-semibold text-ink-100">{stats?.[key] ?? '—'}</div>
        </motion.div>
      ))}
    </div>
  )
}
