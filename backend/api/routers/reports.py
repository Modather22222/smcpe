"""Reports — NSIF/PIT/ESG/Zakat, Decimal, tenant-isolated."""
import datetime
import logging
from decimal import Decimal
from fastapi import APIRouter, HTTPException, Query
from ..deps import DBDep, UserDep
from ..payroll_lib import compute_esg

logger = logging.getLogger("smcpe.reports")
router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/nsif")
async def nsif_report(run_id: str, db: DBDep, user: UserDep) -> dict:
    cur = await db.execute("SELECT id FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
    if not await cur.fetchone():
        raise HTTPException(status_code=404, detail="Run not found or wrong tenant")
    cur = await db.execute("SELECT * FROM payroll_lines WHERE run_id=?", (run_id,))
    lines = [dict(r) for r in await cur.fetchall()]
    if not lines:
        raise HTTPException(status_code=404, detail="No lines")
    totals = {"gross": Decimal("0.00"), "nsif_emp": Decimal("0.00"), "nsif_co": Decimal("0.00")}
    for l in lines:
        totals["gross"] += Decimal(l["gross"])
        totals["nsif_emp"] += Decimal(l["nsif_emp"])
        totals["nsif_co"] += Decimal(l["nsif_co"])
    totals_str = {k: format(v, ".2f") for k, v in totals.items()}
    logger.debug("NSIF report %s totals %s", run_id, totals_str)
    return {"run_id": run_id, "lines": lines, "totals": totals_str}

@router.get("/pit")
async def pit_report(run_id: str, db: DBDep, user: UserDep) -> dict:
    cur = await db.execute("SELECT id FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
    if not await cur.fetchone():
        raise HTTPException(status_code=404, detail="Run not found")
    cur = await db.execute("SELECT emp_id, taxable, pit FROM payroll_lines WHERE run_id=?", (run_id,))
    rows = [dict(r) for r in await cur.fetchall()]
    return {"run_id": run_id, "rows": rows}

@router.get("/esg")
async def esg_report(db: DBDep, user: UserDep) -> dict:
    cur = await db.execute("SELECT id, name, hire_date, base_salary, allowances, base_currency FROM employees WHERE tenant_id=?", (user["tenant_id"],))
    emps = await cur.fetchall()
    cur2 = await db.execute("SELECT currency, rate FROM fx_history WHERE date='2026-09-25'")
    rates = {r["currency"]: r["rate"] for r in await cur2.fetchall()}
    out = []
    for e in emps:
        try:
            hire = datetime.datetime.strptime(e["hire_date"], "%Y-%m-%d")
        except ValueError:
            logger.warning("Bad hire_date %s for %s", e["hire_date"], e["id"])
            continue
        now = datetime.datetime(2026, 9, 30, tzinfo=datetime.timezone.utc)
        hire_utc = hire.replace(tzinfo=datetime.timezone.utc)
        years = (now - hire_utc).days / 365.25
        gross = Decimal(e["base_salary"]) + Decimal(e["allowances"])
        if e["base_currency"] != "SDG":
            try:
                gross = gross * Decimal(rates.get(e["base_currency"], "1"))
            except Exception:
                logger.exception("FX conversion failed for %s", e["id"])
        accrual = compute_esg(f"{years:.2f}", format(gross, ".2f"))
        out.append({"id": e["id"], "name": e["name"], "hire_date": e["hire_date"], "years": round(years, 1), "monthly_sdg": format(gross, ".2f"), "accrual": accrual})
    out.sort(key=lambda x: x["years"], reverse=True)
    return {"esg": out}

@router.get("/zakat")
async def zakat_report(run_id: str, db: DBDep, user: UserDep) -> dict:
    cur = await db.execute("SELECT id FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
    if not await cur.fetchone():
        raise HTTPException(status_code=404, detail="Run not found")
    cur = await db.execute("SELECT emp_id, net FROM payroll_lines WHERE run_id=?", (run_id,))
    rows = [dict(r) for r in await cur.fetchall()]
    nisab = Decimal("100000.00")
    flagged = [r for r in rows if Decimal(r["net"]) > nisab]
    return {"nisab": format(nisab, ".2f"), "flagged": flagged, "note": "Zakat after PIT, consent required"}
