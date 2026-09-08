import apiClient from './apiClient'

export async function getCases(skip = 0, limit = 100) {
    const response = await apiClient.get('/api/cases', { params: { skip, limit } })
    return response.data
}

export async function getCase(caseId) {
    const response = await apiClient.get(`/api/cases/${caseId}`)
    return response.data
}

export async function createCase(payload) {
    const response = await apiClient.post('/api/cases', payload)
    return response.data
}

export async function updateCase(caseId, payload) {
    const response = await apiClient.put(`/api/cases/${caseId}`, payload)
    return response.data
}

export async function deleteCase(caseId) {
    await apiClient.delete(`/api/cases/${caseId}`)
}