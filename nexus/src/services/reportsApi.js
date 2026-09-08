import apiClient from './apiClient'

export async function getReports(caseId, params = {}) { return (await apiClient.get('/api/reports', { params: { case_id: caseId, ...params } })).data }
export async function getReport(reportId) { return (await apiClient.get(`/api/reports/${reportId}`)).data }
export async function generateReport(caseId) { return (await apiClient.post(`/api/reports/generate/${caseId}`)).data }