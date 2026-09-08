# Nexus SIH Demo Runbook
## Step-by-Step Operator Guide for Jury & Evaluators

---

## 1. Environment & Data Segregation

| Environment Layer | Storage Location | Data Profile | Role in Demo |
| :--- | :--- | :--- | :--- |
| **Raw Dataset** | `Nexus/dataset/` | 544 Real FIR Scans + `FIR_details.json` | Immutable source of truth (SHA-256 verified) |
| **Production Demo DB** | Oracle XE 21c (`NEXUS`) | 544 FIRs, 804 Entities, 905 Edges, 804 Analyses | The official live demonstration database |
| **Test Fixtures** | `tests/` | Mock handoffs & transactional rollbacks | Automated regression validation only |

---

## 2. Pre-Demo Verification Checklist

Run this single command in `Nexus/backend` to verify all systems are green:
```powershell
.\venv\Scripts\python.exe -c "
from app.database.connection import SessionLocal
from app.models import FIR, Evidence, Entity, Relationship, Alert, Report
from sqlalchemy import func, select

db = SessionLocal()
print('=== NEXUS LIVE STATUS ===')
print('FIRs:', db.scalar(select(func.count(FIR.id))))
print('Evidence:', db.scalar(select(func.count(Evidence.id))))
print('Entities:', db.scalar(select(func.count(Entity.id))))
print('Relationships:', db.scalar(select(func.count(Relationship.id))))
print('Alerts:', db.scalar(select(func.count(Alert.id))))
print('Reports:', db.scalar(select(func.count(Report.id))))
db.close()
"
```
**Expected Output:**
- FIRs: 544
- Evidence: 544
- Entities: 804
- Relationships: 905
- Alerts: 6
- Reports: 1+

---

## 3. Starting the System

### Terminal 1: Backend Server
```powershell
cd Nexus/backend
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
*Verify: Open `http://localhost:8000/docs` in your browser to inspect interactive Swagger UI.*

### Terminal 2: Frontend Dashboard (Krisha)
```powershell
cd Nexus/frontend
npm run dev
```
*Access: `http://localhost:5173` or `http://localhost:3000`.*

---

## 4. How to Rerun / Reseed the Pipeline On Demand

If evaluators ask to see the pipeline run live from scratch:

1. **Trigger Entity Resolution:**
   ```powershell
   .\venv\Scripts\python.exe -c "from app.database.connection import SessionLocal; from app.entity_resolution.service import resolve_and_persist_full_dataset; db=SessionLocal(); r=resolve_and_persist_full_dataset(db=db); print('Resolved:', r.canonical_entities_total); db.close()"
   ```
2. **Trigger Intelligence Analysis via API:**
   ```powershell
   curl -X POST http://localhost:8000/api/intelligence/run/21
   ```
3. **Trigger Executive Report Generation:**
   ```powershell
   curl -X POST http://localhost:8000/api/reports/generate/21
   ```
