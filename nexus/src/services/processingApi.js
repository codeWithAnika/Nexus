import apiClient from './apiClient'

export async function getAayushHandoff() { return (await apiClient.get('/api/processing/aayush-handoff')).data }
export async function getCrossValidation() { return (await apiClient.get('/api/processing/cross-validate')).data }