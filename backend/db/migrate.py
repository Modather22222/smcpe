#!/usr/bin/env python3
import pathlib, sqlite3, os, sys

ROOT = pathlib.Path(__file__).parent
DB_PATH = pathlib.Path(os.getenv("DB_PATH", ROOT / "smcpe.db"))
SCHEMA = ROOT / "schema.sql"
SEED = ROOT / "seed.sql"

def migrate():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.executescript("PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;")
    print(f"Migrating {DB_PATH} from {SCHEMA}")
    con.executescript(SCHEMA.read_text())
    if SEED.exists():
        print(f"Seeding from {SEED}")
        con.executescript(SEED.read_text())
    con.commit()
    # Verify
    cur = con.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"Tables: {tables}")
    for tbl in ["tenants","employees","fx_history","statutory_tables"]:
        cnt = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"  {tbl}: {cnt} rows")
    con.execute("PRAGMA integrity_check")
    print("Integrity OK")
    con.close()

if __name__ == "__main__":
    migrate()
