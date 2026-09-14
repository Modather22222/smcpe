from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from ..schemas import EmployeeIn
from .auth import require_user
import aiosqlite, os, pathlib, csv, io, uuid, datetime

router = APIRouter(prefix="/api/employees", tags=["employees"])
DB_PATH = os.getenv("DB_PATH", str(pathlib.Path(__file__).parent.parent.parent / "db" / "smcpe.db"))

@router.get("")
async def list_employees(tenant: str = None, user=Depends(require_user)):
    tenant_id = tenant or user["tenant_id"]
    if tenant_id != user["tenant_id"] and user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Tenant mismatch")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM employees WHERE tenant_id=? ORDER BY id", (tenant_id,))
        rows = await cur.fetchall()
        return {"employees": [dict(r) for r in rows]}

@router.post("")
async def create_employee(body: EmployeeIn, user=Depends(require_user)):
    emp_id = body.id or f"SD-{str(uuid.uuid4())[:4].upper()}"
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO employees (id, tenant_id, name, national_id, hire_date, base_currency, base_salary, allowances, nsif_eligible, bank_account, bank_code, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (emp_id, user["tenant_id"], body.name, body.national_id, body.hire_date, body.base_currency, body.base_salary, body.allowances, body.nsif_eligible, body.bank_account, body.bank_code, datetime.datetime.utcnow().isoformat())
            )
            await db.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    return {"id": emp_id}

@router.post("/import")
async def import_csv(file: UploadFile = File(...), user=Depends(require_user)):
    content = (await file.read()).decode()
    reader = csv.DictReader(io.StringIO(content))
    required = {"name","hire_date","base_currency","base_salary","allowances","nsif_eligible"}
    count, warnings = 0, 0
    async with aiosqlite.connect(DB_PATH) as db:
        for row in reader:
            if not required.issubset(row.keys()):
                raise HTTPException(status_code=400, detail=f"CSV missing columns {required}")
            # validate currency
            if row["base_currency"] not in ("SDG","USD","SAR","AED"):
                warnings += 1
                continue
            emp_id = row.get("id") or f"SD-{str(uuid.uuid4())[:4].upper()}"
            try:
                await db.execute(
                    "INSERT OR REPLACE INTO employees (id, tenant_id, name, national_id, hire_date, base_currency, base_salary, allowances, nsif_eligible, bank_account, bank_code, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (emp_id, user["tenant_id"], row["name"], row.get("national_id"), row["hire_date"], row["base_currency"], row["base_salary"], row["allowances"], row["nsif_eligible"], row.get("bank_account"), row.get("bank_code"), datetime.datetime.utcnow().isoformat())
                )
                count += 1
            except Exception:
                warnings += 1
        await db.commit()
    return {"imported": count, "warnings": warnings, "errors": 0}

@router.get("/{emp_id}")
async def get_employee(emp_id: str, user=Depends(require_user)):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM employees WHERE id=? AND tenant_id=?", (emp_id, user["tenant_id"]))
        row = await cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return dict(row)
