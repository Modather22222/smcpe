# 06 — Operations Runbook

## 1) Bank file (H|D|T)

Spec `dashboard/bank.html:12`: fixed-width direct-debit.

```
H|NILEAGRO|202609|000042|0048620400.00
D|1002844551|3307085.82|SD-0042|BANKAK
T|000042|33891240.55|COMP3-EXACT
```

- `H|tenant|YYYYMM|count(6)|gross(11.2)`
- `D|bank_account(24)|net(11.2)|emp_id|bank_code`
- `T|count|net_total|COMP3-EXACT`

Generate:

```bash
# via API
curl -s -H "Authorization: Bearer $TOKEN" "http://127.0.0.1/api/bank/file?run_id=run_2026-09_NA_xxx" > bank.txt
# via worker (also writes to backend/data/runs/2026-09/bank_*.txt)
python3 backend/workers/bank_export.py run_2026-09_NA_xxx
cat backend/data/runs/2026-09/bank_*.txt
# verify
diff <(curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1/api/bank/file?run_id=xxx) backend/data/runs/2026-09/bank_xxx.txt && echo "bank file OK"
```

Validate: `bank_account` length, `net` `^\d+\.\d{2}$`, `count` padded `06d`.

## 2) Daily ops

1. Lock FX (25th): `POST /api/fx/lock {"date":"2026-09-25","rates":{"USD":"2610.5000",...}}`
2. Import CSV: `POST /api/employees/import` (multipart)
3. Compute: `POST /api/runs {"period":"2026-09"}` → `POST /api/runs/{id}/compute` (calls libpayroll.so, 11ms/1k)
4. Approve: `POST /api/runs/{id}/approve` (owner only)
5. Bank: `GET /api/bank/file?run_id=...` → upload to Bankak portal
6. Reports: `GET /api/reports/nsif|pit|esg|zakat?run_id=...`
7. Payslips: `python3 backend/workers/payslip_sender.py <run_id>` → `backend/data/runs/2026-09/payslip_*.txt` (7KB, WhatsApp stub queues audit_log)

## 3) Payslips

- Template `backend/templates/payslip.txt` → rendered via `payslip_sender.py` (794 bytes for SD-0042, <7KB)
- Text for EDGE, optional PDF via `reportlab` (keep <50KB): `GET /api/payslips/{emp_id}?run_id=...` returns `text/plain`
- Delivery log: `audit_log` `PAYSLIP_QUEUED`, webhook stub `POST /api/payslips/send?run_id=...`

## 4) Reports SQL

```sql
-- NSIF schedule
SELECT emp_id, gross, nsif_emp, nsif_co FROM payroll_lines WHERE run_id='run_2026-09_NA_xxx';
-- PIT
SELECT emp_id, taxable, pit FROM payroll_lines WHERE run_id='xxx';
-- ESG
SELECT e.id, e.hire_date, l.net FROM employees e JOIN payroll_lines l ON l.emp_id=e.id WHERE l.run_id='xxx';
```

## 5) Backup & restore

- `ops/scripts/backup.sh` → `sqlite3 .backup` + `tar czf` + `rclone` (or cron `0 2 * * *`)
- `ops/scripts/restore.sh` → `tar xzf` + `PRAGMA integrity_check` in `/tmp`
- Verify: `bash ops/scripts/backup.sh && ls -lh backups/ && bash ops/scripts/restore.sh`

## 6) Logs

- API: `journalctl -u smcpe-api -f` or `/tmp/uvicorn.log` (request ID `X-Request-ID`, `X-Process-Time`)
- Nginx: `/var/log/nginx/smcpe-access.log` + `smcpe-error.log`, `logrotate`
- Audit: `GET /api/audit?limit=50`
