import apiClient from './apiClient'

export async function runIntelligence(caseId) { return (await apiClient.post(`/api/intelligence/run/${caseId}`)).data }
export async function getIntelligenceGraph(caseId, limitNodes = 200) { return (await apiClient.get(`/api/intelligence/graph/${caseId}`, { params: { limit_nodes: limitNodes } })).data }
export async function explainEntity(entityId) { return (await apiClient.post(`/api/intelligence/explain/${entityId}`)).data }