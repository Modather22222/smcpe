from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from .auth import require_user
import aiosqlite, os, pathlib, json

router = APIRouter(prefix="/api/bank", tags=["bank"])
DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).parent.parent.parent / "db" / "smcpe.db"))

@router.get("/file")
async def bank_file(run_id: str, file_format: str = Query("txt", alias="format"), user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
        run = await cur.fetchone()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        cur = await db.execute("SELECT e.bank_account, e.bank_code, l.net, l.emp_id FROM payroll_lines l JOIN employees e ON e.id=l.emp_id WHERE l.run_id=? ORDER BY e.id", (run_id,))
        lines = await cur.fetchall()
        if not lines:
            raise HTTPException(status_code=404, detail="No lines")
        period = run["period"].replace("-","")
        tenant = run["tenant_id"]
        count = len(lines)
        # compute totals
        from decimal import Decimal
        gross_total = Decimal("0.00")
        net_total = Decimal("0.00")
        for r in lines:
            net_total += Decimal(r["net"])
        # need gross total from lines
        cur2 = await db.execute("SELECT SUM(CAST(gross AS REAL)) as g FROM payroll_lines WHERE run_id=?", (run_id,))
        g = await cur2.fetchone()
        gross_val = g["g"] or 0
        gross_str = format(Decimal(str(gross_val)), ".2f")
        net_str = format(net_total, ".2f")
        # Build fixed-width: H|TENANT|YYYYMM|COUNT|GROSS  T|COUNT|NET|COMP3-EXACT
        header = f"H|{tenant}|{period}|{count:06d}|{gross_str}"
        details = []
        for r in lines:
            acct = (r["bank_account"] or "").ljust(24)[:24].strip()
            amt = format(Decimal(r["net"]), ".2f")
            details.append(f"D|{r['bank_account']}|{amt}|{r['emp_id']}|{r['bank_code']}")
        trailer = f"T|{count:06d}|{net_str}|COMP3-EXACT"
        txt = "\n".join([header] + details + [trailer])
        if file_format == "csv":
            csv_lines = ["account,net,emp_id,bank"]
            for r in lines:
                csv_lines.append(f"{r['bank_account']},{r['net']},{r['emp_id']},{r['bank_code']}")
            return PlainTextResponse("\n".join(csv_lines), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=bank_{period}.csv"})
        return PlainTextResponse(txt, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename=bank_{period}.txt"})
