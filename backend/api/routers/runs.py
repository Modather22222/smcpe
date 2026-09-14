from fastapi import APIRouter, Depends, HTTPException
from ..schemas import PayrollRunCreate
from ..payroll_lib import compute_payroll
from .auth import require_user
import aiosqlite, os, pathlib, json, uuid, datetime

router = APIRouter(prefix="/api/runs", tags=["runs"])
DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).parent.parent.parent / "db" / "smcpe.db"))

@router.post("")
async def create_run(body: PayrollRunCreate, user=Depends(require_user)):
    run_id = f"run_{body.period}_{user['tenant_id']}_{uuid.uuid4().hex[:6]}"
    fx_snapshot = body.fx_snapshot
    if not fx_snapshot:
        # fetch latest locked
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT currency, rate FROM fx_history WHERE source='locked' ORDER BY date DESC")
            rows = await cur.fetchall()
            fx_snapshot = {r["currency"]: r["rate"] for r in rows}
            if not fx_snapshot:
                cur = await db.execute("SELECT currency, rate FROM fx_history ORDER BY date DESC")
                rows = await cur.fetchall()
                fx_snapshot = {r["currency"]: r["rate"] for r in rows}
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payroll_runs (id, tenant_id, period, fx_snapshot_json, statutory_version, status, created_by, created_at) VALUES (?,?,?,?,?,?,?,?)",
            (run_id, user["tenant_id"], body.period, json.dumps(fx_snapshot), body.statutory_version, "draft", user["sub"], datetime.datetime.utcnow().isoformat())
        )
        await db.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                         (user["sub"], "RUN_CREATE", "00", json.dumps({"run_id": run_id, "period": body.period})))
        await db.commit()
    return {"run_id": run_id, "fx_snapshot": fx_snapshot}

@router.post("/{run_id}/compute")
async def compute_run(run_id: str, user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
        run = await cur.fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        fx_snapshot = json.loads(run["fx_snapshot_json"])
        statutory_version = run["statutory_version"]
        # get employees (all tenant if run has no specific filter)
        cur = await db.execute("SELECT * FROM employees WHERE tenant_id=?", (user["tenant_id"],))
        emps = await cur.fetchall()
        if not emps:
            raise HTTPException(status_code=400, detail="No employees")
        # clear previous lines
        await db.execute("DELETE FROM payroll_lines WHERE run_id=?", (run_id,))
        totals = {"gross":"0.00","nsif_emp":"0.00","nsif_co":"0.00","taxable":"0.00","pit":"0.00","net":"0.00"}
        from decimal import Decimal
        def add(a,b): return format(Decimal(a)+Decimal(b), ".2f")
        for emp in emps:
            cur_code = emp["base_currency"]
            fx_rate = fx_snapshot.get(cur_code, "1.0000") if cur_code != "SDG" else "1.0000"
            # ensure 4 decimals
            try:
                fx_f = format(Decimal(fx_rate), ".4f")
            except:
                fx_f = "1.0000"
            res = compute_payroll(cur_code, emp["base_salary"], emp["allowances"], fx_f, emp["nsif_eligible"], statutory_version)
            await db.execute(
                "INSERT INTO payroll_lines (run_id, emp_id, gross, nsif_emp, nsif_co, taxable, pit, net, net_fx) VALUES (?,?,?,?,?,?,?,?,?)",
                (run_id, emp["id"], res["gross"], res["nsif_emp"], res["nsif_co"], res["taxable"], res["pit"], res["net"], res["net"])
            )
            totals["gross"] = add(totals["gross"], res["gross"])
            totals["nsif_emp"] = add(totals["nsif_emp"], res["nsif_emp"])
            totals["nsif_co"] = add(totals["nsif_co"], res["nsif_co"])
            totals["taxable"] = add(totals["taxable"], res["taxable"])
            totals["pit"] = add(totals["pit"], res["pit"])
            totals["net"] = add(totals["net"], res["net"])
        await db.execute("UPDATE payroll_runs SET status='computed' WHERE id=?", (run_id,))
        await db.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                         (user["sub"], "RUN_COMPUTE", "00", json.dumps({"run_id": run_id, "totals": totals})))
        await db.commit()
        # also return lines
        cur = await db.execute("SELECT * FROM payroll_lines WHERE run_id=?", (run_id,))
        lines = [dict(r) for r in await cur.fetchall()]
        return {"run_id": run_id, "totals": totals, "lines": lines, "engine": res.get("engine","unknown")}

@router.post("/{run_id}/approve")
async def approve_run(run_id: str, user=Depends(require_user)):
    if user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owner can approve")
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT status FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Run not found")
        if row["status"] != "computed":
            raise HTTPException(status_code=400, detail="Run must be computed first")
        await db.execute("UPDATE payroll_runs SET status='approved' WHERE id=?", (run_id,))
        await db.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                         (user["sub"], "RUN_APPROVE", "00", json.dumps({"run_id": run_id})))
        await db.commit()
    return {"ok": True, "status": "approved"}

@router.get("")
async def list_runs(period: str = None, user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM payroll_runs WHERE tenant_id=? ORDER BY period DESC"
        params = (user["tenant_id"],)
        if period:
            q = "SELECT * FROM payroll_runs WHERE tenant_id=? AND period=? ORDER BY created_at DESC"
            params = (user["tenant_id"], period)
        cur = await db.execute(q, params)
        rows = await cur.fetchall()
        return {"runs": [dict(r) for r in rows]}

@router.get("/{run_id}")
async def get_run(run_id: str, user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
        run = await cur.fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Not found")
        cur = await db.execute("SELECT * FROM payroll_lines WHERE run_id=?", (run_id,))
        lines = [dict(r) for r in await cur.fetchall()]
        return {"run": dict(run), "lines": lines}
