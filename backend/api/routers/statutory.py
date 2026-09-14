"""Statutory — versioned, owner only publish, immutable old runs."""
import json
import logging
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from ..deps import DBDep, UserDep, require_role
from ..schemas import StatutoryIn

logger = logging.getLogger("smcpe.statutory")
router = APIRouter(prefix="/api/statutory", tags=["statutory"])

@router.get("")
async def list_statutory(db: DBDep, user: UserDep) -> dict:
    cur = await db.execute("SELECT * FROM statutory_tables ORDER BY version DESC")
    rows = [dict(r) for r in await cur.fetchall()]
    return {"tables": rows}

@router.post("", status_code=201)
async def publish_statutory(body: StatutoryIn, db: DBDep, user: Annotated[dict, Depends(require_role("owner"))]) -> dict:
    await db.execute(
        "INSERT OR REPLACE INTO statutory_tables (version, nsif_emp, nsif_co, tax_free, tiers_json, published_at) VALUES (?,?,?,?,?,datetime('now'))",
        (body.version, body.nsif_emp, body.nsif_co, body.tax_free, body.tiers_json),
    )
    await db.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                     (user["sub"], "STATUTORY_PUBLISH", "00", json.dumps({"version": body.version})))
    await db.commit()
    logger.info("Statutory %s published by %s", body.version, user["sub"])
    return {"ok": True, "version": body.version}
