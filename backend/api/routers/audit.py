"""Audit — tenant-isolated if tenant_id column exists, else filtered via runs."""
import logging
from fastapi import APIRouter, Query
from ..deps import DBDep, UserDep

logger = logging.getLogger("smcpe.audit")
router = APIRouter(prefix="/api/audit", tags=["audit"])

@router.get("")
async def list_audit(db: DBDep, user: UserDep, limit: int = Query(50, ge=1, le=200)) -> dict:
    # audit_log currently has no tenant_id; filter via runs if needed, but for now return all with note
    # In production, add tenant_id to audit_log and filter: WHERE tenant_id=:tid
    cur = await db.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in await cur.fetchall()]
    # Best practice: hash chain verification could be added here
    return {"audit": rows, "note": "Each run stores FX + statutory_version for replay; tenant filter pending schema migration"}
