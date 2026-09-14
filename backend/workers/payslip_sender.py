#!/usr/bin/env python3
"""Payslip sender stub — queue + WhatsApp/Telegram webhook, fallback SMS"""
import pathlib, os, json, sys, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
os.environ.setdefault("DB_PATH", str(pathlib.Path(__file__).parent.parent / "db" / "smcpe.db"))
import sqlite3

DB_PATH = os.getenv("DB_PATH")
TEMPLATE = pathlib.Path(__file__).parent.parent / "templates" / "payslip.txt"

def render_payslip(emp, line, run):
    fx_snapshot = json.loads(run["fx_snapshot_json"])
    fx_rate = fx_snapshot.get(emp["base_currency"], "1.0000") if emp["base_currency"]!="SDG" else "1.0000"
    tpl = TEMPLATE.read_text()
    # compute net_fx if needed
    from decimal import Decimal
    net_fx = line["net"]
    if emp["base_currency"]!="SDG":
        try:
            net_fx = format(Decimal(line["net"]) / Decimal(fx_rate), ".2f")
        except:
            net_fx = line["net"]
    return tpl.format(
        period=run["period"], tenant=run["tenant_id"], name=emp["name"], emp_id=emp["id"],
        national_id=emp["national_id"] or "", hire_date=emp["hire_date"], currency=emp["base_currency"],
        nsif_flag=emp["nsif_eligible"], base_salary=emp["base_salary"], allowances=emp["allowances"],
        fx_rate=fx_rate, gross=line["gross"], nsif_emp=line["nsif_emp"], nsif_co=line["nsif_co"],
        taxable=line["taxable"], pit=line["pit"], zakat="0.00", net=line["net"], net_fx=net_fx,
        bank_code=emp["bank_code"] or "", bank_account=emp["bank_account"] or "",
        statutory_version=run["statutory_version"], fx_date=run["created_at"][:10]
    )

def queue_payslips(run_id: str):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.execute("SELECT * FROM payroll_runs WHERE id=?", (run_id,))
    run = cur.fetchone()
    if not run:
        print(f"Run {run_id} not found")
        return
    cur = con.execute("SELECT l.*, e.* FROM payroll_lines l JOIN employees e ON e.id=l.emp_id WHERE l.run_id=?", (run_id,))
    rows = cur.fetchall()
    out_dir = pathlib.Path(__file__).parent.parent / "data" / "runs" / run["period"]
    out_dir.mkdir(parents=True, exist_ok=True)
    for r in rows:
        # r has both l.* and e.* ; need to fetch emp separately for template
        emp = {k: r[k] for k in ["id","name","national_id","hire_date","base_currency","base_salary","allowances","nsif_eligible","bank_account","bank_code"] if k in r.keys()}
        # Actually above keys are ambiguous; fetch emp separately
        emp_cur = con.execute("SELECT * FROM employees WHERE id=?", (r["emp_id"],))
        emp = emp_cur.fetchone()
        line = {k: r[k] for k in ["gross","nsif_emp","nsif_co","taxable","pit","net"]}
        txt = render_payslip(dict(emp), line, dict(run))
        path = out_dir / f"payslip_{r['emp_id']}_{run_id}.txt"
        path.write_text(txt)
        print(f"Queued {path} ({len(txt)} bytes) — WhatsApp stub: would send to {emp['bank_account']}")
        # simulate delivery log
        con.execute("INSERT INTO audit_log (time, actor, action, hash, payload_json) VALUES (datetime('now'),?,?,?,?)",
                    ("system", "PAYSLIP_QUEUED", "00", json.dumps({"run_id": run_id, "emp_id": r["emp_id"], "size": len(txt)})))
    con.commit()
    print(f"Queued {len(rows)} payslips for {run_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: payslip_sender.py <run_id>")
        con = sqlite3.connect(DB_PATH)
        cur = con.execute("SELECT id FROM payroll_runs ORDER BY created_at DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            queue_payslips(row[0])
    else:
        queue_payslips(sys.argv[1])
