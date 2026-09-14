"""Runs — create, compute via COBOL COMP-3, approve, with tenant isolation and Decimal totals."""
import json
import uuid
import datetime
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from ..deps import DBDep, UserDep, require_role
from ..schemas import PayrollRunCreate
from ..payroll_lib import compute_payroll

logger = logging.getLogger("smcpe.runs")
router = APIRouter(prefix="/api/runs", tags=["runs"])

def _add(a: str, b: str) -> str:
    return format(Decimal(a) + Decimal(b), ".2f")

@router.post("", status_code=201)
async def create_run(body: PayrollRunCreate, db: DBDep, user: UserDep) -> dict:
    run_id = f"run_{body.period}_{user['tenant_id']}_{uuid.uuid4().hex[:6]}"
    fx_snapshot = body.fx_snapshot
    if not fx_snapshot:
        cur = await db.execute("SELECT currency, rate FROM fx_history WHERE source='locked' ORDER BY date DESC")
        rows = await cur.fetchall()
        fx_snapshot = {r["currency"]: r["rate"] for r in rows}
        if not fx_snapshot:
            cur = await db.execute("SELECT currency, rate FROM fx_history ORDER BY date DESC")
            rows = await cur.fetchall()
            fx_snapshot = {r["currency"]: r["rate"] for r in rows}
    await db.execute(
        "INSERT INTO payroll_runs (id, tenant_id, period, fx_snapshot_json, statutory_version, status, created_by, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (run_id, user["tenant_id"], body.period, json.dumps(fx_snapshot), body.statutory_version, "draft", user["sub"], datetime.datetime.now(datetime.timezone.utc).isoformat()),
    )
    await db.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                     (user["sub"], "RUN_CREATE", "00", json.dumps({"run_id": run_id, "period": body.period})))
    await db.commit()
    logger.info("Run %s created by %s period %s", run_id, user["sub"], body.period)
    return {"run_id": run_id, "fx_snapshot": fx_snapshot}

@router.post("/{run_id}/compute")
async def compute_run(run_id: str, db: DBDep, user: UserDep) -> dict:
    cur = await db.execute("SELECT * FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
    run = await cur.fetchone()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    fx_snapshot = json.loads(run["fx_snapshot_json"])
    statutory_version = run["statutory_version"]
    cur = await db.execute("SELECT * FROM employees WHERE tenant_id=?", (user["tenant_id"],))
    emps = await cur.fetchall()
    if not emps:
        raise HTTPException(status_code=400, detail="No employees for tenant")
    # idempotent: clear previous
    await db.execute("DELETE FROM payroll_lines WHERE run_id=?", (run_id,))
    totals = {"gross": "0.00", "nsif_emp": "0.00", "nsif_co": "0.00", "taxable": "0.00", "pit": "0.00", "net": "0.00"}
    last_engine = "python"
    for emp in emps:
        cur_code = emp["base_currency"]
        fx_rate = fx_snapshot.get(cur_code, "1.0000") if cur_code != "SDG" else "1.0000"
        try:
            fx_f = format(Decimal(fx_rate).quantize(Decimal("0.0000"), rounding=ROUND_HALF_UP), ".4f")
        except Exception:
            fx_f = "1.0000"
            logger.warning("Invalid fx %s for %s, fallback 1.0000", fx_rate, cur_code)
        res = compute_payroll(cur_code, emp["base_salary"], emp["allowances"], fx_f, emp["nsif_eligible"], statutory_version)
        last_engine = res.get("engine", last_engine)
        await db.execute(
            "INSERT INTO payroll_lines (run_id, emp_id, gross, nsif_emp, nsif_co, taxable, pit, net, net_fx) VALUES (?,?,?,?,?,?,?,?,?)",
            (run_id, emp["id"], res["gross"], res["nsif_emp"], res["nsif_co"], res["taxable"], res["pit"], res["net"], res["net"]),
        )
        for k in totals:
            totals[k] = _add(totals[k], res[k])
    await db.execute("UPDATE payroll_runs SET status='computed' WHERE id=?", (run_id,))
    await db.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                     (user["sub"], "RUN_COMPUTE", "00", json.dumps({"run_id": run_id, "totals": totals})))
    await db.commit()
    cur = await db.execute("SELECT * FROM payroll_lines WHERE run_id=?", (run_id,))
    lines = [dict(r) for r in await cur.fetchall()]
    logger.info("Run %s computed %s lines via %s totals %s", run_id, len(lines), last_engine, totals)
    return {"run_id": run_id, "totals": totals, "lines": lines, "engine": last_engine}

@router.post("/{run_id}/approve")
async def approve_run(run_id: str, db: DBDep, user: Annotated[dict, Depends(require_role("owner"))]) -> dict:
    cur = await db.execute("SELECT status FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    if row["status"] != "computed":
        raise HTTPException(status_code=409, detail="Run must be computed before approve")
    await db.execute("UPDATE payroll_runs SET status='approved' WHERE id=?", (run_id,))
    await db.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                     (user["sub"], "RUN_APPROVE", "00", json.dumps({"run_id": run_id})))
    await db.commit()
    logger.info("Run %s approved by %s", run_id, user["sub"])
    return {"ok": True, "status": "approved"}

@router.get("")
async def list_runs(db: DBDep, user: UserDep, period: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)) -> dict:
    q = "SELECT * FROM payroll_runs WHERE tenant_id=? ORDER BY period DESC, created_at DESC LIMIT ? OFFSET ?"
    params: tuple = (user["tenant_id"], limit, offset)
    if period:
        q = "SELECT * FROM payroll_runs WHERE tenant_id=? AND period=? ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params = (user["tenant_id"], period, limit, offset)
    cur = await db.execute(q, params)
    rows = await cur.fetchall()
    return {"runs": [dict(r) for r in rows], "limit": limit, "offset": offset}

@router.get("/{run_id}")
async def get_run(run_id: str, db: DBDep, user: UserDep) -> dict:
    cur = await db.execute("SELECT * FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
    run = await cur.fetchone()
    if not run:
        raise HTTPException(status_code=404, detail="Not found")
    cur = await db.execute("SELECT * FROM payroll_lines WHERE run_id=?", (run_id,))
    lines = [dict(r) for r in await cur.fetchall()]
    return {"run": dict(run), "lines": lines}
