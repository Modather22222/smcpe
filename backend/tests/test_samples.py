"""Samples integrity — CSVs parse, totals match COBOL, checksums, bank file."""
import pathlib, os, sys, csv, json, hashlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))
os.environ["DB_PATH"] = str(pathlib.Path(__file__).parent.parent / "db" / "smcpe.db")
os.environ["COBOL_LIB"] = str(pathlib.Path(__file__).parent.parent / "cobol" / "libpayroll.so")

SAMPLES = pathlib.Path(__file__).parent.parent.parent / "samples"

def test_samples_exist():
    for f in ["employees_sample.csv","employees_42.csv","fx_rates.json","statutory_v2026.09.json","payroll_run_2026-09_12.json","bank_file_sample.txt","payslip_sample_SD-0042.txt","manifest.json","checksums.sha256"]:
        assert (SAMPLES / f).exists(), f"missing {f}"

def test_employees_csv():
    with open(SAMPLES / "employees_sample.csv", encoding="utf-8") as f:
        r = list(csv.DictReader(f))
        assert len(r) == 12
        assert set(r[0].keys()) == {"id","name","national_id","hire_date","base_currency","base_salary","allowances","nsif_eligible","bank_account","bank_code"}
        # edges
        by_id = {x["id"]: x for x in r}
        assert by_id["SD-0044"]["nsif_eligible"] == "N"  # contractor
        assert by_id["SD-0051"]["base_salary"] == "0.00"  # zero
        assert by_id["SD-0042"]["base_currency"] == "USD"
    with open(SAMPLES / "employees_42.csv", encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 42

def test_expected_totals_match_cobol():
    from backend.api.payroll_lib import compute_payroll
    from decimal import Decimal
    exp = json.loads((SAMPLES / "payroll_run_2026-09_12.json").read_text())
    rates = {"USD": "2610.5000", "SAR": "696.1000", "AED": "710.8500", "SDG": "1.0000"}
    totals = {"gross": Decimal("0"), "nsif_emp": Decimal("0"), "pit": Decimal("0"), "net": Decimal("0")}
    with open(SAMPLES / "employees_sample.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            res = compute_payroll(row["base_currency"], row["base_salary"], row["allowances"], rates[row["base_currency"]], row["nsif_eligible"], "v2026.09")
            for k in totals:
                totals[k] += Decimal(res[k])
    for k in totals:
        assert format(totals[k], ".2f") == exp["totals"][k], f"{k} mismatch {totals[k]} vs {exp['totals'][k]}"

def test_bank_sample_format():
    txt = (SAMPLES / "bank_file_sample.txt").read_text()
    assert txt.endswith("\n"), "bank file must end with newline (POSIX)"
    lines = txt.strip().split("\n")
    assert len(lines) == 14  # H + 12 D + T
    assert lines[0].startswith("H|NA|202609|000012|")
    assert lines[-1].startswith("T|000012|") and lines[-1].endswith("|COMP3-EXACT")
    exp = json.loads((SAMPLES / "payroll_run_2026-09_12.json").read_text())
    assert exp["totals"]["gross"] in lines[0]
    assert exp["totals"]["net"] in lines[-1]

def test_checksums():
    # verify manifest files exist and checksums file is parseable
    manifest = json.loads((SAMPLES / "manifest.json").read_text())
    assert manifest["statutory_version"] == "v2026.09"
    # recompute one checksum to ensure file not corrupted
    h = hashlib.sha256((SAMPLES / "employees_sample.csv").read_bytes()).hexdigest()
    checks = (SAMPLES / "checksums.sha256").read_text()
    assert "employees_sample.csv" in checks
    assert h in checks
