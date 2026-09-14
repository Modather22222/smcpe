#!/usr/bin/env python3
"""Bank export worker — generates H|D|T fixed-width from payroll_lines, mirroring /api/bank/file"""
import pathlib, os, json, sys
from decimal import Decimal
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
os.environ.setdefault("DB_PATH", str(pathlib.Path(__file__).parent.parent / "db" / "smcpe.db"))
import sqlite3

DB_PATH = os.getenv("DB_PATH")
def export_run(run_id: str) -> str:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.execute("SELECT * FROM payroll_runs WHERE id=?", (run_id,))
    run = cur.fetchone()
    if not run:
        raise SystemExit(f"Run {run_id} not found")
    cur = con.execute("SELECT e.bank_account, e.bank_code, l.net, l.emp_id, l.gross FROM payroll_lines l JOIN employees e ON e.id=l.emp_id WHERE l.run_id=? ORDER BY e.id", (run_id,))
    lines = cur.fetchall()
    period = run["period"].replace("-", "")
    tenant = run["tenant_id"]
    count = len(lines)
    gross_total = sum((Decimal(str(r["gross"])) for r in lines), Decimal("0.00"))
    net_total = sum((Decimal(str(r["net"])) for r in lines), Decimal("0.00"))
    header = f"H|{tenant}|{period}|{count:06d}|{format(gross_total, '.2f')}"
    details = [f"D|{r['bank_account']}|{format(Decimal(r['net']), '.2f')}|{r['emp_id']}|{r['bank_code']}" for r in lines]
    trailer = f"T|{count:06d}|{format(net_total, '.2f')}|COMP3-EXACT"
    txt = "\n".join([header] + details + [trailer])
    out_path = pathlib.Path(__file__).parent.parent / "data" / "runs" / run["period"] / f"bank_{run_id}.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(txt)
    print(f"Wrote {out_path} ({len(txt)} bytes)")
    return str(out_path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: bank_export.py <run_id>")
        # demo: export latest
        con = sqlite3.connect(DB_PATH)
        cur = con.execute("SELECT id FROM payroll_runs ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            export_run(row[0])
        else:
            print("No runs")
    else:
        export_run(sys.argv[1])
