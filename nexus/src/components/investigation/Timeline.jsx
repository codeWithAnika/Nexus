import { motion } from 'framer-motion'

export default function Timeline({ events }) {
  return (
    <div className="relative pl-2">
      <div className="absolute left-[13px] top-2 bottom-2 w-px bg-base-border" />
      <div className="space-y-6">
        {events.map((e, i) => (
          <motion.div
            key={e.date + e.title}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="relative flex gap-4"
          >
            <div className="relative z-10 w-[26px] h-[26px] rounded-full bg-base-800 border-2 border-accent flex items-center justify-center shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-accent" />
            </div>
            <div className="pb-1">
              <p className="text-xs font-mono text-accent">{e.date}</p>
              <p className="text-sm font-medium text-ink-100 mt-0.5">{e.title}</p>
              <p className="text-xs text-ink-500 mt-1 leading-relaxed max-w-lg">{e.description}</p>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
