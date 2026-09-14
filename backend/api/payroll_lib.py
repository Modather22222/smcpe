"""Payroll lib — COBOL COMP-3 via ctypes with Decimal fallback, strict 2-decimal, logged."""
import ctypes
import logging
import pathlib
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from .config import settings

logger = logging.getLogger("smcpe.payroll_lib")

LIB_PATH = pathlib.Path(settings.COBOL_LIB)
_lib: ctypes.CDLL | None = None
_func = None
_inited = False

def _init_lib() -> None:
    global _lib, _func, _inited
    if _inited:
        return
    _inited = True
    if not LIB_PATH.exists():
        logger.warning("COBOL lib not found %s, using Python fallback", LIB_PATH)
        return
    try:
        libcob = ctypes.CDLL("libcob.so.5")
        libcob.cob_init(0, None)
        logger.debug("libcob initialized")
    except Exception as e:
        logger.warning("libcob init failed: %s", e)
    try:
        _lib = ctypes.CDLL(str(LIB_PATH))
        _func = getattr(_lib, "PAYROLL__CALC")
        _func.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        _func.restype = ctypes.c_int
        logger.info("Loaded COBOL lib %s (%s bytes)", LIB_PATH, LIB_PATH.stat().st_size)
    except Exception as e:
        logger.error("Failed to load %s: %s", LIB_PATH, e)
        _lib = None
        _func = None

def _pad(s: str, n: int) -> bytes:
    return str(s)[:n].ljust(n).encode()

def _quantize_2(d: Decimal) -> Decimal:
    return d.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

def _norm_money(s: str) -> str:
    try:
        return format(Decimal(s).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP), ".2f")
    except (InvalidOperation, ValueError, AttributeError) as e:
        logger.warning("norm_money failed for %r: %s", s, e)
        return "0.00"

def compute_payroll(
    currency: str,
    base_salary: str,
    allowances: str,
    fx_rate: str,
    nsif_flag: str = "Y",
    version: str = "v2026.09",
) -> dict:
    """Try COBOL first (COMP-3, ROUNDED only at NSIF/PIT), fallback to Decimal mirror.

    All money strings are \"0.00\" 2-decimal, FX \"0.0000\" 4-decimal. Never float.
    """
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
            rc = _func(inp_buf, out)
            if rc != 0:
                logger.warning("COBOL PAYROLL__CALC returned %s", rc)
            raw = out.raw
            def get(off: int) -> str:
                return raw[off:off+15].decode().strip() or "0.00"
            return {
                "gross": _norm_money(get(0)),
                "nsif_emp": _norm_money(get(15)),
                "nsif_co": _norm_money(get(30)),
                "taxable": _norm_money(get(45)),
                "pit": _norm_money(get(60)),
                "net": _norm_money(get(75)),
                "status": raw[90:92].decode().strip() or "00",
                "engine": "cobol",
            }
        except Exception as e:
            logger.exception("COBOL compute failed, fallback to Python: %s", e)

    # Python fallback — Decimal, same tiers as COBOL, all quantize ROUND_HALF_UP
    try:
        base_d = Decimal(str(base_salary))
        allow_d = Decimal(str(allowances))
        fx_d = Decimal(str(fx_rate))
    except InvalidOperation as e:
        logger.error("Invalid Decimal input %s/%s/%s: %s", base_salary, allowances, fx_rate, e)
        raise ValueError(f"Invalid money/fx: {e}") from e
    if fx_d <= 0:
        logger.warning("FX %s <=0, fallback 1.0000", fx_d)
        fx_d = Decimal("1.0000")
    q = Decimal("0.00")
    if currency.upper() == "SDG":
        gross = _quantize_2(base_d + allow_d)
    else:
        gross = _quantize_2((base_d + allow_d) * fx_d)
    if nsif_flag.upper() == "Y":
        nsif_emp = _quantize_2(gross * Decimal("0.08"))
        nsif_co = _quantize_2(gross * Decimal("0.17"))
    else:
        nsif_emp = Decimal("0.00")
        nsif_co = Decimal("0.00")
    taxable = _quantize_2(gross - nsif_emp) if gross > nsif_emp else Decimal("0.00")
    free = Decimal("50000.00")
    if taxable <= free:
        pit = Decimal("0.00")
    else:
        remaining = taxable - free
        pit = Decimal("0.00")
        prev = free
        tiers = [
            (Decimal("100000.00"), Decimal("0.05")),
            (Decimal("200000.00"), Decimal("0.10")),
            (Decimal("400000.00"), Decimal("0.15")),
            (Decimal("999999999.00"), Decimal("0.20")),
        ]
        for limit, rate in tiers:
            bracket = limit - prev
            if remaining <= 0:
                break
            if remaining > bracket:
                pit += bracket * rate
                remaining -= bracket
            else:
                pit += remaining * rate
                remaining = Decimal("0.00")
            prev = limit
        pit = _quantize_2(pit)
    net = _quantize_2(gross - nsif_emp - pit)
    return {
        "gross": format(gross, ".2f"),
        "nsif_emp": format(nsif_emp, ".2f"),
        "nsif_co": format(nsif_co, ".2f"),
        "taxable": format(taxable, ".2f"),
        "pit": format(pit, ".2f"),
        "net": format(net, ".2f"),
        "status": "00",
        "engine": "python",
    }

def compute_esg(years: str, monthly: str) -> str:
    """ESG accrual — <3y 0.33*int(y), 3-5 0.5*y, 5-10 1*y, >10 1.5*y."""
    try:
        y = Decimal(str(years))
        m = Decimal(str(monthly))
    except InvalidOperation as e:
        logger.error("ESG invalid %s/%s: %s", years, monthly, e)
        return "0.00"
    if y < Decimal("3"):
        factor = Decimal("0.33")
        accrual = m * factor * Decimal(str(int(y)))  # COBOL INTEGER
    elif y < Decimal("5"):
        factor = Decimal("0.50")
        accrual = m * factor * y
    elif y < Decimal("10"):
        factor = Decimal("1.00")
        accrual = m * factor * y
    else:
        factor = Decimal("1.50")
        accrual = m * factor * y
    return format(_quantize_2(accrual), ".2f")
