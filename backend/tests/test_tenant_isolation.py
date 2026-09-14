import pathlib, os, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
os.environ["DB_PATH"] = str(pathlib.Path(__file__).parent.parent / "db" / "smcpe.db")
os.environ["COBOL_LIB"] = str(pathlib.Path(__file__).parent.parent / "cobol" / "libpayroll.so")
from fastapi.testclient import TestClient
from backend.api.app import app
import sqlite3, pathlib

client = TestClient(app)

def _login(email, pwd="admin123"):
    # ensure password
    db_path = pathlib.Path(__file__).parent.parent / "db" / "smcpe.db"
    con = sqlite3.connect(str(db_path))
    from backend.api.security import hash_password
    h = hash_password(pwd)
    con.execute("UPDATE users SET password_hash=? WHERE email=?", (h, email))
    con.commit()
    con.close()
    r = client.post("/api/auth/login", json={"email": email, "password": pwd})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

def test_tenant_isolation():
    token = _login("owner@nileagro.sd")
    hdr = {"Authorization": f"Bearer {token}"}
    # owner can list own tenant
    r = client.get("/api/tenants", headers=hdr)
    assert r.status_code == 200
    tenants = r.json()["tenants"]
    # Should not leak other tenant data without filter? Our impl scopes to own unless owner
    # Create a second tenant employee and try to access
    # For now, ensure employees are tenant-scoped
    r = client.get("/api/employees?tenant=DEMO", headers=hdr)
    # owner can enumerate DEMO, but DEMO should have 0 employees (we seeded none for DEMO? Actually we seeded tenants DEMO but no employees)
    assert r.status_code == 200
    # Try to access non-existent tenant employee
    r = client.get("/api/employees/SD-0042", headers=hdr)  # SD-0042 is NA, should succeed
    assert r.status_code == 200
    # Create a DEMO employee directly via DB and try to access as NA owner should fail (IDOR)
    db_path = pathlib.Path(__file__).parent.parent / "db" / "smcpe.db"
    con = sqlite3.connect(str(db_path))
    try:
        con.execute("INSERT OR IGNORE INTO employees VALUES ('SD-9999','DEMO','Hacker','000','2020-01-01','SDG','100000.00','0.00','Y','000','BANK','2026-09-01T00:00:00Z')")
        con.commit()
        con.close()
        r = client.get("/api/employees/SD-9999", headers=hdr)
        assert r.status_code == 404, "Should not leak DEMO employee to NA owner via tenant filter"
    finally:
        con2 = sqlite3.connect(str(db_path))
        con2.execute("DELETE FROM employees WHERE id='SD-9999'")
        con2.commit()
        con2.close()

def test_money_strings():
    token = _login("owner@nileagro.sd")
    hdr = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/runs", json={"period": "2026-10"}, headers=hdr)
    assert r.status_code in (200,201)
    rid = r.json()["run_id"]
    r = client.post(f"/api/runs/{rid}/compute", headers=hdr)
    assert r.status_code == 200
    for line in r.json()["lines"]:
        for k in ["gross","nsif_emp","pit","net"]:
            v = line[k]
            assert isinstance(v, str), f"{k} not string {v}"
            assert "." in v and len(v.split(".")[1])==2, f"{k} not 2 decimals {v}"
            # no float
            assert isinstance(v, str)
