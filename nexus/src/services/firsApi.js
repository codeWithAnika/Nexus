import apiClient from './apiClient'

export async function getFirs(caseId, params = {}) { return (await apiClient.get('/api/firs', { params: { case_id: caseId, ...params } })).data }
export async function getFir(firId) { return (await apiClient.get(`/api/firs/${firId}`)).data }