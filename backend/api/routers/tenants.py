"""Tenants — list, owner can enumerate all, others only own."""
import logging
from fastapi import APIRouter, HTTPException
from ..deps import DBDep, UserDep

logger = logging.getLogger("smcpe.tenants")
router = APIRouter(prefix="/api/tenants", tags=["tenants"])

@router.get("")
async def list_tenants(db: DBDep, user: UserDep) -> dict:
    # Best practice: scope to tenant unless owner
    if user["role"] == "owner":
        cur = await db.execute("SELECT * FROM tenants")
    else:
        cur = await db.execute("SELECT * FROM tenants WHERE id=?", (user["tenant_id"],))
    rows = [dict(r) for r in await cur.fetchall()]
    logger.debug("Tenants listed by %s role %s: %s", user["sub"], user["role"], len(rows))
    return {"tenants": rows}
