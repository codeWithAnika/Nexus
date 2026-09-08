import apiClient from './apiClient'

export async function getRelationships(params = {}) { return (await apiClient.get('/api/relationships', { params })).data }
export async function getRelationship(relationshipId) { return (await apiClient.get(`/api/relationships/${relationshipId}`)).data }