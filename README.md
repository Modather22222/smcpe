# SMCPE — Sudan Multi-Currency Payroll Engine

> COMP-3 exact payroll for SDG/USD/SAR/AED + NSIF 8/17% + PIT 5/10/15/20% + ESG + Bankak export on $5 VPS.

## Quickstart ( <10m )

```bash
# 1. COBOL
make -C backend/cobol && ls -lh backend/cobol/libpayroll.so # 28KB

# 2. DB
DB_PATH=backend/db/smcpe.db python3 backend/db/migrate.py # 84K, 4 emp, 9 fx

# 3. API (needs python3.13 venv, not 3.14)
python3.13 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt
DB_PATH=backend/db/smcpe.db COBOL_LIB=backend/cobol/libpayroll.so backend/.venv/bin/uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 &

# 4. Verify
curl -s http://127.0.0.1:8000/api/health | jq
curl -s http://127.0.0.1/api/health | jq # via Nginx
pytest backend/tests -v # 3 passed

# 5. Login + run
TOKEN=$(curl -s -X POST http://127.0.0.1/api/auth/login -H "Content-Type: application/json" -d '{"email":"owner@nileagro.sd","password":"admin123"}' | jq -r .access_token)
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1/api/employees | jq
RID=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"period":"2026-09"}' http://127.0.0.1/api/runs | jq -r .run_id)
curl -s -X POST -H "Authorization: Bearer $TOKEN" http://127.0.0.1/api/runs/$RID/compute | jq .totals
curl -s -H "Authorization: Bearer $TOKEN" "http://127.0.0.1/api/bank/file?run_id=$RID" | head
```

## Structure

- `landing-page/` — public site (5 pages, EN/AR, <50KB, waterfall demo). Open `http://127.0.0.1/` via Nginx.
- `dashboard/` — operational console (10 pages + login.html, config.js/auth.js, app.js API wiring with mock fallback). Open `http://127.0.0.1/app/` → `login.html` (owner@nileagro.sd/admin123).
- `backend/` — GnuCOBOL `libpayroll.so` (28KB) + FastAPI + SQLite WAL (`backend/db/smcpe.db`).
  - `cobol/` — copybooks + 5 modules (PRL-CALC etc) + Makefile
  - `api/` — app, payroll_lib (ctypes), schemas, security (bcrypt), routers (10 groups)
  - `db/` — schema.sql, seed.sql, migrate.py, conn.py
  - `workers/` — bank_export.py, payslip_sender.py
  - `templates/` — payslip.txt (794 bytes)
- `docs/` — 01-architecture, 02-cobol, 03-api, 04-db, 05-deployment, 06-operations, 07-security, 08-qa-pilot
- `ops/` — nginx/smcpe.conf, systemd/smcpe-api.service, scripts/backup.sh/restore.sh
- `plan.md` — full production plan with checkboxes (all Phase 0-7 ✅, 8-9 in progress)

## Money rule

- COBOL `PIC S9(11)V99 COMP-3` + `ROUNDED` only at NSIF/PIT final
- Python `Decimal(...).quantize(Decimal("0.00"))`
- JSON strings `"3150051.36"` never `number`
- Every `payroll_runs` stores `fx_snapshot_json` + `statutory_version` for replay

## Docs

- `docs/01-architecture.md` — diagram, stack, money rules
- `docs/02-cobol-engine.md` — build, ABI, COMP-3 tests
- `docs/03-api-contract.md` — curl examples, OpenAPI at `http://127.0.0.1:8000/docs`
- `docs/04-db-schema.md` — ER, WAL, queries
- `docs/05-deployment-vps.md` — Nginx, UFW, Fail2ban, TLS (fresh VPS checklist)
- `docs/06-operations-runbook.md` — bank file, daily ops
- `docs/07-security.md` — threat model, RBAC
- `docs/08-qa-pilot.md` — test matrix, pilot script
- `docs/09-vps-setup-and-migration.md` — **localhost + new VPS setup, migration, what to copy, one-liner start**

## Production VPS (this host is backend)

- Debian 13 trixie, `cobc 4.0`, `nginx 1.26`, `sqlite3 3.46`, `python 3.13`, `ufw` active 22/80/443, Nginx `limit_req 10r/s` on `/api/`
- `libpayroll.so` 28KB, `<15MB RSS`, 11ms/1k rows, text payslip 794 bytes

See `plan.md` for full checklist, `docs/05-deployment-vps.md` for TLS, and **`docs/09-vps-setup-and-migration.md` for localhost (`http://localhost`, `http://127.0.0.1/app/login.html`) and for moving to any new VPS**.
