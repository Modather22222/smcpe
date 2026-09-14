from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from .auth import require_user
import aiosqlite, os, pathlib

router = APIRouter(prefix="/api/payslips", tags=["payslips"])
DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).parent.parent.parent / "db" / "smcpe.db"))

@router.get("")
async def list_payslips(run_id: str = None, user=Depends(require_user)):
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id required")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT l.*, e.name, e.base_currency FROM payroll_lines l JOIN employees e ON e.id=l.emp_id WHERE l.run_id=?", (run_id,))
        rows = [dict(r) for r in await cur.fetchall()]
        return {"payslips": rows}

@router.get("/{emp_id}")
async def get_payslip(emp_id: str, run_id: str = None, user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if run_id:
            cur = await db.execute("SELECT l.*, e.name FROM payroll_lines l JOIN employees e ON e.id=l.emp_id WHERE l.run_id=? AND l.emp_id=?", (run_id, emp_id))
        else:
            cur = await db.execute("SELECT l.*, e.name FROM payroll_lines l JOIN employees e ON e.id=l.emp_id WHERE l.emp_id=? ORDER BY l.run_id DESC LIMIT 1", (emp_id,))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
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
async def send_payslip(run_id: str, emp_id: str = None, user=Depends(require_user)):
    # stub queue
    return {"ok": True, "queued": emp_id or "all", "run_id": run_id, "note": "WhatsApp/Telegram stub — queued"}
