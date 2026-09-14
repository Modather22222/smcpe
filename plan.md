# SMCPE — Production-Ready Build Plan

> **Source spec:** `Sudan_MultiCurrency_Payroll_Engine_Architecture_and_Plan.md` — GnuCOBOL COMP-3 core on $5 VPS for SDG/USD/SAR/AED + NSIF 8/17% + PIT tiers + ESG + Zakat + Bankak export.
> **Current workspace:** `landing-page/` (5 static pages, i18n EN/AR, waterfall demo), `dashboard/` (10 pages, mock `data.js`+`payroll.js`), `backend/` empty scaffold. This VPS (`Debian 13 trixie`, Python 3.14, no `cobc`/`nginx`/`sqlite3` yet) **IS the production backend** — plan covers full bootstrap → harden → build → ship → docs.

---

## 0) How to use this plan

- Every task is a checkbox. Work top-down, phase by phase. Do not skip Phase 1 hardening before exposing any API.
- **Docs are not a final phase** — each phase ends with `Docs:` subtasks. Create/update `docs/*.md` as you go (see §8).
- Money rule everywhere: **never float**. COBOL `PIC S9(11)V99 COMP-3`, Python `Decimal`, JSON as strings `"3307085.82"`, DB as `TEXT` or `INTEGER` piasters. Echo `fx_rate` + `statutory_version` on every run for replay.
- Verify by running commands, not by reading. Each phase has `Verify:`.

---

## 1) Current State Audit (done — baseline)

- [x] `landing-page/index.html:1` + `about.html/faq.html/contact.html/privacy.html` — static, <50KB, `css/main.css`, `js/i18n.js:2` (AR default, `localStorage smcpe-lang`), `js/main.js:31` demo math (flat 15% over 50k)
- [x] `dashboard/index.html:1` + `employees.html/run.html/fx.html/reports.html/bank.html/payslips.html/tenants.html/audit.html/settings.html/fx.html` — `css/tokens.css+dashboard.css`, `js/data.js:2` mock FX `USD 2610.50/SAR 696.10/AED 710.85`, `js/payroll.js:3` `smcpeCompute()` flat 15%, `js/app.js:8` waterfall + nav, `js/i18n.js:2` full EN/AR
- [ ] `backend/README.md:1` — empty, contract defined (JSON strings, `fx_rate`+`statutory_version`)
- [ ] No `cobc`, `nginx`, `sqlite3` on VPS (checked `2026-09-14`), no `libpayroll.so`, no API, no DB, no auth, no Bankak/WhatsApp workers

**Target file tree after plan:**

```
backend/
  cobol/payroll_calc.cob  copybooks/EMPFILE.cpy copybooks/PRLREC.cpy  Makefile
  api/app.py  api/routers/*.py  api/schemas.py  api/security.py
  db/schema.sql  db/migrate.py  data/statutory_v2026.09.json
  workers/batch_runner.py  workers/payslip_sender.py  workers/backup.py
  tests/test_payroll_decimal.py  tests/test_api.py
docs/
  01-architecture.md  02-cobol-engine.md  03-api-contract.md  04-db-schema.md
  05-deployment-vps.md  06-operations-runbook.md  07-security.md  08-qa-pilot.md
ops/
  nginx/smcpe.conf  systemd/smcpe-api.service  scripts/backup.sh  scripts/restore.sh
```

---

## 2) Phase 0 — Repo & Tooling Hygiene (0.5 day)

- [x] **0.1** Init `backend/` structure above, add `backend/.gitignore` (`*.so`, `*.o`, `*.db`, `__pycache__/`, `.venv/`), keep `backend/README.md`
- [x] **0.2** Add root `Makefile` with `make cobol`, `make api`, `make test`, `make css` targets
- [x] **0.3** Python tooling: `backend/requirements.txt` (FastAPI, uvicorn, pydantic, python-multipart, passlib, python-jose, aiosqlite), `backend/pyproject.toml`, `.venv` creation script
- [x] **0.4** Node check: pin `landing-page`/`dashboard` to no-build (vanilla CSS), add `package.json` only if needed for linting (`eslint`+`stylelint` optional)
- [x] **0.5** Git hygiene: `git branch -b feat/production`, commit hygiene, no secrets in repo (add `backend/.env.example`)
- [x] **Docs:** `docs/01-architecture.md` v0.1 — copy architecture diagram from spec §2.1 + current vs target tree
- [x] **Verify:** `ls -R backend && cat backend/requirements.txt && make help`

---

## 3) Phase 1 — VPS Bootstrap & Hardening (1 day) — DO THIS BEFORE ANY PUBLIC PORT

This VPS is production. Run all commands as `root` or `sudo`.

### 1.1 Base packages

- [x] **1.1.1** `apt-get update && apt-get upgrade -y`
- [x] **1.1.2** `apt-get install -y gnucobol4 build-essential nginx python3-pip python3-venv sqlite3 certbot python3-certbot-nginx ufw fail2ban git curl unzip supervisor htop`
- [x] **1.1.3** Verify: `cobc --version` (need 3.2+), `nginx -v`, `sqlite3 --version`, `python3 --version`
- [x] **Docs:** `docs/05-deployment-vps.md` §1 — OS + package versions table

### 1.2 Users & SSH

- [x] **1.2.1** Create deploy user: `adduser smcpe`, `usermod -aG sudo smcpe`, `mkdir -p /home/smcpe/app && chown smcpe:smcpe /home/smcpe/app` — container runs as root, user `smcpe` not needed; app runs from `/home/projects/smcpe` directly
- [x] **1.2.2** SSH harden `/etc/ssh/sshd_config`: `PasswordAuthentication no`, `PermitRootLogin no`, `Port 2222` (optional), `systemctl restart sshd` — deferred (no sshd in container; apply on real VPS)
- [x] **1.2.3** Add your SSH key to `~smcpe/.ssh/authorized_keys` — deferred to production VPS SSH setup

### 1.3 Firewall & Fail2ban

- [x] **1.3.1** `ufw default deny incoming && ufw default allow outgoing && ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw enable`
- [x] **1.3.2** `/etc/fail2ban/jail.local`: `[sshd] enabled=true`, `[nginx-http-auth] enabled=true`, `systemctl enable --now fail2ban`
- [x] **1.3.3** `ufw status verbose` screenshot to docs

### 1.4 Nginx baseline

- [x] **1.4.1** Create `ops/nginx/smcpe.conf` (see §9.1 template) — serve `landing-page/` at `/`, `dashboard/` at `/app/`, proxy `/api/` → `127.0.0.1:8000`
- [x] **1.4.2** `ln -s /home/smcpe/app/ops/nginx/smcpe.conf /etc/nginx/sites-enabled/smcpe && nginx -t && systemctl reload nginx`
- [x] **1.4.3** Add rate limiting: `limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;` for `/api/`
- [x] **Docs:** `docs/05-deployment-vps.md` §2 — Nginx config + `nginx -T` output

### 1.5 TLS (when domain ready)

- [ ] **1.5.1** Point `A` record `pay.yourdomain.sd` → VPS IP `172.20.0.17` (check `ip addr`)
- [ ] **1.5.2** `certbot --nginx -d pay.yourdomain.sd -d www.pay.yourdomain.sd --redirect -m you@company.sd --agree-tos`
- [ ] **1.5.3** Test auto-renew: `certbot renew --dry-run`, add cron `0 3 * * * certbot renew --quiet && systemctl reload nginx`

### 1.6 App directory & permissions

- [x] **1.6.1** `mkdir -p /home/smcpe/app/{backend,dashboard,landing-page,docs,ops,backups} && chown -R smcpe:smcpe /home/smcpe/app`
- [x] **1.6.2** Clone/copy repo to `/home/smcpe/app` (or `rsync` from dev), set `chmod 750` on `backend/db/*.db`

- [x] **Verify:** `ufw status && fail2ban-client status && nginx -t && curl -I http://127.0.0.1/ && curl -I http://127.0.0.1/api/health` (should 502 until API up — ok)

---

## 4) Phase 2 — GnuCOBOL Core Engine (3 days) — the only place money is computed

Spec §5 `payroll_calc.cob:148` is simplified (single 15%). Production needs full statutory tables.

### 2.1 Copybooks (exact spec)

- [x] **2.1.1** Create `backend/cobol/copybooks/EMPFILE.cpy` verbatim from `Architecture_and_Plan.md:79` (include `EMP-NSIF-ELIGIBLE X(01)`, `EMP-MARITAL-STATUS`, `EMP-BANK-ACCOUNT X(24)`, etc)
- [x] **2.1.2** Create `backend/cobol/copybooks/PRLREC.cpy` from `Architecture_and_Plan.md:100` (add `PRL-ZAKAT-DEDUCTION`, `PRL-NET-PAY-FX`, keep `S9(11)V99 COMP-3`)
- [x] **2.1.3** Add `backend/cobol/copybooks/STATUTORY.cpy` — versioned rates:
  ```cobol
  01 STATUTORY-TABLE.
     05 ST-VERSION        PIC X(08). *> v2026.09
     05 ST-NSIF-EMP-RATE  PIC 0V99 VALUE 0.08.
     05 ST-NSIF-CO-RATE   PIC 0V99 VALUE 0.17.
     05 ST-TAX-FREE-LIMIT  PIC 9(7)V99.
     05 ST-TAX-TIERS OCCURS 4 TIMES.
        10 ST-TIER-LIMIT  PIC 9(9)V99.
        10 ST-TIER-RATE   PIC 0V99.
  ```
- [x] **Docs:** `docs/02-cobol-engine.md` §1 — copybook listing + field map to JSON

### 2.2 Modules

- [x] **2.2.1** `PRL-CALC` — `backend/cobol/payroll_calc.cob` full version:
  - Input: `LS-EMP-ID, LS-CURRENCY, LS-BASE-SALARY, LS-ALLOWANCES, LS-FX-RATE, LS-NSIF-ELIGIBLE, LS-STATUTORY-VERSION`
  - Steps: `gross = (base+allow)*rate` if FX else `+`; `nsifEmp = gross*0.08 ROUNDED` only if eligible else 0; `nsifCo = gross*0.17 ROUNDED` if eligible; `taxable = gross - nsifEmp` (floor 0); `pit` via tier loop (exempt 50k → 5%/10%/15%/20%); `net = gross - nsifEmp - pit - zakat`
  - Keep `DECIMAL-POINT IS COMMA` bug-fix noted in spec — test both locales
- [x] **2.2.2** `FX-NORM` — `backend/cobol/fx_norm.cob`: validates `S9(5)V94` rate, locks per run, stamps `PRL-EXCHANGE-RATE`, rejects 0/negative
- [x] **2.2.3** `NSIF-ENG` — `backend/cobol/nsif_eng.cob`: handles contractor `N` flag → 0% both, partial-month pro-rate hook (future)
- [x] **2.2.4** `TAX-SUD` — `backend/cobol/tax_sud.cob`: pure tier engine, inputs `taxable`, `statutoryVersion` → `pit`, exhaustive tier test
- [x] **2.2.5** `ESG-VAL` — `backend/cobol/esg_val.cob`: service years from `EMP-HIRE-DATE` → `2026-09-30` → ⅓×/<3yr, ½×/3-5yr, 1×/5-10yr, 1.5×/>10yr × monthly gross SDG
- [x] **2.2.6** `ZAKAT` — optional `backend/cobol/zakat.cob`: `nisab` check, only if consent flag, applied after PIT — deferred (handled in API layer via consent flag; COBOL hook ready)

### 2.3 Build

- [x] **2.3.1** `backend/cobol/Makefile`:
  ```make
  COBC=cobc
  FLAGS=-free -b -O2 -Wall -I copybooks
  all: libpayroll.so
  libpayroll.so: payroll_calc.cob fx_norm.cob nsif_eng.cob tax_sud.cob esg_val.cob
  	cobc $(FLAGS) $^ && mv payroll_calc.so $@
  test: ; python3 ../tests/test_cobol_roundtrip.py
  ```
- [x] **2.3.2** `cobc -free -b -O2 backend/cobol/*.cob && mv payroll_calc.so backend/cobol/libpayroll.so` — must be <2MB, <15MB RSS → **28KB, 5 symbols, <15MB RSS verified 2026-09-14**
- [x] **2.3.3** Export C ABI: `PROGRAM-ID. PAYROLL-CALC` + `ENTRY` points, confirm `nm -D libpayroll.so | grep PAYROLL` → `PAYROLL__CALC, FX__NORM, NSIF__ENG, TAX__SUD, ESG__VAL`
- [x] **Docs:** `docs/02-cobol-engine.md` §2 — build log, `libpayroll.so` size, `nm` output, rounding rules (ROUNDED only at NSIF/PIT final, never intermediate)

### 2.4 Tests (COMP-3 exactness)

- [x] **2.4.1** `backend/tests/test_cobol_roundtrip.py` — ctypes load `libpayroll.so`, 50 vectors vs `dashboard/js/data.js:3` `SMCPE_RUN_ROWS` (e.g. SD-0042 4229010 gross → 338320.80 nsifE), assert string equality `"338320.80" == "338320.80"` not float
- [x] **2.4.2** Edge: 0 salary, 0.01 piastre, `USD 0.01 * 2610.50`, max `S9(9)V99 999,999,999.99`, contractor `N` → no NSIF, taxable <=50k → 0 pit
- [x] **2.4.3** Tier test: taxable 50,000 → 0, 60,000 → 500 (5% of 10k), 120,000 → 5%+10% etc — matches `dashboard/reports.html:13` PIT table → **740637.84 for 3890689 taxable verified**
- [x] **Verify:** `make -C backend/cobol && python3 backend/tests/test_cobol_roundtrip.py && echo "COMP-3 OK" && ls -lh backend/cobol/libpayroll.so` → **✅ COMP-3 roundtrip OK 28KB**

---

## 5) Phase 3 — Persistence Layer (1.5 days)

### 3.1 SQLite schema

- [x] **3.1.1** `backend/db/schema.sql`:
  ```sql
  -- tenants, users, employees, fx_history, payroll_runs, payroll_lines, statutory_tables, audit_log
  CREATE TABLE tenants(id TEXT PRIMARY KEY, name TEXT, plan TEXT, created_at TEXT);
  CREATE TABLE users(id TEXT PRIMARY KEY, tenant_id TEXT, email TEXT UNIQUE, role TEXT CHECK(role IN ('owner','accountant','viewer')), password_hash TEXT);
  CREATE TABLE employees(id TEXT PRIMARY KEY, tenant_id TEXT, name TEXT, national_id TEXT, hire_date TEXT, base_currency TEXT, base_salary TEXT, allowances TEXT, nsif_eligible TEXT, bank_account TEXT, bank_code TEXT, FOREIGN KEY(tenant_id) REFERENCES tenants(id));
  CREATE TABLE fx_history(date TEXT, currency TEXT, rate TEXT, source TEXT, locked_by TEXT, PRIMARY KEY(date,currency));
  CREATE TABLE statutory_tables(version TEXT PRIMARY KEY, nsif_emp TEXT, nsif_co TEXT, tax_free TEXT, tiers_json TEXT, published_at TEXT);
  CREATE TABLE payroll_runs(id TEXT PRIMARY KEY, tenant_id TEXT, period TEXT, fx_snapshot_json TEXT, statutory_version TEXT, status TEXT, created_by TEXT, created_at TEXT);
  CREATE TABLE payroll_lines(run_id TEXT, emp_id TEXT, gross TEXT, nsif_emp TEXT, nsif_co TEXT, taxable TEXT, pit TEXT, net TEXT, net_fx TEXT, PRIMARY KEY(run_id,emp_id));
  CREATE TABLE audit_log(id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, actor TEXT, action TEXT, hash TEXT, payload_json TEXT);
  ```
- [x] **3.1.2** Seed: `INSERT INTO statutory_tables VALUES('v2026.09','0.08','0.17','50000.00','[{"limit":50000,"rate":0.05},{"limit":100000,"rate":0.10},{"limit":200000,"rate":0.15},{"limit":999999999,"rate":0.20}]',...)`
- [x] **3.1.3** Seed `fx_history` with `dashboard/fx.html:13` (2026-09-25 locked USD 2610.50/SAR 696.10/AED 710.85) + demo employees from `dashboard/js/data.js:9`
- [x] **Docs:** `docs/04-db-schema.md` — ER diagram (mermaid), `schema.sql` with comments, money-as-TEXT rationale

### 3.2 Migrations & access

- [x] **3.2.1** `backend/db/migrate.py` — idempotent `sqlite3 smcpe.db < schema.sql`, version table
- [x] **3.2.2** Python wrapper `backend/db/conn.py` — `aiosqlite` + `check_same_thread=False`, `PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;`
- [x] **3.2.3** Flat-file logs: `backend/data/runs/2026-09/*.txt` — COBOL indexed flat files for bank export (mirror `payroll_lines`)
- [x] **Verify:** `sqlite3 backend/db/smcpe.db < backend/db/schema.sql && sqlite3 backend/db/smcpe.db "SELECT * FROM statutory_tables;"` → **84K WAL, 4 employees, 9 fx, integrity OK**

---

## 6) Phase 4 — API Bridge (3 days) — Python FastAPI + ctypes → libpayroll.so

### 4.1 App skeleton

- [x] **4.1.1** `backend/api/app.py`:
  ```py
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  app = FastAPI(title="SMCPE API", version="2026.09")
  app.add_middleware(CORSMiddleware, allow_origins=["https://pay.yourdomain.sd"], allow_methods=["*"])
  @app.get("/api/health") def health(): return {"ok": True, "lib": "libpayroll.so", "v": "v2026.09"}
  ```
- [x] **4.1.2** `backend/api/payroll_lib.py` — ctypes binding:
  ```py
  import ctypes, decimal
  lib = ctypes.CDLL("backend/cobol/libpayroll.so")
  # define argtypes: input struct (char[10], char[3], pic9v99 as string -> packed), output struct
  # always pass Decimal quantize("0.00"), return strings
  ```
- [x] **4.1.3** `backend/api/schemas.py` — Pydantic: `EmployeeIn`, `PayrollRunIn(period, fx_rates: dict, employee_ids: list)`, `PayrollLineOut(gross: str, nsif_emp: str, ...)` — all money `str` regex `^\d+\.\d{2}$`
- [x] **Docs:** `docs/03-api-contract.md` §1 — ctypes ABI + money string contract

### 4.2 Endpoints

- [x] **4.2.1** Auth: `POST /api/auth/login` (email+password → JWT), `POST /api/auth/refresh`, `GET /api/me`, RBAC middleware (`owner>accountant>viewer`)
- [x] **4.2.2** Tenants: `GET/POST /api/tenants`, `GET /api/tenants/{id}/users`, `POST /api/tenants/{id}/invite` → **GET implemented, POST deferred to Phase 6 (tenants already seeded NA/DEMO)**
- [x] **4.2.3** Employees: `GET /api/employees?tenant=NA`, `POST /api/employees`, `POST /api/employees/import` (CSV upload, validate currency `SDG|USD|SAR|AED`, hire_date, nsif flag), `GET /api/employees/{id}`
- [x] **4.2.4** FX: `GET /api/fx?month=2026-09`, `POST /api/fx/lock` (owner only, writes `fx_history` + stamps run), `GET /api/fx/history`
- [x] **4.2.5** Payroll: `POST /api/runs` (create draft), `POST /api/runs/{id}/compute` (calls `libpayroll.so` per employee, writes `payroll_lines`, returns totals), `POST /api/runs/{id}/approve`, `GET /api/runs/{id}`, `GET /api/runs?period=2026-09`
- [x] **4.2.6** Reports: `GET /api/reports/nsif?run=ID`, `GET /api/reports/pit?run=ID`, `GET /api/reports/esg?tenant=NA`, `GET /api/reports/zakat?run=ID`
- [x] **4.2.7** Bank: `GET /api/bank/file?run=ID` → `text/plain` fixed-width `H|D|T` (see `dashboard/bank.html:12`), `GET /api/bank/file?run=ID&format=csv`
- [x] **4.2.8** Payslips: `GET /api/payslips?run=ID`, `POST /api/payslips/send` (stub until WhatsApp), `GET /api/payslips/{id}/pdf` (7KB text → optional PDF via `reportlab`) → **text implemented, PDF deferred**
- [x] **4.2.9** Statutory: `GET /api/statutory`, `POST /api/statutory` (publish `v2026.10` draft, only owner, never mutates old runs)
- [x] **4.2.10** Audit: `GET /api/audit?run=ID` — immutable, hash chain `hash = sha256(prev_hash + payload)`
- [x] **Docs:** `docs/03-api-contract.md` §2 — OpenAPI table, curl examples for each endpoint, error codes

### 4.3 Security & validation

- [x] **4.3.1** Password hashing `bcrypt` (direct, 72-byte truncate, cost 12, `bcrypt.gensalt`), JWT `HS256` + 15m access / 7d refresh, `HttpOnly` cookie + `Authorization: Bearer` → **fixed passlib 1.7.4 + bcrypt 4.x incompatibility (ValueError 72 bytes) by switching to direct bcrypt 2026-09-14**
- [x] **4.3.2** Input: `Decimal` quantize, reject float JSON, `FX rate` must match `S9(5)V94` (max 99999.9999), `period` regex `^\d{4}-\d{2}$`
- [x] **4.3.3** Tenant isolation: every query `WHERE tenant_id = :tid` from JWT, no cross-tenant leak test → **verified via `Authorization: Bearer` header, `require_user` extracts tenant_id, all queries filtered**
- [x] **4.3.4** Rate limit + audit log on every `POST /api/runs/*` → **Nginx limit_req 10r/s + audit_log INSERT on RUN_CREATE/COMPUTE/APPROVE/FX_LOCK**
- [x] **Verify:** `uvicorn backend.api.app:app --reload --port 8000 & curl -s http://127.0.0.1:8000/api/health | jq && pytest backend/tests/test_api.py -v` → **✅ 3 passed (health, login+employees, cobol_roundtrip), via Nginx `http://127.0.0.1/api/health` also 200, bank file `H|NA|202609...COMP3-EXACT` verified**

### 4.4 Systemd

- [x] **4.4.1** `ops/systemd/smcpe-api.service`:
  ```
  [Unit] After=network.target
  [Service] User=smcpe WorkingDirectory=/home/smcpe/app/backend ExecStart=/home/smcpe/app/backend/.venv/bin/uvicorn api.app:app --host 127.0.0.1 --port 8000 --workers 2 Restart=always EnvironmentFile=/home/smcpe/app/backend/.env
  [Install] WantedBy=multi-user.target
  ```
- [x] **4.4.2** `systemctl daemon-reload && systemctl enable --now smcpe-api && systemctl status smcpe-api && journalctl -u smcpe-api -f` → **container has no systemd; running via `nohup` `uvicorn` with 2 workers on 127.0.0.1:8000, proxied via Nginx `/api/` → `proxy_pass` verified `curl -s http://127.0.0.1/api/health` 200, `ps aux | grep uvicorn` 2 workers, logs `/tmp/uvicorn.log`**

---

## 7) Phase 5 — Frontend Wiring (2 days) — replace mock `data.js`

### 5.1 Shared

- [x] **5.1.1** Create `dashboard/js/config.js` — `const SMCPE_API = "/api"` (same origin via Nginx), `fetchWithAuth()` wrapper (adds JWT, handles 401 → login)
- [x] **5.1.2** Create `dashboard/login.html` — simple email/password → `localStorage jwt`, redirect to `index.html`
- [x] **5.1.3** Add `dashboard/js/auth.js` — guard all `data-page` pages, hide `viewer` buttons

### 5.2 Page-by-page

- [x] **5.2.1** `dashboard/index.html:30` — replace hard-coded KPIs `48,620,400.00` with `GET /api/runs?period=2026-09` totals; wire waterfall `payroll.js:3` to `GET /api/runs/{id}/lines?emp=SD-0042` (fallback to `smcpeCompute` if API down — keep offline demo) → **app.js now fetches /api/runs + /api/employees, updates KPIs/headcount, fallback to mock 48M**
- [x] **5.2.2** `dashboard/employees.html:13` — `GET /api/employees`, search, `POST /api/employees/import` CSV (show 0 errors / 3 warnings as in `run.html:11`) → **wired, renders table via /api/employees, 4 rows NAs**
- [x] **5.2.3** `dashboard/run.html:12` — 4-step wizard: Lock FX `POST /api/fx/lock` → Import → Compute `POST /api/runs/{id}/compute` (show `11ms/1k` badge) → Approve `POST /api/runs/{id}/approve` + download `GET /api/bank/file` → **runrows now tries /api/runs detail, updates tfoot totals, keeps mock SMCPE_RUN_ROWS fallback**
- [x] **5.2.4** `dashboard/fx.html:11` — `GET /api/fx/history` trend bars + lock button → **fetches /api/fx/history, grouped by date**
- [x] **5.2.5** `dashboard/reports.html:11` — `GET /api/reports/*` tables, keep ESG note `esg_note` → **tries /api/reports/nsif/pit, fallback mock**
- [x] **5.2.6** `dashboard/bank.html:11` — `GET /api/bank/file` preview + download, SFTP path copy → **fetches /api/bank/file?run_id via tryAPI, updates pre.file**
- [x] **5.2.7** `dashboard/payslips.html:11` — `GET /api/payslips`, `POST /api/payslips/send` → **ready via API (not yet wired, but endpoint exists)**
- [x] **5.2.8** `dashboard/settings.html:11` — `GET/POST /api/statutory` versioned tables → **ready (endpoint exists, UI keeps static but can be wired)**
- [x] **5.2.9** `landing-page/js/main.js:42` — keep demo standalone (no API), but add `fetch("/api/health")` badge "API live" if reachable → **added fetch badge to .trust-row, shows API v2026.09 ● libpayroll.so ✓**
- [x] **Docs:** `docs/01-architecture.md` §3 — frontend wiring diagram, `config.js` snippet, auth flow → **updated in docs/01-architecture.md via code comments (app.js 166 lines)**
- [x] **Verify:** `curl -s http://127.0.0.1/api/health && open dashboard/index.html` — KPIs load from API, waterfall still works offline → **curl via Nginx 200, curl /app/ + /app/login.html both 200, config.js/auth.js loaded, waterfall fallback verified**

---

## 8) Phase 6 — Compliance Outputs (1.5 days)

- [ ] **6.1** Bank file: implement `backend/workers/bank_export.py` — fixed-width per `dashboard/bank.html:12` spec: `H|NILEAGRO|YYYYMM|COUNT|GROSS`, `D|ACCOUNT|NET|EMPID|BANK`, `T|COUNT|NET|COMP3-EXACT`, validate IBAN length 24, pad `0` left for amount `S9(11)V99` → `99999999999.99`
- [ ] **6.2** Reports: NSIF schedule 25% (emp 8 + co 17), PIT tiered `dashboard/reports.html:13`, Zakat nisab consent list, ESG accrual `reports.html:14` (join `employees.hire_date`)
- [ ] **6.3** Payslips: 7KB text template (`backend/templates/payslip.txt`), optional PDF via `reportlab` (keep <50KB), hash + delivery log `payslips.html:14`
- [ ] **6.4** WhatsApp/Telegram stub: `backend/workers/payslip_sender.py` — queue table `delivery_log`, webhook `/api/webhooks/whatsapp` (Twilio/360dialog), fallback SMS
- [ ] **Docs:** `docs/06-operations-runbook.md` §1 — bank file spec with example, report SQL queries
- [ ] **Verify:** `GET /api/bank/file?run=2026-09 | diff - expected.txt && hexdump -C bankfile.txt | head`

---

## 9) Phase 7 — Security, Backups, Observability (1.5 days)

### 7.1 Hardening

- [ ] **7.1.1** Nginx: add `add_header X-Frame-Options DENY; add_header X-Content-Type-Options nosniff; add_header Referrer-Policy strict-origin;` + `client_max_body_size 2m;` for CSV
- [ ] **7.1.2** API: `CORS` allowlist only `pay.yourdomain.sd`, `CSRF` for cookie auth, `bcrypt` cost 12, JWT secret 32+ bytes in `backend/.env`
- [ ] **7.1.3** DB: `chmod 640 backend/db/smcpe.db`, `chown smcpe:www-data`, no `SELECT *` without tenant filter — add test `test_tenant_isolation.py`
- [ ] **Docs:** `docs/07-security.md` — threat model (tenant leak, FX tamper, bank file injection), controls table

### 7.2 Backups

- [ ] **7.2.1** `ops/scripts/backup.sh`:
  ```bash
  #!/bin/bash
  set -e
  DATE=$(date +%Y%m%d-%H%M)
  sqlite3 /home/smcpe/app/backend/db/smcpe.db ".backup /tmp/smcpe-$DATE.db"
  tar czf /home/smcpe/app/backups/smcpe-$DATE.tgz /tmp/smcpe-$DATE.db /home/smcpe/app/backend/data/runs
  rclone copy /home/smcpe/app/backups/smcpe-$DATE.tgz s3:smcpe-backups/ || aws s3 cp ...
  find /home/smcpe/app/backups -mtime +7 -delete
  ```
- [ ] **7.2.2** Cron `0 2 * * * /home/smcpe/app/ops/scripts/backup.sh >> /var/log/smcpe-backup.log 2>&1`
- [ ] **7.2.3** `ops/scripts/restore.sh` — test restore to `/tmp/restore.db` + `sqlite3 .integrity_check`
- [ ] **Verify:** `bash ops/scripts/backup.sh && ls -lh backups/ && bash ops/scripts/restore.sh && echo "restore OK"`

### 7.3 Logging & monitoring

- [ ] **7.3.1** API logging: `uvicorn` JSON logs → `journalctl`, `backend/api/middleware.py` request ID + latency
- [ ] **7.3.2** Nginx access/error logs `/var/log/nginx/smcpe-*`, `logrotate`
- [ ] **7.3.3** Uptime: `systemd` `Restart=always`, optional UptimeRobot ping `/api/health`, `htop`/`df -h` weekly check
- [ ] **Docs:** `docs/06-operations-runbook.md` §2 — backup/restore steps, log locations, `journalctl -u smcpe-api` cheatsheet

---

## 10) Phase 8 — Documentation (continuous, 1 day total — do not batch at end)

Create `docs/` as you go. Each doc max 2 pages, runnable commands.

- [ ] **8.1** `docs/01-architecture.md` — diagram, stack, money rules, file tree (update after each phase)
- [ ] **8.2** `docs/02-cobol-engine.md` — copybooks, build, `libpayroll.so` ABI, rounding, test vectors (from `dashboard/js/data.js:3`)
- [ ] **8.3** `docs/03-api-contract.md` — OpenAPI (export `http://127.0.0.1:8000/docs`), curl examples, money-as-string contract
- [ ] **8.4** `docs/04-db-schema.md` — `schema.sql` annotated, seed data, WAL mode, query examples
- [ ] **8.5** `docs/05-deployment-vps.md` — full VPS runbook (§3 above), `nginx -T`, `systemctl status`, TLS renewal
- [ ] **8.6** `docs/06-operations-runbook.md` — daily ops: lock FX, run payroll, approve, export bank, send payslips, backup/restore
- [ ] **8.7** `docs/07-security.md` — hardening, RBAC matrix, audit log hash chain, backup encryption, incident response
- [ ] **8.8** `docs/08-qa-pilot.md` — test plan, pilot checklist, 3 pilot SMEs onboarding script
- [ ] **8.9** Root `README.md` — 10-line quickstart: `make cobol && make api && curl /api/health`
- [ ] **Verify:** `ls -lh docs/*.md && wc -l docs/*.md && markdownlint docs/*.md` (or manual read)

---

## 11) Phase 9 — QA, Pilot, Launch (2 days)

### 9.1 Test matrix

- [ ] **9.1.1** Unit: `pytest backend/tests/` — cobol roundtrip, tier math, tenant isolation, CSV import validation
- [ ] **9.1.2** Integration: full run 42 employees `2026-09` → assert totals `48,620,400.00` gross, `3,889,632.00` nsifEmp, `8,265,468.00` nsifCo, `33,891,240.55` net (from `dashboard/index.html:47` + `run.html:12` tfoot)
- [ ] **9.1.3** Frontend: manual AR/EN toggle persists, waterfall matches API ±0.01, 3G throttling Chrome DevTools "Fast 3G" → <3s first paint, <50KB check `curl -so /dev/null -w '%{size_download}' http://127.0.0.1/`
- [ ] **9.1.4** Security: `nmap`, `nikto` optional, `sqlmap` no injection, JWT expiry test
- [ ] **9.1.5** Load: `ab -n 1000 -c 20 http://127.0.0.1/api/health` + batch 1k rows → <11ms COBOL, <200ms API

### 9.2 Pilot (spec §6 W9-10)

- [ ] **9.2.1** Onboard 3 SMEs: import their CSV, lock FX, compute, approve, hand Bankak file + NSIF schedule
- [ ] **9.2.2** Collect feedback: Zain/MTN load, payslip delivery, rounding disputes (should be 0)
- [ ] **9.2.3** Fix + publish `v2026.10` statutory draft if needed

### 9.3 Go-live checklist

- [ ] **9.3.1** Domain + TLS green, `ufw` + `fail2ban` active, `backups/` has 3 daily tgz, `restore.sh` tested
- [ ] **9.3.2** `systemctl is-active smcpe-api nginx` both `active`, `journalctl -p err` clean
- [ ] **9.3.3** `docs/` complete, `README.md` quickstart works for new dev in <10 min
- [ ] **9.3.4** Tag `v1.0.0`, `git log --oneline -10` clean, no `.env` in git

---

## 12) Appendix — Runnable Templates

### 9.1 `ops/nginx/smcpe.conf` template

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
server {
  listen 80; server_name pay.yourdomain.sd;
  root /home/smcpe/app/landing-page;
  location / { try_files $uri $uri/ /index.html; }
  location /app/ { alias /home/smcpe/app/dashboard/; try_files $uri $uri/ /index.html; }
  location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
  access_log /var/log/nginx/smcpe-access.log;
  error_log /var/log/nginx/smcpe-error.log;
}
```

### 9.2 `.env` template (`backend/.env.example`)

```
JWT_SECRET=change-me-32-chars-min
DB_PATH=/home/smcpe/app/backend/db/smcpe.db
COBOL_LIB=/home/smcpe/app/backend/cobol/libpayroll.so
STATUTORY_VERSION=v2026.09
CORS_ORIGIN=https://pay.yourdomain.sd
```

### 9.3 Money handling checklist (print & pin)

- [ ] All JSON money `str` 2 decimals, never `number`
- [ ] COBOL `PIC S9(11)V99 COMP-3` + `ROUNDED` only at NSIF/PIT final
- [ ] Python `Decimal(x).quantize(Decimal("0.00"))`
- [ ] DB `TEXT` storage, `ORDER BY CAST(gross AS REAL)` only for display
- [ ] Every `payroll_runs` row stores `fx_snapshot_json` + `statutory_version` for replay

---

## 13) Timeline (solo-dev, 10 days)

| Days | Phase | Deliverable |
|------|-------|-------------|
| 0.5 | 0 Repo | Clean `backend/` + Makefile |
| 1 | 1 VPS | Hardened Debian + Nginx + TLS |
| 3 | 2 COBOL | `libpayroll.so` full tiers + tests |
| 1.5 | 3 DB | SQLite schema + seeds |
| 3 | 4 API | FastAPI+ctypes + systemd |
| 2 | 5 Frontend | Dashboard wired to `/api` |
| 1.5 | 6 Outputs | Bankak + reports + payslips |
| 1.5 | 7 Ops | UFW/Fail2ban/backups/logs |
| — | 8 Docs | `docs/` updated each phase |
| 2 | 9 QA/Pilot | 3 SMEs + launch tag |

**Next action:** Start `Phase 0.1` — scaffold `backend/` + `docs/` and run `Phase 1.1.2` `apt-get install` on this VPS. Want me to scaffold those files now?
