import ctypes, pathlib, os, decimal
from decimal import Decimal, ROUND_HALF_UP

LIB_PATH = pathlib.Path(os.getenv("COBOL_LIB", str(pathlib.Path(__file__).parent.parent / "cobol" / "libpayroll.so")))

_lib = None
_func = None

def _init_lib():
    global _lib, _func
    if _lib is not None:
        return
    if not LIB_PATH.exists():
        return
    try:
        libcob = ctypes.CDLL("libcob.so.5")
        libcob.cob_init(0, None)
    except Exception:
        pass
    try:
        _lib = ctypes.CDLL(str(LIB_PATH))
        _func = getattr(_lib, "PAYROLL__CALC")
        _func.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        _func.restype = ctypes.c_int
    except Exception as e:
        print(f"payroll_lib: failed to load {LIB_PATH}: {e}")
        _lib = None
        _func = None

def _pad(s, n):
    return str(s)[:n].ljust(n).encode()

def compute_payroll(currency: str, base_salary: str, allowances: str, fx_rate: str, nsif_flag: str = "Y", version: str = "v2026.09"):
    """Try COBOL first, fallback to Python Decimal. Returns dict with strings 2 decimals."""
    _init_lib()
    if _func is not None:
        try:
            inp = bytearray(57)
            inp[0:3] = _pad(currency, 3)
            inp[3:18] = _pad(base_salary, 15)
            inp[18:33] = _pad(allowances, 15)
            inp[33:48] = _pad(fx_rate, 15)
            inp[48:49] = _pad(nsif_flag, 1)
            inp[49:57] = _pad(version, 8)
            out = ctypes.create_string_buffer(92)
            inp_buf = ctypes.create_string_buffer(bytes(inp), 57)
            _func(inp_buf, out)
            raw = out.raw
            def get(off): return raw[off:off+15].decode().strip() or "0.00"
            # normalize to 2 decimals
            def norm(s):
                try:
                    d = Decimal(s)
                    return format(d.quantize(Decimal("0.00")), ".2f")
                except:
                    return s
            return {
                "gross": norm(get(0)),
                "nsif_emp": norm(get(15)),
                "nsif_co": norm(get(30)),
                "taxable": norm(get(45)),
                "pit": norm(get(60)),
                "net": norm(get(75)),
                "status": raw[90:92].decode().strip(),
                "engine": "cobol"
            }
        except Exception as e:
            print(f"COBOL compute failed, fallback: {e}")

    # Python fallback (Decimal, same tiers as COBOL)
    D = Decimal
    q = D("0.00")
    base_d = D(str(base_salary))
    allow_d = D(str(allowances))
    fx_d = D(str(fx_rate))
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
    return {
        "gross": format(gross, ".2f"),
        "nsif_emp": format(nsif_emp, ".2f"),
        "nsif_co": format(nsif_co, ".2f"),
        "taxable": format(taxable, ".2f"),
        "pit": format(pit, ".2f"),
        "net": format(net, ".2f"),
        "status": "00",
        "engine": "python"
    }

def compute_esg(years: str, monthly: str):
    D = Decimal
    y = D(str(years))
    m = D(str(monthly))
    if y < D("3"):
        factor = D("0.33")
        years_int = int(y.to_integral_value(rounding=ROUND_HALF_UP)) if y < 3 else y
        # For <3, use integer years as per COBOL INTEGER
        accrual = m * factor * D(str(int(y)))
    elif y < D("5"):
        factor = D("0.50")
        accrual = m * factor * y
    elif y < D("10"):
        factor = D("1.00")
        accrual = m * factor * y
    else:
        factor = D("1.50")
        accrual = m * factor * y
    q = D("0.00")
    accrual = accrual.quantize(q, rounding=ROUND_HALF_UP)
    return format(accrual, ".2f")
