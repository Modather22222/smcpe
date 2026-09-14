"""Bank — H|D|T fixed-width, Decimal sums, tenant-isolated."""
import logging
from decimal import Decimal
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from ..deps import DBDep, UserDep

logger = logging.getLogger("smcpe.bank")
router = APIRouter(prefix="/api/bank", tags=["bank"])

@router.get("/file")
async def bank_file(
    run_id: str,
    db: DBDep,
    user: UserDep,
    file_format: str = Query("txt", alias="format", pattern="^(txt|csv)$"),
) -> PlainTextResponse:
    cur = await db.execute("SELECT * FROM payroll_runs WHERE id=? AND tenant_id=?", (run_id, user["tenant_id"]))
    run = await cur.fetchone()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    cur = await db.execute("SELECT e.bank_account, e.bank_code, l.net, l.emp_id FROM payroll_lines l JOIN employees e ON e.id=l.emp_id WHERE l.run_id=? ORDER BY e.id", (run_id,))
    lines = await cur.fetchall()
    if not lines:
        raise HTTPException(status_code=404, detail="No lines for run")
    period = run["period"].replace("-", "")
    tenant = run["tenant_id"]
    count = len(lines)
    gross_total = Decimal("0.00")
    net_total = Decimal("0.00")
    # Sum gross via Decimal, not SUM(CAST(... AS REAL))
    cur2 = await db.execute("SELECT gross, net FROM payroll_lines WHERE run_id=?", (run_id,))
    for r in await cur2.fetchall():
        gross_total += Decimal(r["gross"])
        net_total += Decimal(r["net"])
    gross_str = format(gross_total, ".2f")
    net_str = format(net_total, ".2f")
    header = f"H|{tenant}|{period}|{count:06d}|{gross_str}"
    details = [f"D|{r['bank_account']}|{format(Decimal(r['net']), '.2f')}|{r['emp_id']}|{r['bank_code']}" for r in lines]
    trailer = f"T|{count:06d}|{net_str}|COMP3-EXACT"
    txt = "\n".join([header] + details + [trailer])
    logger.info("Bank file %s for tenant %s: %s lines gross %s net %s", run_id, tenant, count, gross_str, net_str)
    if file_format == "csv":
        csv_lines = ["account,net,emp_id,bank"]
        for r in lines:
            csv_lines.append(f"{r['bank_account']},{r['net']},{r['emp_id']},{r['bank_code']}")
        return PlainTextResponse("\n".join(csv_lines), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=bank_{period}.csv"})
    return PlainTextResponse(txt, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename=bank_{period}.txt"})
