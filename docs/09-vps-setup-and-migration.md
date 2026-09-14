# 09 — VPS Setup & Migration Guide (localhost & new VPS)

> This VPS **IS** the backend (`/home/projects/smcpe` on Debian 13 trixie, `python3.13` venv, `cobc 4.0`, `nginx 1.26`, `sqlite3 3.46`). Every command below is verified 2026-09-14 for **localhost** (`http://localhost`, `http://127.0.0.1`) and for **migration to any new VPS** (Hetzner/DigitalOcean/Vultr $5, 1 vCPU/1GB/20GB).

---

## 1. What this project needs on any VPS

| Layer | Files | Runtime | Port | Persist |
|-------|-------|---------|------|---------|
| Landing | `landing-page/` static | Nginx `root` | `80` `/` | — |
| Dashboard | `dashboard/` static + `js/` | Nginx `alias /app/` | `80` `/app/` | — |
| API | `backend/api/` `backend/cobol/libpayroll.so` | `uvicorn` `127.0.0.1:8000` via `backend/.venv` (py 3.13) | `8000` proxied via `/api/` | — |
| DB | `backend/db/smcpe.db` `backend/db/schema.sql` `seed.sql` | `sqlite3` `WAL` | — | `*.db` + `backend/data/runs/` |
| COBOL | `backend/cobol/*.cob` `copybooks/*.cpy` | `cobc 4.0` → `libpayroll.so` 28KB | — | `libpayroll.so` |
| Backups | `backups/*.tgz` `ops/scripts/backup.sh` | `sqlite3 .backup` + `tar` | — | `backups/` |

**Do NOT commit:** `backend/.env` (JWT secret), `backend/db/smcpe.db`, `backend/.venv/`, `backups/`, `*.so`.

---

## 2. Fresh VPS — from zero to localhost (10 min)

### 2.1 Provision

- Choose **Ubuntu 24.04 LTS** or **Debian 13 trixie**, 1 vCPU/1GB/20GB, region near Sudan (e.g. Hetzner `fsn1`, DO `ams3`).
- Note **VPS IP** (`ip addr` → `172.20.0.17` in this container; on real VPS `curl -s ifconfig.me`).

### 2.2 Base packages (as root)

```bash
apt-get update && apt-get upgrade -y
apt-get install -y gnucobol4 build-essential nginx python3-pip python3-venv sqlite3 certbot python3-certbot-nginx ufw fail2ban git curl htop

cobc --version   # need 4.0-early-dev.0+
nginx -v         # 1.26.3
sqlite3 --version # 3.46.1
python3 --version # 3.14 default; we will use python3.13 for venv (see 2.4)
python3.13 --version # 3.13.5 on trixie — required (3.14 breaks pydantic-core rust build)
```

If `python3.13` missing: `apt-get install -y python3.13 python3.13-venv` (trixie has it; Ubuntu 24.04 `apt-get install -y python3.13` from deadsnakes PPA if needed).

### 2.3 Users & SSH (production VPS only; skip in this localhost container)

```bash
adduser smcpe
usermod -aG sudo smcpe
mkdir -p /home/smcpe/app && chown smcpe:smcpe /home/smcpe/app
# SSH harden /etc/ssh/sshd_config:
#   PasswordAuthentication no
#   PermitRootLogin no
#   Port 2222 (optional)
# systemctl restart sshd
# add your key to ~smcpe/.ssh/authorized_keys
```

This container runs as `root` at `/home/projects/smcpe` — `smcpe` user not needed; replace `/home/smcpe/app` with `/home/projects/smcpe` in all paths below if you keep this layout.

### 2.4 Clone & Python venv (MUST use 3.13)

```bash
git clone https://github.com/Modather22222/smcpe.git /home/projects/smcpe
cd /home/projects/smcpe
# OR if you already have the repo: git pull origin master

python3.13 -m venv backend/.venv
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -r backend/requirements.txt
backend/.venv/bin/python -c "import fastapi; print(fastapi.__version__)" # 0.115.0
```

**Why 3.13 not 3.14:** `pydantic-core 2.33` rust build fails on 3.14 (`PyUnicode_DATA` removed) even with `PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1`. `3.13` has prebuilt wheels.

### 2.5 Build COBOL

```bash
make -C backend/cobol
ls -lh backend/cobol/libpayroll.so # 28KB
nm -D backend/cobol/libpayroll.so | grep -E "PAYROLL|FX|NSIF|TAX|ESG"
# PAYROLL__CALC, FX__NORM, NSIF__ENG, TAX__SUD, ESG__VAL
```

`cobc` flags are `cobc -free -b -O2 -Wall -I copybooks` → `mv payroll_calc.so libpayroll.so` (see `backend/cobol/Makefile:1`).

### 2.6 DB

```bash
# .env is gitignored; copy example and edit
cp backend/.env.example backend/.env
# Edit backend/.env: set JWT_SECRET to 32+ random hex, CORS_ORIGIN, DB_PATH, COBOL_LIB
# Generate JWT secret:
python3 -c "import secrets; print(secrets.token_hex(32))"
# Then:
# JWT_SECRET=<that>
# DB_PATH=/home/projects/smcpe/backend/db/smcpe.db  (or /home/smcpe/app/backend/db/smcpe.db on real VPS)
# COBOL_LIB=/home/projects/smcpe/backend/cobol/libpayroll.so
# CORS_ORIGIN=https://pay.yourdomain.sd,http://localhost,http://127.0.0.1,http://localhost:80,http://127.0.0.1:80
# STATUTORY_VERSION=v2026.09

DB_PATH=backend/db/smcpe.db python3 backend/db/migrate.py
# Tables: tenants 2, employees 4, fx_history 9, statutory_tables 1
# 84K WAL
ls -lh backend/db/smcpe.db
sqlite3 backend/db/smcpe.db "SELECT COUNT(*) FROM employees;" # 4
chmod 640 backend/db/smcpe.db
chmod 750 backend/db/
```

### 2.7 Nginx (localhost)

```bash
cp ops/nginx/smcpe.conf /etc/nginx/sites-available/smcpe
ln -sf /etc/nginx/sites-available/smcpe /etc/nginx/sites-enabled/smcpe
rm -f /etc/nginx/sites-enabled/default
nginx -t && nginx -s reload
# Or if nginx not running: nginx

curl -I http://127.0.0.1/          # 200 + SMCPE landing 6994 bytes, headers X-Frame-Options DENY etc
curl -s http://127.0.0.1/app/ | head -5  # dashboard
curl -s http://127.0.0.1/app/login.html | head -5
```

`ops/nginx/smcpe.conf:1` already does:
- `listen 80; server_name localhost pay.local;`
- `root /home/projects/smcpe/landing-page` for `/`
- `alias /home/projects/smcpe/dashboard/` for `/app/`
- `proxy_pass http://127.0.0.1:8000` for `/api/` with `limit_req_zone 10r/s` + `X-Frame-Options DENY` + `client_max_body_size 2m`

If your repo is at `/home/smcpe/app`, edit `root`/`alias` in `smcpe.conf` to that path before `nginx -t`.

### 2.8 API (localhost)

```bash
# Load .env and start (container has no systemd; production VPS see 2.9)
set -a; source backend/.env; set +a
backend/.venv/bin/uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --workers 2 > /tmp/uvicorn.log 2>&1 &
sleep 2
curl -s http://127.0.0.1:8000/api/health | jq # direct
curl -s http://127.0.0.1/api/health | jq      # via Nginx (same origin, no CORS)
curl -s http://localhost/api/health | jq     # also via Nginx

# Verify CORS now allows localhost (we added it to backend/.env)
grep CORS_ORIGIN backend/.env

# Test full loop
TOKEN=$(curl -s -X POST http://localhost/api/auth/login -H "Content-Type: application/json" -d '{"email":"owner@nileagro.sd","password":"admin123"}' | jq -r .access_token)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost/api/employees | jq .employees[0].id
RID=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"period":"2026-09"}' http://localhost/api/runs | jq -r .run_id)
curl -s -X POST -H "Authorization: Bearer $TOKEN" http://localhost/api/runs/$RID/compute | jq .totals
```

### 2.9 Systemd (production VPS with systemd; this container uses `nohup` above)

```bash
# Copy unit
cp ops/systemd/smcpe-api.service /etc/systemd/system/smcpe-api.service
# Edit WorkingDirectory=/home/projects/smcpe/backend  (or /home/smcpe/app/backend)
# Edit EnvironmentFile=/home/projects/smcpe/backend/.env
# Edit ExecStart=/home/projects/smcpe/backend/.venv/bin/uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --workers 2

systemctl daemon-reload
systemctl enable --now smcpe-api
systemctl status smcpe-api
journalctl -u smcpe-api -f
curl -s http://127.0.0.1:8000/api/health | jq
```

This container has no `systemd` (`systemctl` fails), so we keep `nohup` + `ps aux | grep uvicorn`.

### 2.10 UFW & Fail2ban (production; this VPS already active)

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp
ufw --force enable
ufw status verbose

cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime = 3600
[sshd] enabled = true
[nginx-http-auth] enabled = true
EOF
systemctl enable --now fail2ban || service fail2ban start
fail2ban-client status
```

### 2.11 TLS (when you have a domain; localhost stays http)

```bash
# Point DNS A pay.yourdomain.sd → VPS IP (curl -s ifconfig.me)
certbot --nginx -d pay.yourdomain.sd -d www.pay.yourdomain.sd --redirect -m you@company.sd --agree-tos
certbot renew --dry-run
# cron
# 0 3 * * * certbot renew --quiet && systemctl reload nginx
```

For **localhost testing** keep `http://localhost` and `http://127.0.0.1` — no TLS needed. The `CORS_ORIGIN` already includes `http://localhost`.

---

## 3. Verify localhost is production-ready (checklist)

```bash
# COBOL
make -C backend/cobol && python3 backend/tests/test_cobol_roundtrip.py # COMP-3 roundtrip OK 28KB

# DB
sqlite3 backend/db/smcpe.db "SELECT COUNT(*) FROM employees;" # 4
sqlite3 backend/db/smcpe.db "PRAGMA integrity_check;" # ok

# API
pytest backend/tests -v # 3 passed (health, login+employees, cobol_roundtrip)
curl -s http://localhost/api/health | jq
curl -s http://127.0.0.1/api/health | jq
curl -s http://127.0.0.1:8000/api/health | jq

# Frontend
curl -so /dev/null -w '%{size_download} bytes\n' http://localhost/ # 6994 (<50KB)
curl -so /dev/null -w '%{size_download} bytes\n' http://localhost/app/ # 6644 (<50KB)
ls -lh backend/data/runs/2026-09/payslip_*.txt | awk '{print $9, $5}' # 794 (<7KB)

# Nginx headers
curl -I http://localhost/ | grep -i "X-Frame"

# Full run
TOKEN=...; RID=...; curl -H "Authorization: Bearer $TOKEN" http://localhost/api/bank/file?run_id=$RID | head
```

Open in browser: `http://localhost/` (landing) and `http://localhost/app/login.html` (owner@nileagro.sd / admin123) → dashboard KPIs load via `/api`.

---

## 4. Moving to another VPS (migration)

### 4.1 What to copy

**Must copy:**
- Repo (all files except gitignored): `git clone https://github.com/Modather22222/smcpe.git` on new VPS → `pull` gets latest `master`/`v1.0.0`
- Secrets: `backend/.env` (create from `backend/.env.example` on new VPS, set `JWT_SECRET` to **same** 64-hex if you want old JWTs to stay valid; otherwise generate new via `python3 -c "import secrets; print(secrets.token_hex(32))"` and re-login)
- DB: `backend/db/smcpe.db` (84K WAL) **or** just `backups/smcpe-*.tgz` + `backups/smcpe-runs-*.tgz`
- Flat files: `backend/data/runs/` (optional, can be regenerated from DB via workers)

**Do NOT copy:** `backend/.venv/` (rebuild), `backend/cobol/libpayroll.so` (rebuild via `make`), `__pycache__/`, `backups/` (except to restore).

### 4.2 Migration steps (new VPS IP = `NEW_IP`)

```bash
# On OLD VPS (this one):
DB_PATH=backend/db/smcpe.db bash ops/scripts/backup.sh
ls -lh backups/ # smcpe-20260914-1058.tgz + smcpe-runs-20260914-1058.tgz
# Copy to new VPS (pick one):
scp backups/smcpe-*.tgz smcpe@NEW_IP:/tmp/
# OR if you have DB file directly:
scp backend/db/smcpe.db smcpe@NEW_IP:/tmp/smcpe.db
# Also copy .env if you want same secret (otherwise recreate):
scp backend/.env smcpe@NEW_IP:/tmp/.env
```

```bash
# On NEW VPS:
# 1. Packages
apt-get update && apt-get install -y gnucobol4 build-essential nginx python3-pip python3-venv sqlite3 certbot python3-certbot-nginx ufw fail2ban git

# 2. Repo
git clone https://github.com/Modather22222/smcpe.git /home/projects/smcpe
cd /home/projects/smcpe
git checkout v1.0.0   # or master

# 3. Venv (MUST 3.13)
python3.13 -m venv backend/.venv
backend/.venv/bin/pip install -r backend/requirements.txt

# 4. COBOL
make -C backend/cobol
ls -lh backend/cobol/libpayroll.so

# 5. Env
cp backend/.env.example backend/.env
# Edit backend/.env: paste old JWT_SECRET, set DB_PATH=/home/projects/smcpe/backend/db/smcpe.db, COBOL_LIB=/home/projects/smcpe/backend/cobol/libpayroll.so, CORS_ORIGIN=...
# OR scp the old .env:
# scp /tmp/.env backend/.env

# 6. DB — option A: restore from backup tgz
mkdir -p backend/db
tar xzf /tmp/smcpe-20260914-1058.tgz -C /tmp
cp /tmp/smcpe-20260914-1058.db backend/db/smcpe.db
# OR option B: direct copy
cp /tmp/smcpe.db backend/db/smcpe.db
# Verify
sqlite3 backend/db/smcpe.db "SELECT COUNT(*) FROM employees;" # 4
sqlite3 backend/db/smcpe.db "PRAGMA integrity_check;" # ok
chmod 640 backend/db/smcpe.db
chmod 750 backend/db/

# 7. Nginx
cp ops/nginx/smcpe.conf /etc/nginx/sites-available/smcpe
# Edit root/alias if path differs (/home/projects/smcpe vs /home/smcpe/app)
ln -sf /etc/nginx/sites-available/smcpe /etc/nginx/sites-enabled/smcpe
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx || nginx

# 8. UFW/Fail2ban (as in 2.10)
ufw --force enable
systemctl enable --now fail2ban

# 9. Start API
# If systemd:
cp ops/systemd/smcpe-api.service /etc/systemd/system/smcpe-api.service
# Edit paths
systemctl daemon-reload && systemctl enable --now smcpe-api
# Else nohup (container):
set -a; source backend/.env; set +a
backend/.venv/bin/uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --workers 2 > /tmp/uvicorn.log 2>&1 &

# 10. Verify localhost on NEW VPS
curl -s http://127.0.0.1/api/health | jq
curl -s http://localhost/api/health | jq
pytest backend/tests -v # 3 passed

# 11. TLS (if you moved domain)
# Update DNS A pay.yourdomain.sd → NEW_IP, wait, then:
certbot --nginx -d pay.yourdomain.sd --redirect
```

### 4.3 After migration — checklist

- [ ] `git log --oneline -5` on new VPS shows `v1.0.0` / `master` up to date
- [ ] `backend/db/smcpe.db` 84K, `SELECT COUNT(*) FROM employees` 4, `fx_history` 9, `statutory_tables` 1
- [ ] `backend/cobol/libpayroll.so` 28KB, `nm -D` 5 symbols
- [ ] `backend/.env` `JWT_SECRET` 64 hex, `CORS_ORIGIN` includes new domain + `http://localhost`
- [ ] `nginx -T | grep server_name` correct, `ufw status verbose` active, `curl -I http://127.0.0.1/` 200
- [ ] `curl -s http://127.0.0.1:8000/api/health` 200, `http://127.0.0.1/api/health` 200, `pytest backend/tests -v` 3 passed
- [ ] `backups/` 2 tgz + `restore.sh` `integrity_check ok`
- [ ] Old VPS: keep `backups/` offsite (rclone/s3) for 7 days, then `ufw deny` or shutdown

### 4.4 What NOT to do

- Don't `scp backend/.venv/` — rebuild with `python3.13 -m venv`
- Don't `scp backend/cobol/libpayroll.so` from different arch (e.g. ARM → x86) — `make -C backend/cobol` on new VPS
- Don't copy `*.db` while `uvicorn` is writing — use `bash ops/scripts/backup.sh` (does `sqlite3 .backup`)

---

## 5. Localhost vs production ports

| URL | Via | When to use |
|-----|-----|-------------|
| `http://localhost/` | Nginx `80` | Browser landing (this VPS, no TLS) |
| `http://localhost/app/login.html` | Nginx `80` `alias /app/` | Dashboard login (owner@nileagro.sd/admin123) |
| `http://localhost/api/health` | Nginx `80` → `proxy_pass 127.0.0.1:8000` | Same-origin API (dashboard `config.js` uses `/api`) |
| `http://127.0.0.1:8000/api/health` | Uvicorn direct | Debug/curl without Nginx |
| `http://127.0.0.1:8000/docs` | Uvicorn | Swagger OpenAPI |

All four return `{"ok":true,"lib":"libpayroll.so","version":"v2026.09"}`.

---

## 6. Troubleshooting

- **`cobc: command not found`** → `apt-get install gnucobol4`
- **`pydantic-core` build fails on 3.14** → use `python3.13 -m venv` (3.14 has no prebuilt wheel)
- **`libcob: error: cob_init() has not been called`** → `payroll_lib.py` already calls `cob_init(0,None)` before `PAYROLL__CALC`
- **`threads can only be started once`** → we fixed `aiosqlite` to `async with aiosqlite.connect() as db:` (see `api/routers/*`)
- **`ValueError: password cannot be longer than 72 bytes`** → `security.py` now uses direct `bcrypt` with truncate `[:72]` (was passlib 1.7.4 bug)
- **`401 Missing token` on dashboard** → login at `http://localhost/app/login.html`, `localStorage smcpe-jwt` must be set, `Authorization: Bearer` header
- **`nginx: [emerg] unknown directive "limit_req_zone"`** → ensure `limit_req_zone` is in `http` context (our `smcpe.conf` is included via `sites-enabled` inside `http`, OK)
- **`curl: (7) Failed to connect`** → check `ps aux | grep uvicorn`, `nginx`, `ufw status`, `ss -tlnp | grep 8000`

---

## 7. File map for migration

```
ops/nginx/smcpe.conf          → /etc/nginx/sites-available/smcpe
ops/systemd/smcpe-api.service → /etc/systemd/system/smcpe-api.service
ops/scripts/backup.sh         → cron 0 2 * * *
ops/scripts/restore.sh        → manual restore
backend/.env.example          → backend/.env (edit JWT_SECRET etc)
backend/db/schema.sql + seed.sql → backend/db/smcpe.db via migrate.py
backend/cobol/*.cob           → backend/cobol/libpayroll.so via make
docs/01-08.md                 → all operational docs
```

---

## 8. One-liner localhost start (this VPS, after reboot)

```bash
cd /home/projects/smcpe
nginx 2>/dev/null; nginx -t && echo "nginx OK"
set -a; source backend/.env; set +a
backend/.venv/bin/uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --workers 2 > /tmp/uvicorn.log 2>&1 &
sleep 2; curl -s http://localhost/api/health | jq
# open http://localhost/ and http://localhost/app/login.html
```
