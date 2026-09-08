import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function Shell({
  title,
  subtitle,
  right,
  children,
  noPad = false,
}) {
  return (
    <div className="flex h-screen w-full bg-base-950 text-ink-100">
      <Sidebar />

      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar
          title={title}
          subtitle={subtitle}
          right={right}
        />

        <main
          className={`min-h-0 flex-1 overflow-auto ${
            noPad ? '' : 'p-4 md:p-6'
          }`}
        >
          {children}
        </main>
      </div>
    </div>
  )
}