// ---------------------------------------------------------------------------
// NEXUS API service layer.
// Every function currently resolves from local mock data, but is shaped like
// a real async client so pages never need to change when a backend exists.
// Swap the body of each function for an axios call against the commented
// endpoint and nothing upstream needs to change.
// ---------------------------------------------------------------------------
import axios from 'axios'
import {
    cases,
    entities,
    relationships,
    alerts,
    timeline,
    dashboardStats,
    riskDistribution,
    activityTrend,
    getEntity,
    findConnectionPath,
} from '../data/mockData'
import { normalizeMockDataset, normalizeProcessedDataset } from '../data/normalizeDataset'

// eslint-disable-next-line no-unused-vars
const client = axios.create({ baseURL: '/api', timeout: 8000 })

const delay = (ms = 350) => new Promise((resolve) => setTimeout(resolve, ms))

export const DATA_SOURCES = { local: 'local', mock: 'mock', api: 'api' }
let dataSource = DATA_SOURCES.local
let localDatasetPromise
const demoDataset = normalizeMockDataset({ entities, relationships })

async function getLocalDataset() {
    if (!localDatasetPromise) {
        localDatasetPromise = fetch('/data/structured_evidence_output.json')
            .then((response) => {
                if (!response.ok) throw new Error(`Dataset request failed (${response.status}).`)
                return response.json()
            })
            .then(normalizeProcessedDataset)
            .catch((error) => ({ mode: 'real', status: 'invalid', source: 'local', error: error.message }))
    }
    return localDatasetPromise
}

export function setDataSource(source) {
    if (!Object.values(DATA_SOURCES).includes(source)) throw new Error(`Unsupported data source: ${source}`)
    dataSource = source
}

export function getDataSource() {
    return dataSource
}

export async function getDataset(source = dataSource) {
    if (source === DATA_SOURCES.mock) return demoDataset
    if (source === DATA_SOURCES.local) return getLocalDataset()
    return { mode: 'real', status: 'unavailable', source: 'api', error: 'Backend API provider is not configured.' }
}

async function getActiveDataset() {
    return getDataset(dataSource)
}

export const api = {
    // GET /cases
    async getCases() {
        await delay()
        return cases
    },

    // GET /cases/:id
    async getCase(id) {
        await delay(200)
        return cases.find((c) => c.id === id) || cases[0]
    },

    // GET /cases/:id/network
    async getNetwork(_caseId) {
        await delay(500)
        const dataset = await getActiveDataset()
        if (dataset.status !== 'ready') return dataset
        return {...dataset, entities: dataset.graph.nodes, relationships: dataset.graph.edges }
    },

    // GET /entities/:id
    async getEntityDetail(id) {
        await delay(200)
        const dataset = await getActiveDataset()
        const entity = (dataset.entities && dataset.entities.find((item) => item.id === id)) || getEntity(id)
        if (!entity) return null
        const activeRelationships = dataset.relationships || relationships
        const connected = activeRelationships
            .filter((relationship) => relationship.source === id || relationship.target === id)
            .map((relationship) => (relationship.source === id ? relationship.target : relationship.source))
            .map((connectedId) => (dataset.entities && dataset.entities.find((item) => item.id === connectedId)) || getEntity(connectedId))
            .filter(Boolean)
        return {
            ...entity,
            relationships: activeRelationships.filter((relationship) => relationship.source === id || relationship.target === id),
            connected,
        }
    },

    // GET /alerts
    async getAlerts() {
        await delay(250)
        return alerts
    },

    // POST /evidence/upload
    async uploadEvidence(_file) {
        await delay(600)
        return { status: 'accepted', entitiesFound: 4, relationshipsFound: 6 }
    },

    // GET /reports/:caseId
    async getReport(caseId) {
        await delay(300)
        const dataset = await getActiveDataset()
        return {
            case: cases.find((c) => c.id === caseId) || cases[0],
            entities: dataset.entities || entities,
            relationships: dataset.relationships || relationships,
            alerts,
            timeline,
        }
    },

    // GET /dashboard/summary
    async getDashboardSummary() {
        await delay(300)
        const dataset = await getActiveDataset()
        if (dataset.status !== 'ready') return { status: dataset.status, error: dataset.error, stats: dashboardStats, riskDistribution, activityTrend, timeline }
        const realEntities = dataset.entities
        const stats = {
            ...dashboardStats,
            totalRecords: dataset.metadata.recordCount,
            totalEntities: realEntities.length,
            totalRelationships: dataset.relationships.length,
            personsIdentified: realEntities.filter((entity) => entity.type === 'person').length,
            locationsIdentified: realEntities.filter((entity) => entity.type === 'location').length,
            crimeTypesIdentified: realEntities.filter((entity) => entity.type === 'crime_type').length,
            evidenceSources: dataset.metadata.sourceCount,
            highRiskEntities: realEntities.filter((entity) => entity.riskLevel === 'high').length,
        }
        return { mode: dataset.mode, status: dataset.status, stats, riskDistribution: [], activityTrend: [], timeline, metadata: dataset.metadata }
    },

    // Client-side graph pathfinding — would become GET /entities/:a/path/:b
    async discoverConnection(startId, endId) {
        await delay(700)
        const dataset = await getActiveDataset()
        if (dataset.source === 'local' && dataset.relationships.length === 0) return null
        return findConnectionPath(startId, endId)
    },
}

export default api