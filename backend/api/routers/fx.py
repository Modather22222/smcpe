"""FX — tenant-isolated, Decimal exact, validated S9(5)V9(4)."""
import json
import logging
from decimal import Decimal, InvalidOperation
from typing import Annotated
from fastapi import APIRouter, Depends, Query
from ..deps import DBDep, UserDep, require_role
from ..schemas import FXLockIn

logger = logging.getLogger("smcpe.fx")
router = APIRouter(prefix="/api/fx", tags=["fx"])

@router.get("/history")
async def fx_history(db: DBDep, user: UserDep, currency: str | None = Query(None, pattern="^(USD|SAR|AED|SDG)$")) -> dict:
    q = "SELECT * FROM fx_history ORDER BY date DESC, currency"
    params: tuple = ()
    if currency:
        q = "SELECT * FROM fx_history WHERE currency=? ORDER BY date DESC"
        params = (currency,)
    cur = await db.execute(q, params)
    rows = await cur.fetchall()
    return {"history": [dict(r) for r in rows]}

@router.get("")
async def get_fx(db: DBDep, user: UserDep, month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$")) -> dict:
    cur = await db.execute("SELECT currency, rate FROM fx_history WHERE source='locked' ORDER BY date DESC")
    rows = await cur.fetchall()
    rates = {r["currency"]: r["rate"] for r in rows}
    if not rates:
        cur = await db.execute("SELECT currency, rate FROM fx_history ORDER BY date DESC")
        rows = await cur.fetchall()
        rates = {r["currency"]: r["rate"] for r in rows}
    return {"rates": rates, "month": month}

@router.post("/lock")
async def lock_fx(body: FXLockIn, db: DBDep, user: Annotated[dict, Depends(require_role("owner", "accountant"))]) -> dict:
    for cur, rate in body.rates.items():
        if cur not in ("USD", "SAR", "AED", "SDG"):
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail=f"Invalid currency {cur}")
        try:
            v = Decimal(rate)
            if v <= 0 or v > Decimal("99999.9999"):
                raise ValueError()
            # quantize to 4 decimals exact
            v.quantize(Decimal("0.0000"))
        except (InvalidOperation, ValueError, AttributeError):
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail=f"Invalid rate {rate} for {cur}")
        await db.execute("INSERT OR REPLACE INTO fx_history (date, currency, rate, source, locked_by) VALUES (?,?,?,?,?)",
                         (body.date, cur, rate, "locked", user["sub"]))
        await db.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                         (user["sub"], "FX_LOCK", "00", json.dumps({"date": body.date, "currency": cur, "rate": rate})))
    await db.commit()
    logger.info("FX locked %s by %s", body.rates, user["sub"])
    return {"ok": True, "locked": body.rates}
