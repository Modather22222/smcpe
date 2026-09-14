# 03 — API Contract (FastAPI + ctypes → libpayroll.so)

> All money as `TEXT` strings `"4229010.00"` 2 decimals, FX as `"2610.5000"` 4 decimals. Every run echoes `fx_snapshot` + `statutory_version` for replay.

## Stack

- FastAPI 0.115 + Uvicorn 2 workers on `127.0.0.1:8000`, proxied via Nginx `/api/` with `limit_req 10r/s`
- `backend/api/payroll_lib.py` — `ctypes.CDLL(libpayroll.so)` + `cob_init` + `PAYROLL__CALC` (57B in, 92B out, `Z...9.99`→`TRIM`), fallback to `Decimal` mirror
- `aiosqlite` WAL + `JWT HS256 15m` + `bcrypt` (72-byte truncate)

## Health

```
GET /api/health → {"ok":true,"lib":"libpayroll.so","lib_exists":true,"version":"v2026.09"}
curl -s http://127.0.0.1/api/health | jq
# via Nginx also works:
curl -s http://127.0.0.1:8000/api/health
```

## Auth

| Method | Path | Body | Returns |
|--------|------|------|---------|
| POST | `/api/auth/login` | `{"email":"owner@nileagro.sd","password":"admin123"}` | `{"access_token":"eyJ...","role":"owner","tenant_id":"NA"}` |
| GET | `/api/employees` | `Header Authorization: Bearer <token>` | `{"employees":[...]}` |

RBAC: `owner` > `accountant` > `viewer`. Every query `WHERE tenant_id=:tid` from JWT.

```
TOKEN=$(curl -s -X POST http://127.0.0.1/api/auth/login -H "Content-Type: application/json" -d '{"email":"owner@nileagro.sd","password":"admin123"}' | jq -r .access_token)
curl -s http://127.0.0.1/api/employees -H "Authorization: Bearer $TOKEN" | jq
```

## Tenants

- `GET /api/tenants`

## Employees

- `GET /api/employees?tenant=NA`
- `POST /api/employees` `{name, hire_date YYYY-MM-DD, base_currency SDG|USD|SAR|AED, base_salary "1400.00", allowances "220.00", nsif_eligible Y/N, bank_account, bank_code}`
- `POST /api/employees/import` `multipart/form-data file=employees.csv` → `{"imported":42,"warnings":3}`
- `GET /api/employees/{id}`

## FX

- `GET /api/fx/history` → `{"history":[{"date":"2026-09-25","currency":"USD","rate":"2610.5000","source":"locked"}]}`
- `GET /api/fx?month=2026-09` → `{"rates":{"USD":"2610.5000",...}}`
- `POST /api/fx/lock` `{"date":"2026-09-25","rates":{"USD":"2610.5000","SAR":"696.1000","AED":"710.8500"}}` (owner/accountant only)

## Payroll Runs

```
POST /api/runs {"period":"2026-09"} → {"run_id":"run_2026-09_NA_abc123","fx_snapshot":{...}}
POST /api/runs/{id}/compute → {"totals":{"gross":"13249742.50",...},"lines":[...],"engine":"cobol"}
POST /api/runs/{id}/approve (owner only) → {"ok":true,"status":"approved"}
GET /api/runs?period=2026-09 → {"runs":[...]}
GET /api/runs/{id} → {"run":{...},"lines":[...]}
```

Compute calls `libpayroll.so` per employee: `gross=(base+allow)*fx` if FX else `+`, NSIF 8/17 if `Y`, `taxable=gross-nsif`, PIT progressive `50k 0% → 100k 5% →200k 10% →400k 15% → >400k 20%`, `net=gross-nsif-pit`. Totals as strings via `Decimal`.

Example totals for 4 demo employees (NA): `gross 13249742.50 nsif_emp 725851.40 nsif_co 1542434.23 taxable 12523891.10 pit 2354778.22 net 10169112.88` (via `compute_payroll`).

## Reports

- `GET /api/reports/nsif?run_id=...` → `{"totals":{"gross":..., "nsif_emp":..., "nsif_co":...}}`
- `GET /api/reports/pit?run_id=...` → `{"rows":[{"emp_id":"SD-0042","taxable":"3890689.20","pit":"740637.84"}]}`
- `GET /api/reports/esg` → `{"esg":[{"id":"SD-0045","years":12.7,"monthly_sdg":"3874132.50","accrual":"738..."}]}` (uses `compute_esg` 0.33/0.5/1/1.5×)
- `GET /api/reports/zakat?run_id=...` → `{"nisab":"100000.00","flagged":[...]}`

## Bank

- `GET /api/bank/file?run_id=...` → `text/plain` fixed-width:
  ```
  H|NA|202609|000004|13249742.50
  D|1002844551|3150051.36|SD-0042|BANKAK
  D|88210042|751420.00|SD-0043|FAISAL
  T|000004|10169112.88|COMP3-EXACT
  ```
- `GET /api/bank/file?run_id=...&format=csv` → `text/csv`

## Payslips

- `GET /api/payslips?run_id=...` → `{"payslips":[...]}`
- `GET /api/payslips/{emp_id}?run_id=...` → `text/plain` 7KB
- `POST /api/payslips/send?run_id=...&emp_id=...` → `{"ok":true,"queued":"SD-0042"}` (stub)

## Statutory

- `GET /api/statutory` → `{"tables":[{"version":"v2026.09","nsif_emp":"0.08",...}]}`
- `POST /api/statutory` `{"version":"v2026.10","tiers_json":"[...]"} ` (owner only, never mutates old runs)

## Audit

- `GET /api/audit?limit=50` → `{"audit":[{"action":"RUN_COMPUTE","hash":"00",...}],"note":"Each run stores FX + statutory_version for replay"}` (hash chain `sha256(prev+payload)`)

## Errors & Validation

- `400` bad `period` regex `^\d{4}-\d{2}$`, FX `S9(5)V9(4)` max `99999.9999`, money regex `^\d+\.\d{2}$`
- `401` missing/invalid `Bearer`
- `403` tenant mismatch or role insufficient
- `404` run/employee not found

## OpenAPI

- `http://127.0.0.1:8000/docs` (Swagger) auto-generated from `schemas.py`
- `curl -s http://127.0.0.1:8000/openapi.json | jq .paths`

## Money contract (pin)

- JSON `str` 2 decimals, never `number`
- DB `TEXT`
- `Decimal(...).quantize(Decimal("0.00"), ROUND_HALF_UP)`
- `COBOL COMP-3` + `ROUNDED` only at NSIF/PIT
- Every `payroll_runs.fx_snapshot_json` + `statutory_version` stored for replay
