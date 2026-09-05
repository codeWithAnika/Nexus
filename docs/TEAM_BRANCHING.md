# Nexus Git Team Branching & Contribution Strategy
## Problem Statement 26189 — Ministry of Home Affairs

---

## 1. Branch Strategy

To ensure non-conflicting, modular development across all 6 members, each teammate works on their dedicated feature branch:

| Member | Domain | Feature Branch | Target Merge Branch |
| :--- | :--- | :--- | :--- |
| **Anika** | Backend + Database | `feature/backend-anika` | `develop` / `main` |
| **Krisha** | Frontend + Dashboard | `feature/frontend-krisha` | `develop` / `main` |
| **Aayushman**| Intelligence Engine | `feature/intelligence-aayushman` | `develop` / `main` |
| **Aayush** | Data & Evidence Processing| `feature/processing-aayush` | `develop` / `main` |
| **Safina** | Security + QA | `feature/security-safina` | `develop` / `main` |
| **Meet** | Integration + Final Demo | `feature/integration-meet` | `develop` / `main` |

---

## 2. Contribution & Safety Rules

1. **Never Commit Directly to `main`:** All code merges must happen through peer-reviewed Pull Requests (PRs).
2. **Never Commit Database Credentials or `.env`:** Ensure `.env` is listed in `.gitignore`.
3. **Preserve Database Migration Chain:** Only Anika modifies or generates Alembic migrations (`alembic/versions/`). The current head is `e8f3b2c1d4a5`.
4. **Never Modify Raw Dataset Files:** The SHA-256 hash of `FIR_details.json` must remain `693a1e11bd116e2458898e43c48785853b6d6e99439f315b761063c0bb2a357a`.
5. **Always Run Test Discovery Before Pushing:**
   ```powershell
   python -m unittest discover tests
   ```
   PRs will not be approved unless all tests pass cleanly.
