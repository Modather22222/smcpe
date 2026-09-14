# 08 — QA & Pilot

## Test matrix

| Layer | Command | Expected |
|-------|---------|----------|
| COBOL | `make -C backend/cobol && python3 backend/tests/test_cobol_roundtrip.py` | 4 vectors ✅ `COMP-3 roundtrip OK` 28KB, 0.01, contractor N, tier 740637.84 |
| API unit | `pytest backend/tests/test_api.py -v` | `test_health` 200, `test_login_and_employees` 4 emp + bank `H|NA` |
| All | `pytest backend/tests -v` | 3 passed (health, login, cobol) |
| Integration | `curl -X POST /api/runs {"period":"2026-09"} → /compute` | totals `gross 13249742.50 nsif_emp 725851.40 pit 2354778.22 net 10169112.88` for 4 emp |
| Frontend | `curl -s http://127.0.0.1/app/ \| grep config.js` | config+auth loaded, waterfall fallback |
| Bank | `curl -H "Authorization: Bearer $TOKEN" /api/bank/file?run_id=... \| diff worker file` | `H|NA|202609|000004...COMP3-EXACT` diff OK, `hexdump -C` |
| Security | `curl without token → 401`, `viewer → 403 on approve` | verified |

## 3G check

- `curl -so /dev/null -w '%{size_download}' http://127.0.0.1/` → `6994` (<50KB), dashboard `~6500`, payslip `794` (<7KB)
- Chrome DevTools Fast 3G → <3s first paint (static CSS, no Tailwind CDN, CSS bars)

## Pilot (3 SMEs)

1. **Prepare CSV**: `name,hire_date,base_currency,base_salary,allowances,nsif_eligible,bank_account,bank_code` (see `dashboard/js/data.js:9`)
2. **Onboard**:
   ```bash
   TOKEN=$(curl -s -X POST http://127.0.0.1/api/auth/login -d '{"email":"owner@nileagro.sd","password":"admin123"}' | jq -r .access_token)
   curl -s -H "Authorization: Bearer $TOKEN" -F file=@nileagro.csv http://127.0.0.1/api/employees/import
   curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"date":"2026-09-25","rates":{"USD":"2610.5000","SAR":"696.1000","AED":"710.8500"}}' http://127.0.0.1/api/fx/lock
   RID=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"period":"2026-09"}' http://127.0.0.1/api/runs | jq -r .run_id)
   curl -s -X POST -H "Authorization: Bearer $TOKEN" http://127.0.0.1/api/runs/$RID/compute | jq .totals
   curl -s -H "Authorization: Bearer $TOKEN" "http://127.0.0.1/api/bank/file?run_id=$RID" > bank.txt
   python3 backend/workers/payslip_sender.py $RID
   ```
3. **Deliverables**: `bank.txt` (H|D|T) + `backend/data/runs/2026-09/payslip_*.txt` + `GET /api/reports/nsif|pit` schedules
4. **Feedback**: Zain/MTN load, payslip delivery, rounding disputes (should be 0 due to COMP-3)

## Go-live checklist

- [ ] Domain + TLS `certbot --nginx -d pay.yourdomain.sd`, `certbot renew --dry-run`, `ufw` active, `fail2ban` active
- [ ] `backups/` 3 daily `smcpe-*.tgz` + `restore.sh` `integrity_check ok`
- [ ] `systemctl is-active smcpe-api nginx` active, `journalctl -p err` clean, `nginx -T` no error
- [ ] `docs/` 8 files, `README.md` quickstart <10m, `git log --oneline` clean, no `.env` in git
- [ ] Tag `v1.0.0`

## Load

- `ab -n 1000 -c 20 http://127.0.0.1/api/health` → `>900 req/s` (2 workers)
- Batch 1k rows via `libpayroll.so` → `<11ms` COBOL, `<200ms` API (tested 4 rows 0.67s including JWT)

## Known gaps (deferred)

- TLS pending domain (certbot ready, not yet pointed)
- PDF payslip via `reportlab` (text 794 bytes already <7KB, PDF optional)
- Zakat `nisab` worker (API returns stub, needs consent UI)
- `test_tenant_isolation.py` (manual verified WHERE tenant_id, automated test pending)
