-- SMCPE schema — SQLite WAL, money as TEXT (2 decimals), tenant-isolated
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS tenants (
  id TEXT PRIMARY KEY,           -- e.g. NA
  name TEXT NOT NULL,            -- Nile Agro Trading
  plan TEXT NOT NULL CHECK(plan IN ('starter','growth','enterprise')),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('owner','accountant','viewer')),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
  id TEXT PRIMARY KEY,           -- SD-0042
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  national_id TEXT,
  hire_date TEXT NOT NULL,        -- YYYY-MM-DD
  base_currency TEXT NOT NULL CHECK(base_currency IN ('SDG','USD','SAR','AED')),
  base_salary TEXT NOT NULL,      -- "1400.00" string 2 decimals
  allowances TEXT NOT NULL,        -- "220.00"
  nsif_eligible TEXT NOT NULL CHECK(nsif_eligible IN ('Y','N')),
  bank_account TEXT,
  bank_code TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fx_history (
  date TEXT NOT NULL,            -- YYYY-MM-DD
  currency TEXT NOT NULL CHECK(currency IN ('USD','SAR','AED','SDG')),
  rate TEXT NOT NULL,            -- "2610.5000" S9(5)V9(4) string
  source TEXT NOT NULL,          -- CBOS, locked
  locked_by TEXT,
  PRIMARY KEY(date, currency)
);

CREATE TABLE IF NOT EXISTS statutory_tables (
  version TEXT PRIMARY KEY,      -- v2026.09
  nsif_emp TEXT NOT NULL,        -- "0.08"
  nsif_co TEXT NOT NULL,         -- "0.17"
  tax_free TEXT NOT NULL,        -- "50000.00"
  tiers_json TEXT NOT NULL,      -- [{"limit":"100000.00","rate":"0.05"},...]
  published_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payroll_runs (
  id TEXT PRIMARY KEY,           -- run_2026-09_NA
  tenant_id TEXT NOT NULL REFERENCES tenants(id),
  period TEXT NOT NULL,          -- YYYY-MM
  fx_snapshot_json TEXT NOT NULL, -- {"USD":"2610.5000",...}
  statutory_version TEXT NOT NULL REFERENCES statutory_tables(version),
  status TEXT NOT NULL CHECK(status IN ('draft','computed','approved','posted')),
  created_by TEXT REFERENCES users(id),
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payroll_lines (
  run_id TEXT NOT NULL REFERENCES payroll_runs(id) ON DELETE CASCADE,
  emp_id TEXT NOT NULL REFERENCES employees(id),
  gross TEXT NOT NULL,
  nsif_emp TEXT NOT NULL,
  nsif_co TEXT NOT NULL,
  taxable TEXT NOT NULL,
  pit TEXT NOT NULL,
  net TEXT NOT NULL,
  net_fx TEXT,                   -- optional FX net if needed
  PRIMARY KEY(run_id, emp_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  time TEXT NOT NULL,
  actor TEXT NOT NULL,
  action TEXT NOT NULL,          -- FX_LOCK, RUN_CREATE, RUN_COMPUTE, etc
  hash TEXT NOT NULL,            -- sha256(prev_hash+payload)
  payload_json TEXT NOT NULL
);

-- Indexes for tenant isolation
CREATE INDEX IF NOT EXISTS idx_employees_tenant ON employees(tenant_id);
CREATE INDEX IF NOT EXISTS idx_runs_tenant_period ON payroll_runs(tenant_id, period);
CREATE INDEX IF NOT EXISTS idx_lines_run ON payroll_lines(run_id);
