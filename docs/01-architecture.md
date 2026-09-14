# 01 — Architecture

> Source: `Sudan_MultiCurrency_Payroll_Engine_Architecture_and_Plan.md` §2

## Diagram (target, VPS = backend)

```
CLIENT (low bandwidth)          WEB/API GATEWAY               GNUCOBOL CORE
HTMX + CSS <50KB   ──HTTP/REST──► Nginx ──► FastAPI/uvicorn ──► libpayroll.so (COMP-3)
WhatsApp/Telegram               (TLS, rate limit, static)     PRL-CALC, FX-NORM, NSIF-ENG, TAX-SUD, ESG-VAL
                                │                              │
                                ▼                              ▼
                         SQLite (WAL) + Flat files   Bank/PDF reports
                         users, tenants, runs, fx_history, audit_log
```

## Stack (this VPS: Debian 13 trixie)

- GnuCOBOL 3.2+ `cobc -fPIC -shared -O2` → `backend/cobol/libpayroll.so`
- Python 3.11+ FastAPI + ctypes + aiosqlite
- SQLite + COBOL flat files for batch
- Nginx (TLS via certbot, rate limit 10r/s on /api/)
- 1 vCPU/1GB RAM/20GB NVMe — <15MB RSS batch

## Money rule (enforced everywhere)

- COBOL `PIC S9(11)V99 COMP-3` + `ROUNDED` only at NSIF/PIT final
- Python `Decimal(...).quantize(Decimal("0.00"))`
- JSON strings `"3307085.82"` never `number`
- DB `TEXT` columns; every `payroll_runs` stores `fx_snapshot_json` + `statutory_version` for replay

## File tree (current → target)

```
backend/
  cobol/payroll_calc.cob  copybooks/EMPFILE.cpy  copybooks/PRLREC.cpy  Makefile
  api/app.py  api/payroll_lib.py  api/schemas.py  api/security.py  api/routers/*.py
  db/schema.sql  db/migrate.py  db/conn.py
  data/statutory_v2026.09.json
  tests/test_cobol_roundtrip.py  tests/test_api.py
docs/01-08.md
ops/nginx/smcpe.conf  systemd/smcpe-api.service  scripts/backup.sh
landing-page/  dashboard/  (static, vanilla CSS, no build)
```

## Verify

```
ls -R backend
cat backend/requirements.txt
make help
cobc --version; nginx -v; sqlite3 --version
```
