"""Payslips — text 7KB, tenant-isolated, stub send."""
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from ..deps import DBDep, UserDep

logger = logging.getLogger("smcpe.payslips")
router = APIRouter(prefix="/api/payslips", tags=["payslips"])

@router.get("")
async def list_payslips(run_id: str, db: DBDep, user: UserDep) -> dict:
    cur = await db.execute("SELECT id FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
    if not await cur.fetchone():
        raise HTTPException(status_code=404, detail="Run not found")
    cur = await db.execute("SELECT l.*, e.name, e.base_currency FROM payroll_lines l JOIN employees e ON e.id=l.emp_id WHERE l.run_id=?", (run_id,))
    rows = [dict(r) for r in await cur.fetchall()]
    return {"payslips": rows}

@router.get("/{emp_id}")
async def get_payslip(emp_id: str, db: DBDep, user: UserDep, run_id: str | None = None) -> PlainTextResponse:
    cur = await db.execute("SELECT id FROM employees WHERE id=? AND tenant_id=?", (emp_id, user["tenant_id"]))
    if not await cur.fetchone():
        raise HTTPException(status_code=404, detail="Employee not found or wrong tenant")
    if run_id:
        cur = await db.execute("SELECT id FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="Run not found")
        cur = await db.execute("SELECT l.*, e.name FROM payroll_lines l JOIN employees e ON e.id=l.emp_id WHERE l.run_id=? AND l.emp_id=?", (run_id, emp_id))
    else:
        cur = await db.execute("SELECT l.*, e.name FROM payroll_lines l JOIN employees e ON e.id=l.emp_id WHERE l.emp_id=? AND e.tenant_id=? ORDER BY l.run_id DESC LIMIT 1", (emp_id, user["tenant_id"]))
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Payslip not found")
    d = dict(row)
    txt = f"""SMCPE Payslip {d.get('run_id','')} — {d.get('name','')} ({emp_id})
Gross SDG: {d['gross']}
NSIF Emp 8%: {d['nsif_emp']}
Taxable: {d['taxable']}
PIT: {d['pit']}
Net SDG: {d['net']}
"""
    return PlainTextResponse(txt, media_type="text/plain")

@router.post("/send")
async def send_payslip(run_id: str, db: DBDep, user: UserDep, emp_id: str | None = None) -> dict:
    cur = await db.execute("SELECT id FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
    if not await cur.fetchone():
        raise HTTPException(status_code=404, detail="Run not found")
    logger.info("Payslip send queued %s emp %s by %s", run_id, emp_id or "all", user["sub"])
    return {"ok": True, "queued": emp_id or "all", "run_id": run_id, "note": "WhatsApp/Telegram stub — queued"}
