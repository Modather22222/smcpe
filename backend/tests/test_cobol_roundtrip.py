#!/usr/bin/env python3
"""COBOL roundtrip test — ctypes -> libpayroll.so vs Python Decimal mirror."""
import ctypes, decimal, pathlib, sys
from decimal import Decimal, ROUND_HALF_UP

lib_path = pathlib.Path(__file__).parent.parent / "cobol" / "libpayroll.so"
if not lib_path.exists():
    print(f"SKIP: {lib_path} not found, run make -C backend/cobol")
    sys.exit(0)

libcob = ctypes.CDLL("libcob.so.5")
libcob.cob_init(0, None)

lib = ctypes.CDLL(str(lib_path))

# GnuCOBOL mangles PROGRAM-ID PAYROLL-CALC -> PAYROLL__CALC
try:
    func = getattr(lib, "PAYROLL__CALC")
except AttributeError:
    # fallback try hyphen version
    func = getattr(lib, "PAYROLL-CALC")

# Define argtypes: two char buffers
func.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
func.restype = ctypes.c_int  # GnuCOBOL returns int

def cobol_compute(currency, base, allow, fx, nsif_flag="Y", version="v2026.09"):
    # Build input buffer 57 bytes
    def pad(s, n): return str(s)[:n].ljust(n).encode()
    inp = bytearray(57)
    inp[0:3] = pad(currency, 3)
    inp[3:18] = pad(base, 15)
    inp[18:33] = pad(allow, 15)
    inp[33:48] = pad(fx, 15)
    inp[48:49] = pad(nsif_flag, 1)
    inp[49:57] = pad(version, 8)
    out = ctypes.create_string_buffer(92)
    # COBOL expects pointers to structures
    # Need to pass by reference: ctypes uses c_char_p which expects bytes
    # Instead use create_string_buffer for inp too and pass pointer
    inp_buf = ctypes.create_string_buffer(bytes(inp), 57)
    res = func(inp_buf, out)
    # Parse output: 6 fields 15 chars + status 2
    raw = out.raw
    def get(off): return raw[off:off+15].decode().strip()
    gross = get(0)
    nsif_emp = get(15)
    nsif_co = get(30)
    taxable = get(45)
    pit = get(60)
    net = get(75)
    status = raw[90:92].decode().strip()
    return {"gross": gross, "nsif_emp": nsif_emp, "nsif_co": nsif_co, "taxable": taxable, "pit": pit, "net": net, "status": status, "raw": raw}

def py_compute(currency, base, allow, fx, nsif_flag="Y"):
    D = Decimal
    q = D("0.00")
    base_d = D(str(base))
    allow_d = D(str(allow))
    fx_d = D(str(fx))
    if fx_d <= 0:
        fx_d = D("1")
    if currency.upper() == "SDG":
        gross = (base_d + allow_d).quantize(q)
    else:
        gross = ((base_d + allow_d) * fx_d).quantize(q)
    if nsif_flag.upper() == "Y":
        nsif_emp = (gross * D("0.08")).quantize(q, rounding=ROUND_HALF_UP)
        nsif_co = (gross * D("0.17")).quantize(q, rounding=ROUND_HALF_UP)
    else:
        nsif_emp = D("0.00")
        nsif_co = D("0.00")
    taxable = (gross - nsif_emp).quantize(q) if gross > nsif_emp else D("0.00")
    free = D("50000.00")
    if taxable <= free:
        pit = D("0.00")
    else:
        remaining = taxable - free
        pit = D("0.00")
        prev = free
        tiers = [(D("100000.00"), D("0.05")), (D("200000.00"), D("0.10")), (D("400000.00"), D("0.15")), (D("999999999.00"), D("0.20"))]
        for limit, rate in tiers:
            bracket = limit - prev
            if remaining <= 0:
                break
            if remaining > bracket:
                pit += bracket * rate
                remaining -= bracket
            else:
                pit += remaining * rate
                remaining = D("0.00")
            prev = limit
        pit = pit.quantize(q, rounding=ROUND_HALF_UP)
    net = (gross - nsif_emp - pit).quantize(q)
    return {"gross": format(gross, ".2f"), "nsif_emp": format(nsif_emp, ".2f"), "nsif_co": format(nsif_co, ".2f"), "taxable": format(taxable, ".2f"), "pit": format(pit, ".2f"), "net": format(net, ".2f")}

def test_cobol_roundtrip():
    vectors = [
        ("USD", "1400.00", "220.00", "2610.50", "Y"),
        ("SDG", "850000.00", "120000.00", "1", "Y"),
        ("SAR", "5200.00", "800.00", "696.10", "N"),
        ("AED", "4800.00", "650.00", "710.85", "Y"),
    ]
    for cur, base, allow, fx, nsif in vectors:
        py = py_compute(cur, base, allow, fx, nsif)
        cb = cobol_compute(cur, base, allow, fx, nsif)
        for k in ["gross","nsif_emp","taxable","pit","net"]:
            assert py[k] == cb[k], f"{cur} {k} mismatch py {py[k]} vs cob {cb[k]}"
    # edge
    for cur, base, allow, fx, nsif in [("SDG","0.00","0.00","1","Y"), ("USD","0.01","0.00","2610.50","Y"), ("SDG","50000.00","0.00","1","Y")]:
        py = py_compute(cur, base, allow, fx, nsif)
        cb = cobol_compute(cur, base, allow, fx, nsif)
        assert py["net"] == cb["net"]

if __name__ == "__main__":
    vectors = [
        ("USD", "1400.00", "220.00", "2610.50", "Y"),
        ("SDG", "850000.00", "120000.00", "1", "Y"),
        ("SAR", "5200.00", "800.00", "696.10", "N"),
        ("AED", "4800.00", "650.00", "710.85", "Y"),
    ]
    print("=== COBOL vs Python Decimal ===")
    all_ok = True
    for cur, base, allow, fx, nsif in vectors:
        py = py_compute(cur, base, allow, fx, nsif)
        cb = cobol_compute(cur, base, allow, fx, nsif)
        print(f"\n{cur} {base}+{allow} x{fx} NSIF={nsif}")
        print(f"  PY  gross={py['gross']} nsif_emp={py['nsif_emp']} taxable={py['taxable']} pit={py['pit']} net={py['net']}")
        print(f"  COB gross={cb['gross']} nsif_emp={cb['nsif_emp']} taxable={cb['taxable']} pit={cb['pit']} net={cb['net']} status={cb['status']}")
        for k in ["gross","nsif_emp","taxable","pit","net"]:
            if py[k] != cb[k]:
                print(f"  ❌ mismatch {k}: py {py[k]} vs cob {cb[k]}")
                all_ok = False
            else:
                print(f"  ✅ {k} ok")
    print("\n=== Edge ===")
    edge = [
        ("SDG", "0.00", "0.00", "1", "Y", py_compute("SDG","0.00","0.00","1","Y")),
        ("USD", "0.01", "0.00", "2610.50", "Y", None),
        ("SDG", "50000.00", "0.00", "1", "Y", None),
    ]
    for cur, base, allow, fx, nsif, exp in edge:
        py = py_compute(cur, base, allow, fx, nsif)
        cb = cobol_compute(cur, base, allow, fx, nsif)
        print(f"{cur} {base} -> py net {py['net']} cb net {cb['net']} status {cb['status']}")
    if all_ok:
        print("\n✅ COMP-3 roundtrip OK")
        sys.exit(0)
    else:
        print("\n❌ Some mismatches")
        sys.exit(1)
