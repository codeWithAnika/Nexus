import apiClient from './apiClient'

export async function getEvidence(caseId, params = {}) { return (await apiClient.get('/api/evidence', { params: { case_id: caseId, ...params } })).data }
export async function uploadEvidence({ caseId, file, description, evidenceType }) { const form = new FormData();
    form.append('case_id', String(caseId));
    form.append('uploaded_file', file);
    form.append('description', description || '');
    form.append('evidence_type', evidenceType); return (await apiClient.post('/api/evidence/upload', form)).data }
export async function updateEvidence(evidenceId, payload) { return (await apiClient.put(`/api/evidence/${evidenceId}`, payload)).data }
export async function deleteEvidence(evidenceId) { return (await apiClient.delete(`/api/evidence/${evidenceId}`)).data }