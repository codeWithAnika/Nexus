// ---------------------------------------------------------------------------
// NEXUS — mock intelligence dataset
// One consistent fictional investigation: "OPERATION NEXUS"
// All fictional. Any resemblance to real persons or entities is coincidental.
// ---------------------------------------------------------------------------

export const ENTITY_TYPES = {
    person: { label: 'Person', color: '#3aa8ff' },
    phone: { label: 'Phone Number', color: '#7cc4ff' },
    account: { label: 'Financial Account', color: '#3ecf8e' },
    location: { label: 'Location', color: '#e8a13a' },
    organization: { label: 'Organization', color: '#c084fc' },
    vehicle: { label: 'Vehicle', color: '#f472b6' },
    device: { label: 'Device', color: '#94a3b8' },
    event: { label: 'Event', color: '#e5484d' },
}

export const RELATIONSHIP_TYPES = {
    called: 'Called',
    transferred: 'Transferred Money',
    met: 'Met',
    visited: 'Visited',
    owns: 'Owns',
    uses: 'Uses',
    associated: 'Associated With',
    located_at: 'Located At',
    employs: 'Employs',
}

// -------------------------- ENTITIES --------------------------------------
export const entities = [{
        id: 'p-arjun',
        type: 'person',
        name: 'Arjun Mehta',
        role: 'Logistics Coordinator',
        riskScore: 87,
        riskLevel: 'high',
        connections: 9,
        observation: 'Acts as a bridge between two otherwise separate network communities — the Meridian financial cluster and the Falcon logistics cluster.',
        tags: ['bridge-entity', 'multi-community', 'frequent-contact'],
        evidence: ['CDR-2201', 'FIN-0098', 'SURV-114'],
    },
    {
        id: 'p-rohan',
        type: 'person',
        name: 'Rohan Verma',
        role: 'Financial Facilitator',
        riskScore: 74,
        riskLevel: 'high',
        connections: 6,
        observation: 'Repeated high-value transfers routed through shell accounts within a short time window.',
        tags: ['financial-cluster'],
        evidence: ['FIN-0091', 'FIN-0097'],
    },
    {
        id: 'p-kavita',
        type: 'person',
        name: 'Kavita Nair',
        role: 'Freight Dispatcher',
        riskScore: 69,
        riskLevel: 'medium',
        connections: 6,
        observation: 'Coordinates vehicle movements that overlap with unregistered warehouse visits.',
        tags: ['logistics-cluster'],
        evidence: ['SURV-101', 'SURV-108'],
    },
    {
        id: 'p-suresh',
        type: 'person',
        name: 'Suresh Iyer',
        role: 'Financier',
        riskScore: 81,
        riskLevel: 'high',
        connections: 5,
        observation: 'Primary source of funds into the Meridian Trade Solutions account structure.',
        tags: ['financial-cluster', 'fund-source'],
        evidence: ['FIN-0091', 'FIN-0102'],
    },
    {
        id: 'p-neha',
        type: 'person',
        name: 'Neha Kapoor',
        role: 'Accountant',
        riskScore: 58,
        riskLevel: 'medium',
        connections: 4,
        observation: 'Manages books for Meridian Trade Solutions; signatory on two flagged accounts.',
        tags: ['financial-cluster'],
        evidence: ['FIN-0093'],
    },
    {
        id: 'p-dev',
        type: 'person',
        name: 'Dev Malhotra',
        role: 'Transport Contractor',
        riskScore: 63,
        riskLevel: 'medium',
        connections: 5,
        observation: 'Owns the vehicle observed at the Bhiwandi warehouse on multiple flagged dates.',
        tags: ['logistics-cluster'],
        evidence: ['SURV-103'],
    },
    {
        id: 'p-priya',
        type: 'person',
        name: 'Priya Desai',
        role: 'Courier',
        riskScore: 41,
        riskLevel: 'low',
        connections: 3,
        observation: 'Low-frequency contact, mostly device pickups. No direct financial links found yet.',
        tags: ['logistics-cluster'],
        evidence: ['SURV-109'],
    },
    {
        id: 'p-farhan',
        type: 'person',
        name: 'Farhan Sheikh',
        role: 'Unknown Associate',
        riskScore: 55,
        riskLevel: 'medium',
        connections: 3,
        observation: 'Identified only through a shared burner device; identity not yet confirmed.',
        tags: ['unverified'],
        evidence: ['DEV-004'],
    },
    {
        id: 'ph-arjun',
        type: 'phone',
        name: '+91 98XXX-11042',
        role: "Arjun Mehta's registered number",
        riskScore: 62,
        riskLevel: 'medium',
        connections: 4,
        observation: 'Used to contact both financial and logistics cluster members within the same week.',
        tags: [],
        evidence: ['CDR-2201'],
    },
    {
        id: 'ph-rohan',
        type: 'phone',
        name: '+91 99XXX-77310',
        role: "Rohan Verma's registered number",
        riskScore: 47,
        riskLevel: 'low',
        connections: 2,
        observation: 'Standard usage pattern; flagged only due to contact with Arjun Mehta.',
        tags: [],
        evidence: ['CDR-2205'],
    },
    {
        id: 'dev-burner',
        type: 'device',
        name: 'Burner Handset · IMEI 3561XXXXXXXX210',
        role: 'Unregistered device',
        riskScore: 79,
        riskLevel: 'high',
        connections: 3,
        observation: 'Prepaid, no KYC on file. Shared briefly between two unrelated individuals.',
        tags: ['unregistered'],
        evidence: ['DEV-004', 'DEV-006'],
    },
    {
        id: 'acc-meridian',
        type: 'account',
        name: 'Meridian Trade Solutions — Current A/C',
        role: 'Corporate account',
        riskScore: 88,
        riskLevel: 'high',
        connections: 5,
        observation: 'Receives structured deposits below reporting thresholds from multiple individual sources.',
        tags: ['structuring-pattern'],
        evidence: ['FIN-0091', 'FIN-0098'],
    },
    {
        id: 'acc-offshore',
        type: 'account',
        name: 'Offshore Holding — Dubai',
        role: 'Foreign account',
        riskScore: 91,
        riskLevel: 'high',
        connections: 3,
        observation: 'Outbound transfers immediately followed inbound structured deposits, three times in 60 days.',
        tags: ['rapid-movement', 'offshore'],
        evidence: ['FIN-0102', 'FIN-0104'],
    },
    {
        id: 'org-meridian',
        type: 'organization',
        name: 'Meridian Trade Solutions Ltd.',
        role: 'Registered trading company',
        riskScore: 84,
        riskLevel: 'high',
        connections: 5,
        observation: 'Minimal operational footprint relative to declared transaction volume.',
        tags: ['shell-indicators'],
        evidence: ['FIN-0093', 'FIN-0098'],
    },
    {
        id: 'org-falcon',
        type: 'organization',
        name: 'Falcon Freight Co.',
        role: 'Transport & logistics firm',
        riskScore: 66,
        riskLevel: 'medium',
        connections: 4,
        observation: 'Fleet movements do not consistently match filed manifests.',
        tags: ['manifest-mismatch'],
        evidence: ['SURV-101'],
    },
    {
        id: 'loc-warehouse',
        type: 'location',
        name: 'Warehouse 7, Sector 12 — Bhiwandi',
        role: 'Storage facility',
        riskScore: 76,
        riskLevel: 'high',
        connections: 6,
        observation: 'Recurring visits by individuals from both clusters at irregular hours.',
        tags: ['recurring-site'],
        evidence: ['SURV-101', 'SURV-103', 'SURV-108'],
    },
    {
        id: 'loc-office',
        type: 'location',
        name: 'Andheri Corporate Office, Unit 4B',
        role: 'Registered office address',
        riskScore: 52,
        riskLevel: 'medium',
        connections: 3,
        observation: 'Registered address for two entities with no shared declared ownership.',
        tags: [],
        evidence: ['FIN-0093'],
    },
    {
        id: 'loc-dubai',
        type: 'location',
        name: 'Dubai Transit Hub',
        role: 'International transfer point',
        riskScore: 70,
        riskLevel: 'medium',
        connections: 2,
        observation: 'Common routing point for offshore transfers linked to this case.',
        tags: [],
        evidence: ['FIN-0104'],
    },
    {
        id: 'veh-truck',
        type: 'vehicle',
        name: 'Truck · MH-04-XX-1234',
        role: 'Heavy goods vehicle',
        riskScore: 60,
        riskLevel: 'medium',
        connections: 3,
        observation: 'Logged at Warehouse 7 on four of six flagged surveillance dates.',
        tags: [],
        evidence: ['SURV-103', 'SURV-108'],
    },
    {
        id: 'evt-meeting',
        type: 'event',
        name: 'Undisclosed Meeting — 12 Aug',
        role: 'Observed gathering',
        riskScore: 58,
        riskLevel: 'medium',
        connections: 3,
        observation: 'Three individuals from separate clusters present at the same location within a 40-minute window.',
        tags: [],
        evidence: ['SURV-108'],
    },
]

// -------------------------- RELATIONSHIPS (edges) --------------------------
export const relationships = [
    { id: 'e1', source: 'p-arjun', target: 'ph-arjun', type: 'uses', evidence: ['CDR-2201'] },
    { id: 'e2', source: 'p-arjun', target: 'p-rohan', type: 'called', strength: 'frequent', evidence: ['CDR-2201', 'CDR-2205'] },
    { id: 'e3', source: 'p-rohan', target: 'ph-rohan', type: 'uses', evidence: ['CDR-2205'] },
    { id: 'e4', source: 'p-rohan', target: 'p-suresh', type: 'met', evidence: ['SURV-114'] },
    { id: 'e5', source: 'p-suresh', target: 'acc-meridian', type: 'transferred', strength: 'high-value', evidence: ['FIN-0091'] },
    { id: 'e6', source: 'p-neha', target: 'acc-meridian', type: 'associated', evidence: ['FIN-0093'] },
    { id: 'e7', source: 'p-neha', target: 'org-meridian', type: 'employs', evidence: ['FIN-0093'] },
    { id: 'e8', source: 'acc-meridian', target: 'org-meridian', type: 'owns', evidence: ['FIN-0098'] },
    { id: 'e9', source: 'org-meridian', target: 'loc-office', type: 'located_at', evidence: ['FIN-0093'] },
    { id: 'e10', source: 'acc-meridian', target: 'acc-offshore', type: 'transferred', strength: 'high-value', evidence: ['FIN-0102'] },
    { id: 'e11', source: 'acc-offshore', target: 'loc-dubai', type: 'located_at', evidence: ['FIN-0104'] },
    { id: 'e12', source: 'p-arjun', target: 'p-kavita', type: 'met', evidence: ['SURV-108'] },
    { id: 'e13', source: 'p-kavita', target: 'org-falcon', type: 'employs', evidence: ['SURV-101'] },
    { id: 'e14', source: 'p-kavita', target: 'p-dev', type: 'associated', evidence: ['SURV-101'] },
    { id: 'e15', source: 'p-dev', target: 'veh-truck', type: 'owns', evidence: ['SURV-103'] },
    { id: 'e16', source: 'veh-truck', target: 'loc-warehouse', type: 'visited', strength: 'recurring', evidence: ['SURV-103', 'SURV-108'] },
    { id: 'e17', source: 'org-falcon', target: 'loc-warehouse', type: 'located_at', evidence: ['SURV-101'] },
    { id: 'e18', source: 'p-priya', target: 'p-dev', type: 'associated', evidence: ['SURV-109'] },
    { id: 'e19', source: 'p-priya', target: 'dev-burner', type: 'uses', evidence: ['DEV-004'] },
    { id: 'e20', source: 'p-farhan', target: 'dev-burner', type: 'uses', evidence: ['DEV-006'] },
    { id: 'e21', source: 'p-arjun', target: 'loc-warehouse', type: 'visited', strength: 'recurring', evidence: ['SURV-108'] },
    { id: 'e22', source: 'evt-meeting', target: 'p-arjun', type: 'associated', evidence: ['SURV-108'] },
    { id: 'evt2', source: 'evt-meeting', target: 'p-kavita', type: 'associated', evidence: ['SURV-108'] },
    { id: 'evt3', source: 'evt-meeting', target: 'p-dev', type: 'associated', evidence: ['SURV-108'] },
    { id: 'e23', source: 'evt-meeting', target: 'loc-warehouse', type: 'located_at', evidence: ['SURV-108'] },
]

// -------------------------- CASES ------------------------------------------
export const cases = [{
        id: '/network',
        name: 'Operation Nexus',
        description: 'Suspected structured financial movement linked to an unregistered freight network operating out of Bhiwandi.',
        status: 'Active',
        riskLevel: 'high',
        entityCount: entities.length,
        alertCount: 5,
        lead: 'Insp. S. Rathore',
        opened: '2026-07-28',
        lastUpdated: '2026-08-16',
    },
    {
        id: 'CASE-2026-0119',
        name: 'Silverline Remittance Review',
        description: 'Routine review of remittance patterns flagged by automated threshold monitoring.',
        status: 'Active',
        riskLevel: 'medium',
        entityCount: 8,
        alertCount: 2,
        lead: 'Insp. A. Bhatt',
        opened: '2026-07-02',
        lastUpdated: '2026-08-10',
    },
    {
        id: 'CASE-2026-0087',
        name: 'Coastal Cargo Discrepancy',
        description: 'Manifest mismatches identified during a routine port authority audit.',
        status: 'Under Review',
        riskLevel: 'medium',
        entityCount: 6,
        alertCount: 1,
        lead: 'Insp. R. Krishnan',
        opened: '2026-06-14',
        lastUpdated: '2026-07-30',
    },
    {
        id: 'CASE-2026-0053',
        name: 'Northgate Identity Cluster',
        description: 'Group of identity documents sharing overlapping metadata; verification pending.',
        status: 'Closed',
        riskLevel: 'low',
        entityCount: 4,
        alertCount: 0,
        lead: 'Insp. M. Fernandes',
        opened: '2026-05-02',
        lastUpdated: '2026-06-18',
    },
]

// -------------------------- ALERTS ------------------------------------------
export const alerts = [{
        id: 'ALT-501',
        priority: 'high',
        type: 'Suspicious Network Bridge',
        title: 'Entity bridges two previously separate communities',
        description: 'Arjun Mehta connects the Meridian financial cluster and the Falcon logistics cluster, a pattern consistent with a coordinating role.',
        entities: ['p-arjun'],
        caseId: '/network',
        status: 'active',
        timestamp: '2026-08-16T09:12:00',
    },
    {
        id: 'ALT-502',
        priority: 'high',
        type: 'Structuring Pattern',
        title: 'Deposits structured below reporting threshold',
        description: 'Meridian Trade Solutions account received five deposits from separate individuals, each just under the reporting threshold, within nine days.',
        entities: ['acc-meridian', 'p-suresh'],
        caseId: '/network',
        status: 'active',
        timestamp: '2026-08-14T15:40:00',
    },
    {
        id: 'ALT-503',
        priority: 'high',
        type: 'Rapid Offshore Movement',
        title: 'Funds moved offshore within 48 hours of deposit',
        description: 'Outbound transfer to the Dubai holding account followed inbound structured deposits by less than two days on three occasions.',
        entities: ['acc-meridian', 'acc-offshore'],
        caseId: '/network',
        status: 'active',
        timestamp: '2026-08-13T11:05:00',
    },
    {
        id: 'ALT-504',
        priority: 'medium',
        type: 'Shared Device',
        title: 'Unregistered device shared between two individuals',
        description: 'A prepaid handset with no KYC record was used by both Priya Desai and an unconfirmed associate, Farhan Sheikh.',
        entities: ['dev-burner', 'p-priya', 'p-farhan'],
        caseId: '/network',
        status: 'active',
        timestamp: '2026-08-11T18:22:00',
    },
    {
        id: 'ALT-505',
        priority: 'medium',
        type: 'Manifest Mismatch',
        title: 'Vehicle movements do not match filed manifests',
        description: 'Truck MH-04-XX-1234 was logged at Warehouse 7 on dates not reflected in Falcon Freight filed manifests.',
        entities: ['veh-truck', 'org-falcon'],
        caseId: '/network',
        status: 'active',
        timestamp: '2026-08-09T07:50:00',
    },
    {
        id: 'ALT-499',
        priority: 'low',
        type: 'Address Overlap',
        title: 'Two entities share a registered office address',
        description: 'Meridian Trade Solutions and an unrelated filer both list Unit 4B, Andheri Corporate Office as their registered address.',
        entities: ['org-meridian', 'loc-office'],
        caseId: '/network',
        status: 'resolved',
        timestamp: '2026-08-02T13:00:00',
    },
]

// -------------------------- TIMELINE ------------------------------------------
export const timeline = [{
        date: '2026-08-01',
        title: 'Initial data ingestion',
        description: 'Call detail records and financial filings for the reported tip-off were ingested and entity extraction began.',
    },
    {
        date: '2026-08-05',
        title: 'Communication detected',
        description: 'Repeated contact identified between Arjun Mehta and Rohan Verma across a nine-day window.',
    },
    {
        date: '2026-08-09',
        title: 'Manifest mismatch flagged',
        description: 'Vehicle MH-04-XX-1234 logged at Warehouse 7 on dates absent from Falcon Freight filed manifests.',
    },
    {
        date: '2026-08-11',
        title: 'Shared device identified',
        description: 'A single unregistered handset traced to two separate individuals in the network.',
    },
    {
        date: '2026-08-13',
        title: 'Financial relationship identified',
        description: 'Structured deposits into the Meridian account traced to Suresh Iyer, followed by rapid offshore transfer.',
    },
    {
        date: '2026-08-14',
        title: 'Structuring pattern confirmed',
        description: 'Five deposits, each below the reporting threshold, identified within a nine-day period.',
    },
    {
        date: '2026-08-16',
        title: 'Bridge entity confirmed',
        description: 'Arjun Mehta confirmed as the sole link between the financial and logistics clusters, based on call and location data.',
    },
]

// -------------------------- HELPERS ------------------------------------------
export function getEntity(id) {
    return entities.find((e) => e.id === id)
}

export function getEntityRelationships(id) {
    return relationships.filter((r) => r.source === id || r.target === id)
}

export function getConnectedEntities(id) {
    const rels = getEntityRelationships(id)
    return rels.map((r) => (r.source === id ? r.target : r.source)).map(getEntity).filter(Boolean)
}

// Breadth-first search shortest path between two entities across the graph.
export function findConnectionPath(startId, endId) {
    if (startId === endId) return null
    const adjacency = {}
    relationships.forEach((r) => {
        adjacency[r.source] = adjacency[r.source] || []
        adjacency[r.target] = adjacency[r.target] || []
        adjacency[r.source].push({ node: r.target, edge: r })
        adjacency[r.target].push({ node: r.source, edge: r })
    })

    const visited = new Set([startId])
    const queue = [{ node: startId, path: [startId], edges: [] }]

    while (queue.length) {
        const { node, path, edges } = queue.shift()
        if (node === endId) return { path, edges }
        const neighbours = adjacency[node] || []
        for (const { node: next, edge }
            of neighbours) {
            if (!visited.has(next)) {
                visited.add(next)
                queue.push({ node: next, path: [...path, next], edges: [...edges, edge] })
            }
        }
    }
    return null
}

export const currentCase = cases[0]

export const dashboardStats = {
    activeCases: cases.filter((c) => c.status === 'Active').length,
    totalEntities: entities.length,
    totalRelationships: relationships.length,
    highRiskEntities: entities.filter((e) => e.riskLevel === 'high').length,
    activeAlerts: alerts.filter((a) => a.status === 'active').length,
}

export const riskDistribution = [
    { name: 'High', value: entities.filter((e) => e.riskLevel === 'high').length, color: '#e5484d' },
    { name: 'Medium', value: entities.filter((e) => e.riskLevel === 'medium').length, color: '#e8a13a' },
    { name: 'Low', value: entities.filter((e) => e.riskLevel === 'low').length, color: '#3ecf8e' },
]

export const activityTrend = [
    { day: 'Aug 10', entities: 12, relationships: 15 },
    { day: 'Aug 11', entities: 14, relationships: 18 },
    { day: 'Aug 12', entities: 15, relationships: 20 },
    { day: 'Aug 13', entities: 16, relationships: 22 },
    { day: 'Aug 14', entities: 18, relationships: 23 },
    { day: 'Aug 15', entities: 19, relationships: 24 },
    { day: 'Aug 16', entities: entities.length, relationships: relationships.length },
]