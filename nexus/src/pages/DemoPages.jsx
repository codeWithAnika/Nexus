import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertTriangle,
  Check,
  ChevronDown,
  Clock3,
  Download,
  FileSearch,
  Fingerprint,
  GitBranch,
  Plus,
  Search,
  ShieldCheck,
  Upload,
  X,
} from 'lucide-react'
import { motion } from 'framer-motion'
import CytoscapeComponent from 'react-cytoscapejs'
import Shell from '../components/layout/Shell'

const demoAlerts = [
  {
    id: 'a1',
    title: 'Cross-FIR Entity Link',
    severity: 'HIGH',
    time: '18 min ago',
    description:
      'Subject A-17 appears across 3 independent FIR clusters.',
    evidence: 'FIR-00021, FIR-00144, FIR-00308',
    entities: 'Subject A-17, Subject B-04',
    action:
      'Review cross-FIR co-occurrence and validate source mentions.',
  },
  {
    id: 'a2',
    title: 'Dense Association Cluster',
    severity: 'MEDIUM',
    time: '42 min ago',
    description:
      '8 direct relationships detected around Meridian Trading.',
    evidence: 'FIR-00308, 12 evidence mentions',
    entities: 'Meridian Trading, Subject B-04',
    action:
      'Review organization links and transaction context.',
  },
  {
    id: 'a3',
    title: 'Repeated Statute Pattern',
    severity: 'MEDIUM',
    time: '1 hr ago',
    description:
      'IPC Section 420 co-occurs across 12 evidence mentions.',
    evidence: 'FIR-00021, FIR-00217',
    entities: 'IPC Section 420, Subject A-17',
    action:
      'Compare statute context across referenced FIRs.',
  },
  {
    id: 'a4',
    title: 'Location Recurrence',
    severity: 'LOW',
    time: '2 hrs ago',
    description:
      'Warehouse 03 is referenced in four resolved evidence clusters.',
    evidence: 'FIR-00021, FIR-00308',
    entities: 'Warehouse 03, Northstar Logistics',
    action:
      'Confirm location provenance before escalation.',
  },
  {
    id: 'a5',
    title: 'New Evidence Mention',
    severity: 'LOW',
    time: '3 hrs ago',
    description:
      'OCR extraction added a high-confidence organization mention.',
    evidence: 'FIR-00412',
    entities: 'Subject C-22, Meridian Trading',
    action:
      'Inspect the source page and bounding-box context.',
  },
]

const evidenceRows = [
  [
    'EV-00021',
    'FIR-00021',
    'FIR Document',
    'ICDAR 2023',
    '96.8%',
    '06 Sep 2026',
  ],
  [
    'EV-00144',
    'FIR-00144',
    'OCR Text',
    'ICDAR 2023',
    '94.2%',
    '06 Sep 2026',
  ],
  [
    'EV-00308',
    'FIR-00308',
    'Image',
    'FIR_images_v1',
    '98.1%',
    '05 Sep 2026',
  ],
  [
    'EV-00217',
    'FIR-00217',
    'CDR',
    'Operational ingest',
    '91.7%',
    '05 Sep 2026',
  ],
  [
    'EV-00412',
    'FIR-00412',
    'Transaction',
    'Evidence ingest',
    '89.4%',
    '04 Sep 2026',
  ],
]

const networkNodes = [
  ['subject-a17', 'Subject A-17', 'person', 120, 115],
  ['subject-b04', 'Subject B-04', 'person', 320, 65],
  ['subject-c22', 'Subject C-22', 'person', 430, 170],
  ['airport', 'Airport Police Station', 'station', 75, 260],
  ['central', 'Central Station', 'station', 330, 280],
  ['ipc420', 'IPC Section 420', 'statute', 215, 205],
  ['ipc406', 'IPC Section 406', 'statute', 505, 275],
  ['electronics', 'Electronics Complex', 'location', 110, 400],
  ['warehouse', 'Warehouse 03', 'location', 400, 415],
  ['meridian', 'Meridian Trading', 'org', 610, 130],
  ['northstar', 'Northstar Logistics', 'org', 615, 350],
  ['subject-d09', 'Subject D-09', 'person', 550, 485],
  ['market', 'Old City Market', 'location', 250, 490],
  ['ipc120', 'IPC Section 120B', 'statute', 690, 250],
]

const networkEdges = [
  ['subject-a17', 'subject-b04'],
  ['subject-a17', 'airport'],
  ['subject-a17', 'ipc420'],
  ['subject-b04', 'meridian'],
  ['subject-b04', 'central'],
  ['subject-c22', 'meridian'],
  ['subject-c22', 'ipc406'],
  ['airport', 'electronics'],
  ['central', 'warehouse'],
  ['ipc420', 'meridian'],
  ['ipc406', 'warehouse'],
  ['meridian', 'northstar'],
  ['northstar', 'subject-d09'],
  ['subject-d09', 'ipc120'],
  ['market', 'warehouse'],
  ['subject-a17', 'market'],
  ['ipc120', 'northstar'],
]

const networkElements = [
  ...networkNodes.map(([id, label, type, x, y]) => ({
    data: { id, label, type },
    position: { x, y },
  })),
  ...networkEdges.map(([source, target], index) => ({
    data: {
      id: `edge-${index}`,
      source,
      target,
    },
  })),
]

const networkEntity = {
  'subject-a17': ['Subject A-17', 'PERSON', 72, 94, 8],
  'subject-b04': ['Subject B-04', 'PERSON', 58, 91, 5],
  airport: ['Airport Police Station', 'POLICE STATION', 12, 99, 6],
  meridian: ['Meridian Trading', 'ORGANIZATION', 46, 87, 4],
}

const graphStyles = [
  {
    selector: 'node',
    style: {
      label: 'data(label)',
      color: '#dbe4ff',
      'font-size': 8,
      'text-valign': 'bottom',
      'text-margin-y': 8,
      'text-wrap': 'wrap',
      'text-max-width': 90,
      width: 22,
      height: 22,
      'border-width': 2,
      'border-color': '#080b16',
    },
  },
  {
    selector: 'node[type = "person"]',
    style: {
      'background-color': '#f97316',
    },
  },
  {
    selector: 'node[type = "station"]',
    style: {
      'background-color': '#22d3ee',
    },
  },
  {
    selector: 'node[type = "statute"]',
    style: {
      'background-color': '#8b5cf6',
    },
  },
  {
    selector: 'node[type = "location"]',
    style: {
      'background-color': '#10b981',
    },
  },
  {
    selector: 'node[type = "org"]',
    style: {
      'background-color': '#f59e0b',
    },
  },
  {
    selector: 'edge',
    style: {
      width: 1.2,
      'line-color': '#4e5a88',
      'target-arrow-color': '#4e5a88',
      'target-arrow-shape': 'triangle',
      opacity: 0.72,
    },
  },
  {
    selector: ':selected',
    style: {
      'border-color': '#ffffff',
      'border-width': 3,
    },
  },
]

function PageHeader({ title, subtitle, action }) {
  return (
    <div className="subpage-heading">
      <div>
        <div className="eyebrow">
          <span className="live-line" />
          NEXUS / LIVE CASE WORKSPACE
        </div>

        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>

      {action}
    </div>
  )
}

function PageCard({ children, className = '' }) {
  return <div className={`panel demo-card ${className}`}>{children}</div>
}

function Modal({ title, close, children }) {
  return (
    <div
      className="modal-backdrop"
      onClick={close}
      role="presentation"
    >
      <motion.div
        initial={{ y: 15, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="evidence-modal demo-modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="modal-header">
          <div>
            <div className="eyebrow">
              NEXUS / INTELLIGENCE WORKSPACE
            </div>

            <h2>{title}</h2>
          </div>

          <button
            type="button"
            aria-label="Close modal"
            onClick={close}
          >
            <X size={18} />
          </button>
        </div>

        {children}
      </motion.div>
    </div>
  )
}

function Toast({ text }) {
  return (
    <div className="toast" role="status">
      <Check size={17} />

      <div>
        <strong>Success</strong>
        <span>{text}</span>
      </div>
    </div>
  )
}

export function NetworkPage() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState(null)
  const [search, setSearch] = useState('')

  const inspectNode = (node) => {
    const entity =
      networkEntity[node.id()] || [
        node.data('label'),
        String(node.data('type') || 'entity').toUpperCase(),
        34,
        86,
        3,
      ]

    setSelected({
      name: entity[0],
      type: entity[1],
      risk: entity[2],
      confidence: entity[3],
      connections: entity[4],
    })
  }

  return (
    <Shell
      title="Network Intelligence"
      subtitle="Explore evidence-grounded entities and relationships."
    >
      <PageHeader
        title="Network Intelligence"
        subtitle="Explore resolved entities, relationship patterns and explainable graph indicators."
        action={
          <button
            type="button"
            className="button secondary"
            onClick={() => setSelected(null)}
          >
            <GitBranch size={15} />
            Reset Layout
          </button>
        }
      />

      <PageCard className="network-page-card">
        <div className="network-toolbar">
          <div className="search page-search">
            <Search size={15} />

            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Find an entity..."
            />
          </div>

          <button type="button" className="button secondary">
            All entity types
            <ChevronDown size={14} />
          </button>

          <button
            type="button"
            className="button primary"
            onClick={() => setSelected(null)}
          >
            Fit Graph
          </button>

          <span className="network-stat">
            Network visualization
          </span>
        </div>

        <div className="real-network-graph">
          <CytoscapeComponent
            elements={networkElements}
            layout={{ name: 'preset' }}
            stylesheet={graphStyles}
            style={{
              width: '100%',
              height: '100%',
            }}
            cy={(cy) => {
              cy.removeAllListeners('tap', 'node')

              cy.on('tap', 'node', (event) => {
                inspectNode(event.target)
              })
            }}
          />
        </div>

        <div className="network-footer">
          <span>
            <i className="person" />
            Person
          </span>

          <span>
            <i className="station" />
            Police Station
          </span>

          <span>
            <i className="statute" />
            Statute
          </span>

          <span>
            <i className="location" />
            Location
          </span>

          <span className="network-disclaimer">
            Decision-support indicators — not findings of guilt.
          </span>
        </div>
      </PageCard>

      {selected && (
        <aside className="network-drawer">
          <button
            type="button"
            aria-label="Close entity drawer"
            className="drawer-close"
            onClick={() => setSelected(null)}
          >
            <X size={17} />
          </button>

          <div className="drawer-eyebrow">
            <span className="pulse-dot" />
            ENTITY INTELLIGENCE
          </div>

          <h2>{selected.name}</h2>

          <span className="drawer-type">
            {selected.type} · RESOLVED ENTITY
          </span>

          <div className="network-score">
            <div>
              <span>RISK SCORE</span>
              <strong>
                {selected.risk}
                <small>/100</small>
              </strong>
            </div>

            <div>
              <span>CONFIDENCE</span>
              <strong>
                {selected.confidence}
                <small>%</small>
              </strong>
            </div>
          </div>

          <p>
            {selected.connections} direct connections identified across
            evidence-grounded relationships.
          </p>

          <button
            type="button"
            className="button primary full"
            onClick={() => navigate('/evidence')}
          >
            <FileSearch size={15} />
            View Evidence
          </button>

          <div className="drawer-note">
            <ShieldCheck size={15} />
            Results require investigator verification and are not findings
            of guilt.
          </div>
        </aside>
      )}
    </Shell>
  )
}

function EvidenceModal({ row, close }) {
  return (
    <Modal title={`Source evidence · ${row[1]}`} close={close}>
      <div className="evidence-preview">
        <span>FIRST INFORMATION REPORT</span>

        <div className="preview-lines" />

        <div className="highlight-box">
          Subject A-17
          <small>OCR mention</small>
        </div>
      </div>

      <div className="evidence-detail-grid">
        <div>
          <span>Extracted text</span>
          <strong>
            Subject A-17 referenced in associated evidence record.
          </strong>
        </div>

        <div>
          <span>OCR confidence</span>
          <strong>{row[4]}</strong>
        </div>

        <div>
          <span>Integrity status</span>
          <strong>Verification metadata available</strong>
        </div>

        <div>
          <span>Provenance trail</span>
          <strong>{row[2]} → OCR → Entity resolution</strong>
        </div>
      </div>

      <p className="modal-note">
        <Fingerprint size={15} />
        Traceable to the original FIR evidence. Investigator verification
        is required.
      </p>
    </Modal>
  )
}

export function EvidencePage() {
  const [query, setQuery] = useState('')
  const [selected, setSelected] = useState(null)
  const [uploadOpen, setUploadOpen] = useState(false)
  const [toast, setToast] = useState(false)

  const rows = evidenceRows.filter((row) =>
    row.join(' ').toLowerCase().includes(query.toLowerCase()),
  )

  const handleDemoUpload = () => {
    setUploadOpen(false)
    setToast(true)

    window.setTimeout(() => {
      setToast(false)
    }, 3500)
  }

  return (
    <Shell
      title="Evidence & FIR Repository"
      subtitle="Trace graph insights to their source evidence."
    >
      <PageHeader
        title="Evidence & FIR Repository"
        subtitle="Trace every graph insight back to source documents and extracted evidence."
        action={
          <button
            type="button"
            className="button primary"
            onClick={() => setUploadOpen(true)}
          >
            <Upload size={15} />
            Upload Evidence
          </button>
        }
      />

      <div className="toolbar">
        <div className="search page-search">
          <Search size={15} />

          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search evidence ID or FIR reference..."
          />
        </div>

        {[
          'FIR Document',
          'Image',
          'OCR Text',
          'CDR',
          'Transaction',
        ].map((type) => (
          <button
            type="button"
            className="filter-chip"
            key={type}
          >
            {type}
          </button>
        ))}
      </div>

      <PageCard className="table-card">
        <table>
          <thead>
            <tr>
              {[
                'Evidence ID',
                'FIR Reference',
                'Type',
                'Source',
                'Integrity',
                'OCR Confidence',
                'Added Date',
                'Action',
              ].map((heading) => (
                <th key={heading}>{heading}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.map((row) => (
              <tr key={row[0]}>
                {row.slice(0, 4).map((cell, index) => (
                  <td key={`${row[0]}-${index}`}>{cell}</td>
                ))}

                <td>
                  <span className="integrity-cell">
                    <Check size={12} />
                    Metadata available
                  </span>
                </td>

                <td>{row[4]}</td>
                <td>{row[5]}</td>

                <td>
                  <button
                    type="button"
                    className="table-action"
                    onClick={() => setSelected(row)}
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </PageCard>

      {selected && (
        <EvidenceModal
          row={selected}
          close={() => setSelected(null)}
        />
      )}

      {uploadOpen && (
        <Modal
          title="Upload Evidence"
          close={() => setUploadOpen(false)}
        >
          <label>
            Evidence file
            <input type="file" />
          </label>

          <label>
            Evidence type
            <select defaultValue="FIR Document">
              <option>FIR Document</option>
              <option>OCR Text</option>
              <option>CDR</option>
              <option>Transaction</option>
            </select>
          </label>

          <label>
            Description
            <textarea placeholder="Add evidence provenance notes..." />
          </label>

          <button
            type="button"
            className="button primary full"
            onClick={handleDemoUpload}
          >
            Submit Evidence
          </button>
        </Modal>
      )}

      {toast && (
        <Toast text="Evidence staged locally for review." />
      )}
    </Shell>
  )
}

export function AlertsPage() {
  const [alerts, setAlerts] = useState(
    demoAlerts.map((alert) => ({
      ...alert,
      status: 'Open',
    })),
  )

  const [selected, setSelected] = useState(null)
  const [severityFilter, setSeverityFilter] = useState('ALL')
  const [statusFilter, setStatusFilter] = useState('ACTIVE')

  const updateAlert = (id, status) => {
    setAlerts((current) =>
      current.map((alert) =>
        alert.id === id ? { ...alert, status } : alert,
      ),
    )
  }

  const filteredAlerts = alerts.filter((alert) => {
    const severityMatches =
      severityFilter === 'ALL' ||
      alert.severity === severityFilter

    const statusMatches =
      statusFilter === 'ALL' ||
      (statusFilter === 'ACTIVE' && alert.status !== 'Resolved') ||
      (statusFilter === 'RESOLVED' && alert.status === 'Resolved')

    return severityMatches && statusMatches
  })

  const activeCount = alerts.filter(
    (alert) => alert.status !== 'Resolved',
  ).length

  return (
    <Shell
      title="Alerts"
      subtitle="Review evidence-grounded operational signals."
    >
      <PageHeader
        title="Alerts & Signals"
        subtitle="Operational signals requiring review, acknowledgement or resolution."
      />

      <div className="toolbar">
        <select
          value={severityFilter}
          onChange={(event) => setSeverityFilter(event.target.value)}
        >
          <option value="ALL">All severities</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>

        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.target.value)}
        >
          <option value="ACTIVE">Open and acknowledged</option>
          <option value="RESOLVED">Resolved</option>
          <option value="ALL">All statuses</option>
        </select>

        <span className="demo-chip">
          {activeCount} active alerts
        </span>
      </div>

      <PageCard className="alerts-page-card">
        {filteredAlerts.length === 0 ? (
          <div className="p-8 text-center text-ink-500">
            No alerts match the selected filters.
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const severity = String(
              alert?.severity || 'MEDIUM',
            ).toLowerCase()

            return (
              <div
                className={`alert-page-row ${
                  alert.status === 'Resolved' ? 'resolved' : ''
                }`}
                key={alert.id}
              >
                <div className={`alert-mark ${severity}`}>
                  <AlertTriangle size={15} />
                </div>

                <div className="alert-page-copy">
                  <div>
                    <h2>{alert.title}</h2>

                    <span className={`severity ${severity}`}>
                      {alert.severity}
                    </span>

                    <span className="alert-status">
                      {alert.status}
                    </span>
                  </div>

                  <p>{alert.description}</p>

                  <small>
                    <Clock3 size={12} />
                    {alert.time} · Evidence-grounded signal
                  </small>
                </div>

                <div className="alert-actions">
                  <button
                    type="button"
                    className="table-action"
                    onClick={() => setSelected(alert)}
                  >
                    View Details
                  </button>

                  {alert.status !== 'Resolved' && (
                    <>
                      <button
                        type="button"
                        className="ack-button"
                        onClick={() =>
                          updateAlert(alert.id, 'Acknowledged')
                        }
                      >
                        {alert.status === 'Acknowledged'
                          ? 'Acknowledged'
                          : 'Acknowledge'}
                      </button>

                      <button
                        type="button"
                        className="resolve-button"
                        onClick={() =>
                          updateAlert(alert.id, 'Resolved')
                        }
                      >
                        <Check size={13} />
                        Resolve
                      </button>
                    </>
                  )}
                </div>
              </div>
            )
          })
        )}
      </PageCard>

      {selected && (
        <Modal
          title={selected.title}
          close={() => setSelected(null)}
        >
          <div className="detail-block">
            <span>Evidence basis</span>
            <strong>{selected.evidence}</strong>
          </div>

          <div className="detail-block">
            <span>Connected entities</span>
            <strong>{selected.entities}</strong>
          </div>

          <div className="detail-block">
            <span>Recommended investigator action</span>
            <strong>{selected.action}</strong>
          </div>

          <button
            type="button"
            className="button primary full"
            onClick={() => setSelected(null)}
          >
            Close Details
          </button>
        </Modal>
      )}
    </Shell>
  )
}

export function ReportsPage() {
  const [reports, setReports] = useState([
    [
      'Operation Nexus Intelligence Brief',
      'Operation Nexus',
      'Network Analysis',
      '06 Sep 2026',
      'Completed',
    ],
    [
      'Evidence Provenance Report',
      'Operation Nexus',
      'Evidence Audit',
      '05 Sep 2026',
      'Completed',
    ],
    [
      'Cross-FIR Link Summary',
      'FIR Cluster 07',
      'Investigation Summary',
      '03 Sep 2026',
      'Completed',
    ],
  ])

  const [selectedReport, setSelectedReport] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [toast, setToast] = useState(false)

  const generateReport = () => {
    setGenerating(true)

    window.setTimeout(() => {
      setReports((current) => [
        [
          'Fresh Intelligence Analysis',
          'Operation Nexus',
          'Network Analysis',
          new Date().toLocaleDateString('en-IN'),
          'Completed',
        ],
        ...current,
      ])

      setGenerating(false)
      setToast(true)

      window.setTimeout(() => {
        setToast(false)
      }, 3500)
    }, 1500)
  }

  const downloadReport = (report) => {
    const selected = report || [
      'NEXUS Intelligence Report',
      'Operation Nexus',
    ]

    const content = [
      'NEXUS INTELLIGENCE REPORT',
      '',
      `Title: ${selected[0]}`,
      `Case: ${selected[1]}`,
      '',
      'Evidence-grounded network analysis.',
      '',
      'Decision-support findings require investigator verification.',
    ].join('\n')

    const blob = new Blob([content], {
      type: 'text/plain;charset=utf-8',
    })

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')

    link.href = url
    link.download = 'nexus-intelligence-report.txt'

    document.body.appendChild(link)
    link.click()
    link.remove()

    URL.revokeObjectURL(url)
  }

  return (
    <Shell
      title="Intelligence Reports"
      subtitle="Generate and review investigation reports."
    >
      <PageHeader
        title="Intelligence Reports"
        subtitle="Explainable outputs prepared for investigator review and case handoff."
        action={
          <button
            type="button"
            className="button primary"
            onClick={generateReport}
            disabled={generating}
          >
            <GitBranch size={15} />

            {generating ? 'Generating...' : 'Generate Report'}
          </button>
        }
      />

      {generating && (
        <div className="generation-strip">
          <span className="pulse-dot" />
          Aggregating evidence and preparing the report...
        </div>
      )}

      <div className="card-grid reports-grid">
        {reports.map((report, index) => (
          <PageCard key={`${report[0]}-${index}`}>
            <div className="card-top">
              <span className="case-id">
                REPORT-{String(index + 21).padStart(3, '0')}
              </span>

              <span className="state active">
                {report[4]}
              </span>
            </div>

            <h2>{report[0]}</h2>

            <p className="report-meta">
              {report[1]} · {report[2]}
            </p>

            <div className="card-footer">
              <span>{report[3]}</span>

              <div>
                <button
                  type="button"
                  className="table-action"
                  onClick={() => setSelectedReport(report)}
                >
                  View Report
                </button>

                <button
                  type="button"
                  aria-label={`Download ${report[0]}`}
                  className="icon-button"
                  onClick={() => downloadReport(report)}
                >
                  <Download size={15} />
                </button>
              </div>
            </div>
          </PageCard>
        ))}
      </div>

      {selectedReport && (
        <Modal
          title={selectedReport[0]}
          close={() => setSelectedReport(null)}
        >
          <div className="report-preview">
            <div className="eyebrow">
              NEXUS / INTELLIGENCE REPORT
            </div>

            <h2>{selectedReport[0]}</h2>

            <p>
              {selectedReport[1]} · Evidence-grounded network analysis
            </p>

            <div className="report-summary">
              <strong>544</strong>
              <span>FIRs analysed</span>

              <strong>804</strong>
              <span>Entities resolved</span>

              <strong>905</strong>
              <span>Relationships mapped</span>
            </div>

            <p>
              Decision-support findings are traceable to source evidence
              and require investigator verification.
            </p>
          </div>

          <button
            type="button"
            className="button primary full"
            onClick={() => downloadReport(selectedReport)}
          >
            <Download size={15} />
            Download Report
          </button>
        </Modal>
      )}

      {toast && (
        <Toast text="Report generated successfully." />
      )}
    </Shell>
  )
}