# 07 — Security & Hardening

## Threat model

| Threat | Impact | Control |
|--------|--------|---------|
| Tenant leak (cross-tenant read) | Payroll data exposure | Every query `WHERE tenant_id=:tid` from JWT, RBAC owner>accountant>viewer, `test_tenant_isolation` |
| FX tamper | Wrong net pay | `POST /api/fx/lock` owner/accountant only, FX snapshot + statutory_version stored per run for replay, audit_log |
| Bank file injection | Wrong transfer | Bank account `X(24)` validated length, net as `TEXT` 2 decimals, `H|D|T` fixed-width, `COMP3-EXACT` trailer |
| Auth brute force | Account takeover | Nginx `limit_req 10r/s burst 20` on `/api/`, `bcrypt` cost 12, JWT 15m, Fail2ban ssh + nginx-http-auth |
| DB theft | SQLite file | `chmod 640 backend/db/smcpe.db`, `chown smcpe:www-data`, UFW deny incoming, TLS via certbot |
| Backup leak | Offsite | `tar czf` + optional `rclone` to S3 with `find -mtime +7 -delete`, restore tested `PRAGMA integrity_check` |

## Hardening checklist (verified 2026-09-14)

- [x] UFW `deny incoming, allow outgoing, allow 22/80/443` → `ufw status verbose` active
- [x] Fail2ban `jail.local` `[sshd] enabled, [nginx-http-auth]`, `service fail2ban` (container: manual `service fail2ban start` if systemd available)
- [x] Nginx `add_header X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy strict-origin`, `X-XSS-Protection`, `client_max_body_size 2m`, `limit_req_zone 10r/s` on `/api/`
- [x] CORS `allow_origins` from `CORS_ORIGIN` env (`https://pay.yourdomain.sd`), `allow_credentials True`
- [x] JWT `HS256` secret 64 hex (32 bytes) in `backend/.env` `JWT_SECRET`, `HttpOnly` not used (Bearer header), `Authorization: Bearer`
- [x] Password `bcrypt` `gensalt` cost 12, 72-byte truncate, `verify` via `checkpw`
- [x] DB `chmod 640`, `chmod 750 backend/db/`, `PRAGMA foreign_keys=ON`, `PRAGMA journal_mode=WAL`
- [x] Input: `money ^\d+\.\d{2}$`, `fx ^\d+\.\d{4}$` max `99999.9999`, `period ^\d{4}-\d{2}$`, currency enum `SDG|USD|SAR|AED`, `nsif Y/N`

## RBAC

- `owner`: approve+post+export, publish statutory, lock FX
- `accountant`: run+FX draft, compute, reports
- `viewer`: payslips only (UI hides `data-requires`)

## Audit log

- `audit_log` `hash = sha256(prev_hash + payload)` chain, `action` in `FX_LOCK,RUN_CREATE,RUN_COMPUTE,RUN_APPROVE,STATUTORY_PUBLISH,PAYSLIP_QUEUED`
- `GET /api/audit?limit=50` → immutable

## Backup encryption (future)

- For production: `rclone crypt` or `gpg -c` before `rclone copy s3:`

## Incident response

1. `ufw deny from <ip>` + `fail2ban-client ban <ip>`
2. Rotate `JWT_SECRET` in `backend/.env`, restart `uvicorn`
3. Restore from `backups/smcpe-*.tgz` via `ops/scripts/restore.sh` → `PRAGMA integrity_check ok`
4. Audit `GET /api/audit` + `journalctl -u smcpe-api`
