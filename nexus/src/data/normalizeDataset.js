const TYPE_MAP = {
    PERSON: { type: 'person', label: 'Person' },
    LOCATION: { type: 'location', label: 'Location' },
    DATE: { type: 'date', label: 'Date' },
    'CRIME TYPE': { type: 'crime_type', label: 'Crime Type' },
}

function asArray(value) {
    return Array.isArray(value) ? value : []
}

function riskLevelFromScore(score) {
    if (typeof score !== 'number') return null
    if (score >= 75) return 'high'
    if (score >= 45) return 'medium'
    return 'low'
}

function normalizeType(type) {
    const mapped = TYPE_MAP[String(type || '').toUpperCase()]
    return mapped || { type: 'unknown', label: String(type || 'Unknown') }
}

function normalizeEntity(entity, record, index) {
    const mapped = normalizeType(entity.type)
    const name = entity.value || entity.name || `Unnamed ${mapped.label}`
    const recordId = record.fir_id || record.id || `record-${index + 1}`
    const sourceImage = record.source_image || record.source || null
    const score = typeof entity.score === 'number' ? entity.score : null

    return {
        id: entity.id || `${mapped.type}-${recordId}-${index}`,
        name,
        type: mapped.type,
        metadata: {
            originalType: entity.type || null,
            value: entity.value || null,
            confidence: score,
            recordId,
        },
        sourceRecords: [{ id: recordId, source: sourceImage }],
        evidence: sourceImage ? [sourceImage] : [],
        riskScore: null,
        riskLevel: null,
        sourceType: 'real',
    }
}

function mergeEntities(entities) {
    const byId = new Map()
    entities.forEach((entity) => {
        const existing = byId.get(entity.id)
        if (!existing) {
            byId.set(entity.id, entity)
            return
        }
        existing.sourceRecords = [...existing.sourceRecords, ...entity.sourceRecords]
        existing.evidence = [...new Set([...existing.evidence, ...entity.evidence])]
    })
    return [...byId.values()]
}

function normalizeRelationship(relationship, index) {
    if (!relationship || !relationship.source || !relationship.target) return null
    return {
        id: relationship.id || `real-relationship-${index + 1}`,
        source: relationship.source,
        target: relationship.target,
        type: relationship.type || 'associated',
        evidence: asArray(relationship.evidence),
        strength: relationship.strength || null,
        sourceType: 'real',
    }
}

export function normalizeProcessedDataset(payload) {
    if (!Array.isArray(payload)) {
        return { mode: 'real', status: 'invalid', error: 'Processed dataset must be a JSON array.' }
    }

    const records = payload.map((record, index) => ({
        id: record.fir_id || record.id || `record-${index + 1}`,
        source: record.source_image || record.source || null,
        metadata: {
            firId: record.fir_id || null,
            sourceImage: record.source_image || null,
        },
        entities: asArray(record.entities),
        relationships: asArray(record.relationships),
    }))
    const entities = mergeEntities(payload.flatMap((record, recordIndex) => asArray(record.entities).map((entity, index) => normalizeEntity(entity, record, recordIndex * 10000 + index))))
    const relationships = payload.flatMap((record) => asArray(record.relationships)).map(normalizeRelationship).filter(Boolean)

    return {
        mode: 'real',
        status: records.length ? 'ready' : 'empty',
        source: 'local',
        records,
        entities,
        relationships,
        graph: { nodes: entities, edges: relationships },
        metadata: {
            recordCount: records.length,
            entityCount: entities.length,
            relationshipCount: relationships.length,
            sourceCount: new Set(records.map((record) => record.source).filter(Boolean)).size,
            entityTypes: [...new Set(entities.map((entity) => entity.type))],
            processingComplete: records.every((record) => record.entities.length > 0),
            limitations: relationships.length === 0 ? ['No relationships were provided by the processing output.'] : [],
        },
    }
}

export function normalizeMockDataset(dataset) {
    const entities = asArray(dataset.entities).map((entity) => ({
        ...entity,
        metadata: entity.metadata || {},
        sourceRecords: entity.sourceRecords || [],
        sourceType: 'demo',
    }))
    const relationships = asArray(dataset.relationships).map((relationship) => ({
        ...relationship,
        sourceType: 'demo',
    }))
    return {
        mode: 'demo',
        status: 'ready',
        source: 'mock',
        records: [],
        entities,
        relationships,
        graph: { nodes: entities, edges: relationships },
        metadata: {
            recordCount: null,
            entityCount: entities.length,
            relationshipCount: relationships.length,
            sourceCount: null,
            entityTypes: [...new Set(entities.map((entity) => entity.type))],
            processingComplete: true,
            limitations: ['Demo data is fictional and must not be presented as investigative evidence.'],
        },
    }
}

export { riskLevelFromScore, TYPE_MAP }