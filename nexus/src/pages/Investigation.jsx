import { useEffect, useMemo, useState } from 'react'
import { useParams, useSearchParams } from 'react-router-dom'
import { Radar, UploadCloud, GitCompareArrows, Clock3, Share2 } from 'lucide-react'
import Sidebar from '../components/layout/Sidebar'
import Topbar from '../components/layout/Topbar'
import LeftPanel from '../components/investigation/LeftPanel'
import NetworkGraph from '../components/investigation/NetworkGraph'
import EntityPanel from '../components/investigation/EntityPanel'
import DiscoverConnectionModal from '../components/investigation/DiscoverConnectionModal'
import EvidenceUploadModal from '../components/investigation/EvidenceUploadModal'
import Timeline from '../components/investigation/Timeline'
import RiskBadge from '../components/common/RiskBadge'
import { cases, timeline as timelineData } from '../data/mockData'
import api from '../services/api'

export default function Investigation() {
  const { caseId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const caseInfo = cases.find((c) => c.id === caseId) || cases[0]

  const [typeFilter, setTypeFilter] = useState([])
  const [riskFilter, setRiskFilter] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedId, setSelectedId] = useState(null)
  const [selectedEntity, setSelectedEntity] = useState(null)
  const [highlightPath, setHighlightPath] = useState(null)
  const [discoverOpen, setDiscoverOpen] = useState(false)
  const [uploadOpen, setUploadOpen] = useState(searchParams.get('upload') === '1')
  const [view, setView] = useState('graph') // graph | timeline
  const [networkData, setNetworkData] = useState({ nodes: [], edges: [] })
  const [networkStatus, setNetworkStatus] = useState('loading')
  const [networkMode, setNetworkMode] = useState('real')

  useEffect(() => {
    if (searchParams.get('upload') === '1') {
      setUploadOpen(true)
      searchParams.delete('upload')
      setSearchParams(searchParams, { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    setNetworkStatus('loading')
    api.getNetwork(caseId).then((result) => {
      setNetworkStatus(result.status || 'ready')
      setNetworkMode(result.mode || 'real')
      setNetworkData(result.graph || { nodes: result.entities || [], edges: result.relationships || [] })
    })
  }, [caseId])

  useEffect(() => {
    if (!selectedId) {
      setSelectedEntity(null)
      return
    }
    api.getEntityDetail(selectedId).then(setSelectedEntity)
  }, [selectedId])

  function handleSelect(id) {
    setHighlightPath(null)
    setSelectedId(id)
  }

  function handleReset() {
    setSelectedId(null)
    setHighlightPath(null)
    setSearchTerm('')
    setTypeFilter([])
    setRiskFilter([])
  }

  const analysisStatus = useMemo(() => (caseInfo.status === 'Active' ? 'Analysis current' : 'Analysis archived'), [caseInfo])

  return (
    <div className="h-screen w-full flex bg-base-950 text-ink-100">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar
          title={
            <span className="flex items-center gap-2.5">
              <Radar size={17} className="text-accent" />
              {caseInfo.name}
            </span>
          }
          subtitle={caseInfo.id}
          right={
            <div className="flex items-center gap-2 mr-2">
              <RiskBadge level={caseInfo.riskLevel} />
              <span className="text-xs px-2 py-1 rounded-md border border-accent/30 bg-accent/10 text-accent">
                {caseInfo.status}
              </span>
              <span className="text-xs px-2 py-1 rounded-md border border-base-border text-ink-500 font-mono hidden lg:inline">
                {analysisStatus}
              </span>
            </div>
          }
        />

        <div className="px-6 pt-4 flex items-center justify-between">
          <div className="flex items-center gap-1 bg-base-800 border border-base-border rounded-lg p-1 w-fit">
            <button
              onClick={() => setView('graph')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors ${
                view === 'graph' ? 'bg-accent/15 text-accent' : 'text-ink-500 hover:text-ink-100'
              }`}
            >
              <Share2 size={13} /> Network Graph
            </button>
            <button
              onClick={() => setView('timeline')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs transition-colors ${
                view === 'timeline' ? 'bg-accent/15 text-accent' : 'text-ink-500 hover:text-ink-100'
              }`}
            >
              <Clock3 size={13} /> Timeline
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setDiscoverOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-accent/30 bg-accent/10 text-accent text-xs hover:bg-accent/15 transition-colors"
            >
              <GitCompareArrows size={13} /> Discover Connection
            </button>
            <button
              onClick={() => setUploadOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-base-border text-ink-300 text-xs hover:border-accent/40 hover:text-ink-100 transition-colors"
            >
              <UploadCloud size={13} /> Upload Evidence
            </button>
          </div>
        </div>

        {view === 'graph' ? (
          <div className="flex-1 min-h-0 flex mt-4">
            <LeftPanel
              caseInfo={caseInfo}
              typeFilter={typeFilter}
              setTypeFilter={setTypeFilter}
              riskFilter={riskFilter}
              setRiskFilter={setRiskFilter}
              searchTerm={searchTerm}
              setSearchTerm={setSearchTerm}
              onReset={handleReset}
              onOpenDiscover={() => setDiscoverOpen(true)}
            />

            <div className="flex-1 min-w-0 relative bg-base-950">
              <div className="absolute top-3 right-4 z-10 flex items-center gap-2 text-[10px] font-mono">
                <span className={`px-2 py-1 rounded border ${networkMode === 'demo' ? 'border-risk-medium/30 bg-risk-mediumSoft text-risk-medium' : 'border-risk-low/30 bg-risk-lowSoft text-risk-low'}`}>
                  {networkMode === 'demo' ? 'DEMO MODE' : 'REAL DATA MODE'}
                </span>
                {networkStatus === 'ready' && networkData.edges.length === 0 && <span className="px-2 py-1 rounded border border-base-border bg-base-900 text-ink-500">NO RELATIONSHIPS</span>}
              </div>
              {highlightPath && (
                <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10 bg-risk-lowSoft border border-risk-low/30 text-risk-low text-xs px-3 py-1.5 rounded-full flex items-center gap-2">
                  <GitCompareArrows size={12} />
                  Showing discovered path · {highlightPath.path.length} entities
                  <button onClick={() => setHighlightPath(null)} className="underline hover:text-risk-low/80">
                    clear
                  </button>
                </div>
              )}
              <NetworkGraph
                typeFilter={typeFilter}
                riskFilter={riskFilter}
                selectedId={selectedId}
                onSelect={handleSelect}
                highlightPath={highlightPath}
                searchTerm={searchTerm}
                graphData={networkData}
              />
            </div>

            <EntityPanel
              entity={selectedEntity}
              onClose={() => handleSelect(null)}
              onSelectRelated={handleSelect}
            />
          </div>
        ) : (
          <div className="flex-1 min-h-0 overflow-auto p-8">
            <div className="max-w-3xl mx-auto">
              <h2 className="font-display text-lg font-semibold text-ink-100 mb-1">Investigation Timeline</h2>
              <p className="text-sm text-ink-500 mb-8">Chronological reconstruction of events as they were identified.</p>
              <Timeline events={timelineData} />
            </div>
          </div>
        )}
      </div>

      <DiscoverConnectionModal
        open={discoverOpen}
        onClose={() => setDiscoverOpen(false)}
        onResult={(res) => {
          if (res) {
            setHighlightPath(res)
            setSelectedId(null)
            setDiscoverOpen(false)
            setView('graph')
          }
        }}
      />

      <EvidenceUploadModal open={uploadOpen} onClose={() => setUploadOpen(false)} />
    </div>
  )
}
