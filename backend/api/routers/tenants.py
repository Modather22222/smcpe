from fastapi import APIRouter, Depends
from .auth import require_user
import aiosqlite, os, pathlib

router = APIRouter(prefix="/api/tenants", tags=["tenants"])
DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).parent.parent.parent / "db" / "smcpe.db"))

@router.get("")
async def list_tenants(user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM tenants")
        rows = [dict(r) for r in await cur.fetchall()]
        return {"tenants": rows}
