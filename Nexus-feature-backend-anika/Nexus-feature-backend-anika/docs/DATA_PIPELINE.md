# Nexus Data Pipeline Specification
## From Raw ICDAR FIRs to Canonical Graph Intelligence

---

## 1. Raw Dataset Specification

- **Dataset Root:** `Nexus/dataset/FIR_Dataset_ICDAR2023-main/FIR_Dataset_ICDAR2023-main`
- **Metadata File:** `FIR_details.json`
- **SHA-256 Hash:** `693a1e11bd116e2458898e43c48785853b6d6e99439f315b761063c0bb2a357a`
- **Total FIR Images:** 569 (544 populated with OCR annotations)
- **Total Raw OCR Records:** 2,447

### Authoritative Category Mapping

| Category ID | Semantic Meaning | System Entity Handling |
| :---: | :--- | :--- |
| **0** | Police Station / Jurisdiction | `POLICE_STATION` canonical entity; cross-FIR unified. |
| **1** | Year / Date of Filing | Document metadata only; strictly **NOT** an entity. |
| **2** | Statutes & Penal Sections | `STATUTE` canonical entity; cross-FIR unified. |
| **3** | Complainant / Informant / Accused | `PERSON` canonical entity; strict cross-FIR isolation. |

---

## 2. Ingestion & Provenance Preservation

Ingestion into Oracle XE is handled by `app/dataset_ingestion/importer.py`.
- Generates 544 `firs` rows with unique `dataset_image_id`.
- Generates 544 `evidence` rows storing OCR text payloads and hashes.
- For every extraction candidate, an `entity_mention_provenance` row is created storing:
  - Exact character span: `start_char` and `end_char`
  - Bounding box coordinates: `bbox_x1`, `bbox_y1`, `bbox_x2`, `bbox_y2`
  - Source tracking: `evidence_id`, `source_index`, `category_id`, `ocr_confidence`

---

## 3. Conservative Entity Resolution Algorithm

The resolution engine (`app/entity_resolution/resolver.py`) adheres to three deterministic rules:

1. **Same-FIR Name Matching:**
   If a person name appears multiple times in the same FIR (e.g. *Rubina Laskar* in FIR-003), both mentions are merged to one canonical entity.
2. **Cross-FIR Person Separation:**
   Without explicit business identifiers (e.g. Aadhaar, Phone, PAN), persons with identical names across distinct FIRs are **strictly separated** (`KEPT_SEPARATE_CROSS_FIR`) to avoid catastrophic false criminal identity linking.
3. **Statute & Police Station Canonicalization:**
   Identical penal citations (e.g. *498A IPC*) and police stations (*Airport Police Station*) across distinct FIRs are unified to establish cross-jurisdictional network topology.

---

## 4. Aayush Evidence Processing Integration

Aayush's standalone module (`Nexus/aayush work/PS189/processing`) provides fuzzy deduplication and confidence thresholding (`min_score >= 0.60`, `rapidfuzz > 90%`).
- **Adapter Service:** `app/services/aayush_processing_adapter.py` converts Aayush's output into the frozen handoff contract:
  ```json
  {
    "entities": [...],
    "relationships": [],
    "metadata": { "source": "aayush_processing" }
  }
  ```
- **Cross-Validation:** Endpoint `GET /api/processing/cross-validate` evaluates entity overlap against the authoritative Oracle XE database.
