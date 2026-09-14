from fastapi import APIRouter, Depends, HTTPException
from ..schemas import StatutoryIn
from .auth import require_user
import aiosqlite, os, pathlib, json

router = APIRouter(prefix="/api/statutory", tags=["statutory"])
DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).parent.parent.parent / "db" / "smcpe.db"))

@router.get("")
async def list_statutory(user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM statutory_tables ORDER BY version DESC")
        rows = [dict(r) for r in await cur.fetchall()]
        return {"tables": rows}

@router.post("")
async def publish_statutory(body: StatutoryIn, user=Depends(require_user)):
    if user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Only owner can publish")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO statutory_tables (version, nsif_emp, nsif_co, tax_free, tiers_json, published_at) VALUES (?,?,?,?,?,datetime('now'))",
            (body.version, body.nsif_emp, body.nsif_co, body.tax_free, body.tiers_json)
        )
        await db.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                         (user["sub"], "STATUTORY_PUBLISH", "00", json.dumps({"version": body.version})))
        await db.commit()
    return {"ok": True, "version": body.version}
