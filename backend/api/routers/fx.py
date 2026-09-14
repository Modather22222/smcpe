from fastapi import APIRouter, Depends, HTTPException
from ..schemas import FXLockIn
from .auth import require_user
import aiosqlite, os, pathlib, json

router = APIRouter(prefix="/api/fx", tags=["fx"])
DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).parent.parent.parent / "db" / "smcpe.db"))

@router.get("/history")
async def fx_history(currency: str = None, date: str = None, user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM fx_history ORDER BY date DESC, currency"
        params = ()
        if currency:
            q = "SELECT * FROM fx_history WHERE currency=? ORDER BY date DESC"
            params = (currency,)
        cur = await db.execute(q, params)
        rows = await cur.fetchall()
        return {"history": [dict(r) for r in rows]}

@router.get("")
async def get_fx(month: str = None, user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT currency, rate FROM fx_history WHERE source='locked' ORDER BY date DESC")
        rows = await cur.fetchall()
        rates = {r["currency"]: r["rate"] for r in rows}
        if not rates:
            cur = await db.execute("SELECT currency, rate FROM fx_history ORDER BY date DESC")
            rows = await cur.fetchall()
            rates = {r["currency"]: r["rate"] for r in rows}
        return {"rates": rates, "month": month}

@router.post("/lock")
async def lock_fx(body: FXLockIn, user=Depends(require_user)):
    if user["role"] not in ("owner","accountant"):
        raise HTTPException(status_code=403, detail="Only owner/accountant can lock FX")
    async with aiosqlite.connect(DB_PATH) as db:
        for cur, rate in body.rates.items():
            if cur not in ("USD","SAR","AED","SDG"):
                raise HTTPException(status_code=400, detail=f"Invalid currency {cur}")
            try:
                v = float(rate)
                if v <= 0 or v > 99999.9999:
                    raise ValueError()
            except:
                raise HTTPException(status_code=400, detail=f"Invalid rate {rate} for {cur}")
            await db.execute("INSERT OR REPLACE INTO fx_history (date, currency, rate, source, locked_by) VALUES (?,?,?,?,?)",
                             (body.date, cur, rate, "locked", user["sub"]))
            await db.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                             (user["sub"], "FX_LOCK", "00", json.dumps({"date": body.date, "currency": cur, "rate": rate})))
        await db.commit()
    return {"ok": True, "locked": body.rates}
