import apiClient from './apiClient'

export async function getEntities(caseId, params = {}) { return (await apiClient.get('/api/entities', { params: { case_id: caseId, ...params } })).data }
export async function getEntity(entityId) { return (await apiClient.get(`/api/entities/${entityId}`)).data }
export async function getEntityMentions(entityId) { return (await apiClient.get(`/api/entities/${entityId}/mentions`)).data }
export async function getEntityIdentifiers(entityId) { return (await apiClient.get(`/api/entities/${entityId}/identifiers`)).data }