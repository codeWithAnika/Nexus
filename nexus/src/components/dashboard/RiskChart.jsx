import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts'

export default function RiskChart({ data }) {
  const total = data.reduce((sum, d) => sum + d.value, 0)
  return (
    <div className="panel p-5 h-full flex flex-col">
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-display text-sm font-semibold text-ink-100">Risk Distribution</h3>
        <span className="label-eyebrow">{total} ENTITIES</span>
      </div>
      <div className="flex-1 min-h-[180px] relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={54} outerRadius={78} paddingAngle={3} strokeWidth={0}>
              {data.map((entry) => (
                <Cell key={entry.name} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: '#161f32', border: '1px solid #233047', borderRadius: 8, fontSize: 12 }}
              itemStyle={{ color: '#eef2f8' }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="font-display text-2xl font-bold text-ink-100">{total}</span>
          <span className="text-[10px] text-ink-500 font-mono">TOTAL</span>
        </div>
      </div>
      <div className="flex justify-center gap-4 mt-2">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-1.5 text-xs text-ink-300">
            <span className="w-2 h-2 rounded-full" style={{ background: d.color }} />
            {d.name} · {d.value}
          </div>
        ))}
      </div>
    </div>
  )
}
