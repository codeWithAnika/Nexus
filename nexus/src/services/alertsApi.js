import apiClient from './apiClient'

export async function getAlerts(caseId, params = {}) { return (await apiClient.get('/api/alerts', { params: { case_id: caseId, ...params } })).data }
export async function getAlert(alertId) { return (await apiClient.get(`/api/alerts/${alertId}`)).data }
export async function updateAlertStatus(alertId, status) { return (await apiClient.put(`/api/alerts/${alertId}/status`, { status })).data }