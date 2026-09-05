# Nexus Evidence Processing Handoff Guide
## For: Aayush (Data & Evidence Processing Lead)
**Workspace Location:** `Nexus/aayush work/PS189/processing`

---

## 1. Module Overview & Integration Boundaries

- **Input:** Raw FIR/evidence data (`FIR_details.json` with 2,447 OCR records).
- **Output:** Structured evidence processing output (`structured_evidence_output.json`).
- **Current Backend Authority:** Oracle XE database tables (`firs`, `evidence`, `entities`, `entity_mention_provenance`) remain the **sole authoritative ground truth** for intelligence graph construction.
- **Role of Adapter:** `app/services/aayush_processing_adapter.py` functions as an **interoperability adapter and cross-validation bridge**. It does NOT replace the backend's extraction and resolution pipeline.

### Known Extraction Differences:
1. **Date Metadata:** `structured_evidence_output.json` contains 460 DATE mentions. In the backend, dates are preserved as FIR incident timestamps, not graph entity nodes.
2. **Person Mentions:** 80% direct string match rate (393/493 persons match identically).
3. **Statutes & Police Stations:** Backend applies canonical standardizations (adding "Police Station" suffix, and splitting compound sections such as "341/323/506/34 IPC" into distinct statutory graph nodes).
4. **Overall Semantic Overlap:** 67.91% (948 / 1,396 non-date entities).

---

## 2. Frozen Output Contract

The project specification defines the standard handoff format:
```json
{
  "entities": [
    {
      "temp_id": "P0001",
      "fir_id_ref": "FIR_0",
      "dataset_image_id": 0,
      "extraction_entity_type": "PERSON",
      "raw_value": "Sumita Bera",
      "normalized_value": "Sumita Bera",
      "source_image": "0.jpg",
      "provenance": {
        "source": "aayush_processing",
        "original_type": "PERSON"
      }
    }
  ],
  "relationships": [],
  "metadata": {
    "source": "aayush_processing",
    "processor_version": "1.0.0",
    "total_firs_processed": 544,
    "total_entities_extracted": 1396
  }
}
```

---

## 3. How to Cross-Validate Your Output

The backend exposes a live cross-validation endpoint:
- **Endpoint:** `GET http://localhost:8000/api/processing/cross-validate`
- **Output:**
  - `aayush_total_entities`: Number of entities in your `structured_evidence_output.json`.
  - `oracle_total_canonical_entities`: Canonical entities in Oracle (804).
  - `matched_entities_count`: Direct matches against authoritative canonical entities.
  - `match_rate_percent`: Overall alignment score.
  - `overlap_by_type`: Match breakdown for PERSON, POLICE_STATION, and STATUTE.

---

## 4. What to Work On
- Fine-tuning fuzzy similarity thresholds in `processing/deduplicator.py` to maximize precision without dropping valid complainant names.
- Cleaning noisy OCR artifacts in Hindi/regional text transliterations.
- Exporting updated `structured_evidence_output.json` files for cross-validation testing.

## 5. What NOT to Touch
- Do **NOT** modify raw files in `Nexus/dataset/` or change the SHA-256 hash of `FIR_details.json`.
- Do **NOT** bypass category 2 (Statutes) or category 0 (Police Stations), as both are critical anchors for cross-FIR network topology.
- Do **NOT** alter backend Oracle database models.
