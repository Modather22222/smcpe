import pathlib, os, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
os.environ["DB_PATH"] = str(pathlib.Path(__file__).parent.parent / "db" / "smcpe.db")
os.environ["COBOL_LIB"] = str(pathlib.Path(__file__).parent.parent / "cobol" / "libpayroll.so")
from fastapi.testclient import TestClient
from backend.api.app import app
from backend.api.security import hash_password
import aiosqlite, asyncio, pathlib

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert "libpayroll" in j["lib"]

def test_login_and_employees():
    # ensure user exists with known password admin123
    db_path = pathlib.Path(__file__).parent.parent / "db" / "smcpe.db"
    # reset password to admin123 for test
    import sqlite3
    con = sqlite3.connect(str(db_path))
    from backend.api.security import hash_password
    h = hash_password("admin123")
    con.execute("UPDATE users SET password_hash=? WHERE email='owner@nileagro.sd'", (h,))
    con.commit()
    con.close()
    r = client.post("/api/auth/login", json={"email":"owner@nileagro.sd","password":"admin123"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    hdr = {"Authorization": f"Bearer {token}"}
    # employees
    r = client.get("/api/employees", headers=hdr)
    assert r.status_code == 200
    assert len(r.json()["employees"]) >= 4
    # fx
    r = client.get("/api/fx/history", headers=hdr)
    assert r.status_code == 200
    # statutory
    r = client.get("/api/statutory", headers=hdr)
    assert r.status_code == 200
    # runs create + compute
    r = client.post("/api/runs", json={"period":"2026-09"}, headers=hdr)
    assert r.status_code == 200, r.text
    run_id = r.json()["run_id"]
    r = client.post(f"/api/runs/{run_id}/compute", headers=hdr)
    assert r.status_code == 200, r.text
    totals = r.json()["totals"]
    # verify totals are strings 2 decimals
    for k in ["gross","net"]:
        assert "." in totals[k]
    # bank file
    r = client.get(f"/api/bank/file?run_id={run_id}", headers=hdr)
    assert r.status_code == 200
    assert "H|" in r.text
    assert "COMP3-EXACT" in r.text
    # reports
    r = client.get(f"/api/reports/nsif?run_id={run_id}", headers=hdr)
    assert r.status_code == 200
    r = client.get(f"/api/reports/pit?run_id={run_id}", headers=hdr)
    assert r.status_code == 200
