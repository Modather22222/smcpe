"""Employees — tenant-isolated CRUD + CSV import, money as TEXT, validated."""
import csv
import io
import uuid
import datetime
import logging
from typing import Annotated
from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from ..schemas import EmployeeIn
from ..deps import DBDep, UserDep, require_role

logger = logging.getLogger("smcpe.employees")
router = APIRouter(prefix="/api/employees", tags=["employees"])

@router.get("")
async def list_employees(
    db: DBDep,
    user: UserDep,
    tenant: str | None = Query(None, description="Tenant filter, owner only"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    tenant_id = tenant or user["tenant_id"]
    if tenant_id != user["tenant_id"] and user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    cur = await db.execute("SELECT * FROM employees WHERE tenant_id=? ORDER BY id LIMIT ? OFFSET ?", (tenant_id, limit, offset))
    rows = await cur.fetchall()
    return {"employees": [dict(r) for r in rows], "limit": limit, "offset": offset}

@router.post("", status_code=201)
async def create_employee(body: EmployeeIn, db: DBDep, user: UserDep) -> dict:
    emp_id = body.id or f"SD-{uuid.uuid4().hex[:4].upper()}"
    try:
        await db.execute(
            "INSERT INTO employees (id, tenant_id, name, national_id, hire_date, base_currency, base_salary, allowances, nsif_eligible, bank_account, bank_code, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (emp_id, user["tenant_id"], body.name, body.national_id, body.hire_date, body.base_currency, body.base_salary, body.allowances, body.nsif_eligible, body.bank_account, body.bank_code, datetime.datetime.now(datetime.timezone.utc).isoformat()),
        )
        await db.commit()
        logger.info("Employee %s created by %s tenant %s", emp_id, user["sub"], user["tenant_id"])
    except Exception as e:
        await db.rollback()
        logger.exception("Create employee failed %s", emp_id)
        raise HTTPException(status_code=400, detail=str(e))
    return {"id": emp_id}

@router.post("/import")
async def import_csv(file: Annotated[UploadFile, File(...)], db: DBDep, user: UserDep) -> dict:
    if file.content_type not in ("text/csv", "application/vnd.ms-excel", "text/plain", None):
        logger.warning("Import with content-type %s", file.content_type)
    content = (await file.read()).decode("utf-8-sig")
    try:
        reader = csv.DictReader(io.StringIO(content))
        if reader.fieldnames is None:
            raise HTTPException(status_code=400, detail="CSV empty or missing header")
        required = {"name", "hire_date", "base_currency", "base_salary", "allowances", "nsif_eligible"}
        if not required.issubset(set(reader.fieldnames)):
            raise HTTPException(status_code=400, detail=f"CSV missing columns {required}, got {reader.fieldnames}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")

    count = warnings = 0
    for row in reader:
        if row["base_currency"] not in ("SDG", "USD", "SAR", "AED"):
            warnings += 1
            logger.debug("Skip row bad currency %s", row)
            continue
        emp_id = row.get("id") or f"SD-{uuid.uuid4().hex[:4].upper()}"
        try:
            await db.execute(
                "INSERT OR REPLACE INTO employees (id, tenant_id, name, national_id, hire_date, base_currency, base_salary, allowances, nsif_eligible, bank_account, bank_code, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (emp_id, user["tenant_id"], row["name"], row.get("national_id"), row["hire_date"], row["base_currency"], row["base_salary"], row["allowances"], row["nsif_eligible"], row.get("bank_account"), row.get("bank_code"), datetime.datetime.now(datetime.timezone.utc).isoformat()),
            )
            count += 1
        except Exception:
            warnings += 1
            logger.exception("Import row failed %s", row.get("name"))
    await db.commit()
    logger.info("CSV import %s by %s: %s imported, %s warnings", file.filename, user["sub"], count, warnings)
    return {"imported": count, "warnings": warnings, "errors": 0}

@router.get("/{emp_id}")
async def get_employee(emp_id: str, db: DBDep, user: UserDep) -> dict:
    cur = await db.execute("SELECT * FROM employees WHERE id=? AND tenant_id=?", (emp_id, user["tenant_id"]))
    row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Not found")
    return dict(row)
