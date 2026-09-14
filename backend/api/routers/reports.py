from fastapi import APIRouter, Depends, HTTPException
from .auth import require_user
import aiosqlite, os, pathlib, datetime
from decimal import Decimal
from ..payroll_lib import compute_esg

router = APIRouter(prefix="/api/reports", tags=["reports"])
DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).parent.parent.parent / "db" / "smcpe.db"))

@router.get("/nsif")
async def nsif_report(run_id: str = None, user=Depends(require_user)):
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id required")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payroll_lines WHERE run_id=?", (run_id,))
        lines = [dict(r) for r in await cur.fetchall()]
        if not lines:
            raise HTTPException(status_code=404, detail="No lines")
        totals = {"gross": "0.00","nsif_emp":"0.00","nsif_co":"0.00"}
        for l in lines:
            for k in totals:
                col = {"gross":"gross","nsif_emp":"nsif_emp","nsif_co":"nsif_co"}[k]
                totals[k] = format(Decimal(totals[k]) + Decimal(l[col]), ".2f")
        return {"run_id": run_id, "lines": lines, "totals": totals}

@router.get("/pit")
async def pit_report(run_id: str = None, user=Depends(require_user)):
    if not run_id:
        raise HTTPException(status_code=400, detail="run_id required")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT emp_id, taxable, pit FROM payroll_lines WHERE run_id=?", (run_id,))
        rows = [dict(r) for r in await cur.fetchall()]
        return {"run_id": run_id, "rows": rows}

@router.get("/esg")
async def esg_report(user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT id, name, hire_date, base_salary, allowances, base_currency FROM employees WHERE tenant_id=?", (user["tenant_id"],))
        emps = await cur.fetchall()
        # fetch latest fx for SDG conversion? Use USD 2610.50 as monthly gross approximation
        # For ESG, monthly gross in SDG = (base+allow)*fx
        cur2 = await db.execute("SELECT currency, rate FROM fx_history WHERE date='2026-09-25'")
        rates = {r["currency"]: r["rate"] for r in await cur2.fetchall()}
        out = []
        for e in emps:
            hire = datetime.datetime.strptime(e["hire_date"], "%Y-%m-%d")
            now = datetime.datetime(2026,9,30)
            years = (now - hire).days / 365.25
            gross = Decimal(e["base_salary"]) + Decimal(e["allowances"])
            if e["base_currency"] != "SDG":
                gross = gross * Decimal(rates.get(e["base_currency"], "1"))
            accrual = compute_esg(f"{years:.2f}", format(gross, ".2f"))
            out.append({"id": e["id"], "name": e["name"], "hire_date": e["hire_date"], "years": round(years,1), "monthly_sdg": format(gross, ".2f"), "accrual": accrual})
        out.sort(key=lambda x: x["years"], reverse=True)
        return {"esg": out}

@router.get("/zakat")
async def zakat_report(run_id: str = None, user=Depends(require_user)):
    # stub: nisab check after PIT
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT emp_id, net FROM payroll_lines WHERE run_id=?", (run_id,))
        rows = [dict(r) for r in await cur.fetchall()]
        # nisab threshold example 100000 SDG
        nisab = Decimal("100000.00")
        flagged = [r for r in rows if Decimal(r["net"]) > nisab]
        return {"nisab": "100000.00", "flagged": flagged, "note": "Zakat after PIT, consent required"}
