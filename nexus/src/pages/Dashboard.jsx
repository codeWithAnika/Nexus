import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { Radar, Bell, UploadCloud, Clock } from 'lucide-react'
import Shell from '../components/layout/Shell'
import StatsCards from '../components/dashboard/StatsCards'
import RiskChart from '../components/dashboard/RiskChart'
import RecentCases from '../components/dashboard/RecentCases'
import AlertsFeed from '../components/dashboard/AlertsFeed'
import NetworkOverview from '../components/dashboard/NetworkOverview'
import api from '../services/api'
import { cases as allCases } from '../data/mockData'

const QUICK_ACTIONS = [
  {
    label: 'Open Investigation',
    icon: Radar,
    to: '/network',
  },
  {
    label: 'View Alerts',
    icon: Bell,
    to: '/alerts',
  },
  {
    label: 'Upload Evidence',
    icon: UploadCloud,
    to: '/evidence?upload=1',
  },
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState(null)
  const [alerts, setAlerts] = useState([])

  useEffect(() => {
    api.getDashboardSummary().then(setSummary)
    api.getAlerts().then(setAlerts)
  }, [])

  return (
    <Shell title="Command Center" subtitle={`${summary?.mode === 'demo' ? 'DEMO MODE · Operation Nexus' : 'REAL DATA MODE · processed evidence'} · overview across all active investigations`}>
      <div className="space-y-6">
        <StatsCards stats={summary?.stats} />

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          <div className="xl:col-span-2 panel p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-display text-sm font-semibold text-ink-100">Investigation Activity</h3>
              <span className="label-eyebrow">LAST 7 DAYS</span>
            </div>
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={summary?.activityTrend || []}>
                  <CartesianGrid stroke="#1e293e" vertical={false} />
                  <XAxis dataKey="day" tick={{ fill: '#7c869c', fontSize: 11 }} axisLine={{ stroke: '#233047' }} tickLine={false} />
                  <YAxis tick={{ fill: '#7c869c', fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#161f32', border: '1px solid #233047', borderRadius: 8, fontSize: 12 }} />
                  <Line type="monotone" dataKey="entities" stroke="#3aa8ff" strokeWidth={2} dot={false} name="Entities" />
                  <Line type="monotone" dataKey="relationships" stroke="#3ecf8e" strokeWidth={2} dot={false} name="Relationships" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <RiskChart data={summary?.riskDistribution || []} />
        </div>

        {summary?.metadata?.relationshipCount === 0 && (
          <div className="rounded-lg border border-base-border bg-base-900 px-4 py-3 text-xs text-ink-500">
            Real data is active. The processed output contains extracted entities but no relationship records, so network connections are not inferred.
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          <RecentCases cases={allCases.slice(0, 4)} />
          <AlertsFeed alerts={alerts} />
          <NetworkOverview />
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          <div className="xl:col-span-2 panel p-5">
            <div className="flex items-center gap-2 mb-4">
              <Clock size={15} className="text-accent" />
              <h3 className="font-display text-sm font-semibold text-ink-100">Recent Timeline</h3>
            </div>
            <div className="space-y-4">
              {(summary?.timeline || []).slice(-4).reverse().map((t, i) => (
                <div key={i} className="flex gap-3">
                  <div className="flex flex-col items-center pt-1">
                    <span className="w-2 h-2 rounded-full bg-accent" />
                    {i !== 3 && <span className="w-px flex-1 bg-base-border mt-1" />}
                  </div>
                  <div className="pb-1">
                    <p className="text-xs text-ink-500 font-mono">{t.date}</p>
                    <p className="text-sm text-ink-100 font-medium">{t.title}</p>
                    <p className="text-xs text-ink-500 mt-0.5">{t.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel p-5">
            <h3 className="font-display text-sm font-semibold text-ink-100 mb-4">Quick Actions</h3>
            <div className="space-y-2.5">
              {QUICK_ACTIONS.map(({ label, icon: Icon, to }) => (
                <button
                  key={label}
                  onClick={() => navigate(to)}
                  className="w-full flex items-center gap-3 px-3.5 py-3 rounded-lg border border-base-border hover:border-accent/40 hover:bg-accent/5 transition-colors text-left"
                >
                  <Icon size={16} className="text-accent" />
                  <span className="text-sm text-ink-100">{label}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Shell>
  )
}
