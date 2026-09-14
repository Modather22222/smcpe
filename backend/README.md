# Backend (reserved)

Empty scaffold for the future Python/FastCGI + GnuCOBOL integration.

Planned:
- `cobol/` — `payroll_calc.cob`, copybooks `EMPFILE.cpy`, `PRLREC.cpy`, build `cobc -fPIC -shared -O2`
- `api/` — FastCGI endpoints: auth, employees, runs, fx, reports, bank export
- `db/` — SQLite schema: users, tenants, periods, fx_history, payroll_logs
- `workers/` — batch runner, WhatsApp/Telegram payslip sender, backup cron

Contract with frontend: JSON over HTTP; all money as strings with 2 decimals (`"3307085.82"`); every run echoes `fx_rate` + `statutory_version` for audit replay.
