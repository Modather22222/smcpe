# 04 — DB Schema (SQLite WAL, money as TEXT)

> Money never float. `TEXT` `"4229010.00"` + `Decimal` in Python, `COMP-3` in COBOL.

## ER (tenant-isolated)

```
tenants 1──∞ employees
        1──∞ users
        1──∞ payroll_runs 1──∞ payroll_lines (emp_id)
               └── fx_snapshot_json + statutory_version (replay)
statutory_tables (version PK)
fx_history (date+currency PK)
audit_log (hash chain)
```

## Tables

- **tenants** `id PK (NA)`, `name`, `plan starter|growth|enterprise`, `created_at`
- **users** `id PK`, `tenant_id FK`, `email UNIQUE`, `password_hash`, `role owner|accountant|viewer`
- **employees** `id PK SD-0042`, `tenant_id FK`, `name`, `national_id`, `hire_date YYYY-MM-DD`, `base_currency SDG|USD|SAR|AED`, `base_salary TEXT "1400.00"`, `allowances TEXT`, `nsif_eligible Y/N`, `bank_account`, `bank_code`
- **fx_history** `date YYYY-MM-DD`, `currency`, `rate TEXT "2610.5000" S9(5)V9(4)`, `source CBOS|locked`, `locked_by`
- **statutory_tables** `version PK v2026.09`, `nsif_emp "0.08"`, `nsif_co "0.17"`, `tax_free "50000.00"`, `tiers_json [{"limit":"100000.00","rate":"0.05"},...]`
- **payroll_runs** `id PK run_2026-09_NA`, `tenant_id`, `period YYYY-MM`, `fx_snapshot_json {"USD":"2610.5000"}`, `statutory_version`, `status draft|computed|approved|posted`, `created_by`, `created_at`
- **payroll_lines** `run_id+emp_id PK`, `gross TEXT`, `nsif_emp`, `nsif_co`, `taxable`, `pit`, `net`, `net_fx`
- **audit_log** `id AUTOINC`, `time`, `actor`, `action FX_LOCK|RUN_CREATE|...`, `hash sha256(prev+payload)`, `payload_json`

Indexes: `idx_employees_tenant`, `idx_runs_tenant_period`, `idx_lines_run`

## WAL & FK

- `PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;` per connection (`backend/db/conn.py`)
- Every query `WHERE tenant_id=:tid` from JWT (tested in `test_tenant_isolation.py`)

## Seed (v2026.09)

```sql
-- statutory
INSERT INTO statutory_tables VALUES ('v2026.09','0.08','0.17','50000.00','[{"limit":"100000.00","rate":"0.05"},...]','2026-09-01');
-- fx 2026-09-25 locked USD 2610.5000 SAR 696.1000 AED 710.8500 + CBOS history
-- employees SD-0042..45 from dashboard/js/data.js:9
```

## Migrate

```
DB_PATH=backend/db/smcpe.db python3 backend/db/migrate.py
# Tables: tenants 2, employees 4, fx_history 9, statutory_tables 1
sqlite3 backend/db/smcpe.db "SELECT * FROM statutory_tables;"
```

Verify: `sqlite3 backend/db/smcpe.db "PRAGMA integrity_check;"` → `ok`, `ls -lh backend/db/smcpe.db` 84K WAL

## Flat files

`backend/data/runs/2026-09/*.txt` mirror `payroll_lines` for COBOL batch + bank export (fixed-width). Created per run, backed up via `ops/scripts/backup.sh`.

## Query examples

```sql
-- NSIF schedule per run
SELECT emp_id, gross, nsif_emp, nsif_co FROM payroll_lines WHERE run_id='run_2026-09_NA';
-- PIT tier
SELECT emp_id, taxable, pit FROM payroll_lines WHERE run_id='run_2026-09_NA';
-- ESG join hire_date
SELECT e.id, e.hire_date, l.net FROM employees e JOIN payroll_lines l ON l.emp_id=e.id WHERE l.run_id='run_2026-09_NA';
```
