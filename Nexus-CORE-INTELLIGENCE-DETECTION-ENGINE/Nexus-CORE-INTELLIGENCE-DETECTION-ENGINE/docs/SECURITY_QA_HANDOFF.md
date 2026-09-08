# Nexus Security & QA Audit Handoff Guide
## For: Safina (Cybersecurity & QA Lead)
**Baseline Test Status:** 107/107 Unit & Integration Tests Passing  
**Execution Command:** `python -m unittest discover tests`

## Baseline Status & Handoff Truth

> [!WARNING]
> **Authentication & RBAC Status:** In the current backend baseline, routes are operating in **local demo mode** with authentication middleware bypassed to allow seamless jury evaluation and frontend prototyping.
> **Safina's Responsibility:** Safina owns enabling JWT bearer enforcement (`app/core/security.py`), RBAC checks, OWASP testing, input validation/fuzzing, and security regression tests.
> **DO NOT mark security as 100% complete.**

---

## 1. Security Vectors & Test Matrix

### A. Authentication & Session Security
- **No Token / Missing Header:** Protected administrative routes return `401 Unauthorized`.
- **Invalid / Tampered Token:** Signature validation failure returns `401 Unauthorized`.
- **Password Hashing:** Argon2id implementation (`argon2-cffi`) with safe memory/time parameters.
- **Secrets Management:** Ensure `.env` is never committed; verify `.gitignore` blocks `.env`, credentials, and private keys.

### B. Access Control & Tenant Isolation (RBAC)
- **Case Ownership Isolation:** Verify that an investigator cannot read or alter cases owned by a different user/unit.
- **Referential Integrity Defense:** Verify that attempts to link evidence or entities across mismatched `case_id` are rejected with `CaseOwnershipMismatchError` (`400 Bad Request`).

### C. File Upload Security (`POST /api/evidence/upload`)
- **Allowed MIME Types:** PDF, JPEG, PNG, TIFF only. Reject executables, scripts, or HTML.
- **Malicious Filename Defense:** Filename sanitization blocks path traversal (`../../etc/passwd`, `..\..\Windows`).
- **File Size Limits:** Max file size capped (e.g. 50MB); empty files (`0 bytes`) rejected with `400 Bad Request`.
- **Hash Integrity:** Every uploaded file is digested via SHA-256 upon reception and verified against database storage.

### D. Web Vulnerability Protections
- **SQL / CQL Injection:** 100% parametrized queries via SQLAlchemy 2.x Core/ORM. Zero raw string formatting in SQL statements.
- **Cross-Site Scripting (XSS):** Pydantic input schemas strictly validate and sanitize strings; FastAPI JSON encoders ensure safe encoding.
- **CORS Policies:** Configured in `app/main.py`. Ensure allowed origins are restricted to trusted dashboard domains for production deployment.

### E. Database Integrity & Transactional Safety
- **Orphan Prevention:** All foreign keys enforced (`ON DELETE RESTRICT` / `CASCADE` where specified).
- **Rollback Verification:** In the event of persistence failures during intelligence runs, transactions rollback cleanly with zero half-created records (verified by `test_intelligence_transaction_rollback`).
- **Idempotency Invariant:** Successive execution of ingestion, entity resolution, and intelligence scoring creates zero duplicate rows.

---

## 2. QA Test Suite Execution Commands

1. **Run Full Test Suite:**
   ```powershell
   .\venv\Scripts\python.exe -m unittest discover tests
   ```
2. **Verify Python Syntax & Bytecode Compilation:**
   ```powershell
   .\venv\Scripts\python.exe -m compileall app scripts tests -q
   ```
3. **Verify Dependency Consistency:**
   ```powershell
   .\venv\Scripts\pip.exe check
   ```
4. **Audit Database Foreign Keys & Orphans:**
   ```powershell
   .\venv\Scripts\python.exe -c "from app.database.connection import SessionLocal; from app.models import *; print('DB Connection OK')"
   ```
