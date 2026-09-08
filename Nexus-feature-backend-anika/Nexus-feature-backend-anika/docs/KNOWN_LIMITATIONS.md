# Nexus SIH PS26189 — Known Limitations & System Boundaries

**Project:** AI-Powered Criminal Network Analysis System (PS 26189)  
**Organization:** Ministry of Home Affairs / NCRB, Women Safety Division  
**Branch:** `feature/backend-anika`  
**Status Date:** 2026-09-06  

This document provides a truthful, unvarnished disclosure of current architectural boundaries, deliberate design choices, and pending work across the Nexus project.

---

## 1. Authentication & Authorization (Demo Mode)
- **Current State:** API endpoints currently operate in local demonstration mode without strict JWT bearer token enforcement.
- **Rationale:** Facilitates rapid evaluation by SIH judges and seamless local testing across frontend and integration layers without token expiration friction.
- **Pending Work:** Teammate Safina is responsible for enabling the JWT authentication middleware (`app/core/security.py`) and verifying role-based access control (RBAC) across protected routes before final deployment.

---

## 2. Frontend Implementation Status
- **Current State:** The frontend web application is **NOT YET IMPLEMENTED** in this repository. The `Nexus/frontend` directory does not yet exist.
- **Readiness:** All backend endpoints required for the UI—including Cytoscape-compatible graph schemas (`GET /api/intelligence/graph/{case_id}`), alert triage, entity dossiers, and report downloads—are implemented, tested, and frozen.
- **Pending Work:** Teammate Krisha is responsible for delivering the React/Vite frontend using the frozen contracts documented in `docs/FRONTEND_HANDOFF.md`.

---

## 3. Grounded Explanation Layer (Deterministic vs LLM)
- **Current State:** The entity risk and investigation reasoning endpoint (`POST /api/intelligence/explain/{entity_id}`) uses a **deterministic, factor-based grounded explanation engine**, rather than an external or cloud-hosted LLM.
- **Rationale:**
  - **Zero Hallucination:** Law enforcement and court evidence cannot tolerate generative hallucinations. Explanations strictly cite real graph centrality metrics, Louvain community cluster assignments, and direct statutory co-occurrences.
  - **Zero Latency & Offline Capability:** Eliminates external API dependencies, network timeouts, API key exposure, and rate limits during the SIH evaluation.
- **Future Roadmap:** An offline quantized LLM (e.g., Llama 3 / Mistral via Ollama or vLLM) can be plugged into this grounded factor layer to produce narrative polish without compromising factual integrity.

---

## 4. Conservative Cross-FIR Entity Resolution
- **Current State:** While persons within the *same* FIR are clustered and merged based on exact/normalized name equivalence, identical person names appearing across *different* FIRs are deliberately kept isolated (`KEPT_SEPARATE_CROSS_FIR`).
- **Rationale:** Under Indian evidentiary standards, common names (e.g., "Rahul Kumar", "Ramesh") cannot be assumed to represent the same individual across unrelated cases without corroborating unique government identifiers (Aadhaar, PAN, Voter ID, father's name, or biometric records).
- **Impact:** 493 unique person nodes are preserved. False-positive cross-case linkages are prevented.

---

## 5. Dataset Scope & OCR Characteristics
- **Dataset Source:** ICDAR 2023 Real-world First Information Report Dataset (569 images on disk, 544 usable annotated records, 25 unannotated blank/corrupted scans).
- **Text Extraction:** Ingestion leverages ground-truth OCR transcriptions and bounding boxes provided in `FIR_details.json`.
- **Transliteration & Noise:** Scanned police FIRs contain phonetic variations and handwritten OCR errors. Canonical resolution standardizes police station names and splits compound statute citations (e.g., "341/323/506/34 IPC" is parsed into distinct section nodes).

---

## 6. Teammate Pipeline Interoperability
- **Aayush's Processing Pipeline:** Serves as an independent evidence extraction reference. Due to backend canonicalization (station normalization and section splitting) and filtering of non-entity date metadata, direct string overlap is 31.73%, while semantic overlap is 67.91%. Oracle XE backend entities remain the authoritative ground truth for intelligence graph generation.
- **Aayushman's Intelligence Engine:** Integrated via adapter bridging Oracle XE tables directly to NetworkX graph analytics (Louvain community detection, centrality metrics, multi-tier risk scoring). Phase 1 mock extraction and experimental LLM relationship generation are disabled in favor of verified database evidence.

---

## 7. Pending Teammate Handoff Items
- **Safina (Security & QA):** Security test suite execution, penetration testing, rate limiting, and JWT enforcement.
- **Meet (Integration & Demo):** Git branch convergence into `develop`/`main`, environment setup on evaluation machines, and live presentation rehearsal.
