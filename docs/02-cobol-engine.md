# 02 — COBOL Engine (COMP-3 exact)

> All money in `COMP-3` packed decimal, ROUNDED only at statutory points. JSON/API never sees float.

## Copybooks

- `EMPFILE.cpy` — `EMP-ID X(10)`, `EMP-NAME X(40)`, `EMP-NATIONAL-ID X(15)`, `EMP-HIRE-DATE (YYYYMMDD)`, `EMP-BASE-CURRENCY X(03)`, `EMP-BASE-SALARY S9(9)V99 COMP-3`, `EMP-ALLOWANCES-SDG/FX S9(9)V99 COMP-3`, `EMP-NSIF-ELIGIBLE X(01) Y/N`, `EMP-BANK-ACCOUNT X(24)`, `EMP-BANK-CODE X(08)`
- `PRLREC.cpy` — `PRL-EMP-ID X(10)`, `PRL-PERIOD-DATE X(06) YYYYMM`, `PRL-EXCHANGE-RATE S9(5)V9(4) COMP-3`, `PRL-GROSS-SDG S9(11)V99`, `PRL-NSIF-EMP/CO S9(9)V99`, `PRL-TAXABLE S9(11)V99`, `PRL-PIT S9(9)V99`, `PRL-ZAKAT S9(9)V99`, `PRL-NET-PAY-SDG S9(11)V99`
- `STATUTORY.cpy` — versioned `ST-VERSION X(08)`, `ST-NSIF-EMP 0.08`, `ST-NSIF-CO 0.17`, `ST-TAX-FREE 50000.00`, 4 tiers (`100k 5%`, `200k 10%`, `400k 15%`, `999M 20%`)

## Modules

| Module | File | Input | Output | Logic |
|--------|------|-------|--------|-------|
| PRL-CALC | `payroll_calc.cob` | currency, base, allow, fx, nsifFlag, version | gross, nsifEmp/Co, taxable, pit, net | `gross=(base+allow)*fx` if FX else `+`; NSIF 8/17 only if `Y`; `taxable=gross-nsifEmp`; PIT progressive via tier loop; `net=gross-nsif-pit` |
| FX-NORM | `fx_norm.cob` | fxStr | outRate, status | validate `0 < rate <= 99999.9999`, else `01` |
| NSIF-ENG | `nsif_eng.cob` | grossStr, flag | empStr, coStr | contractor `N`→0 |
| TAX-SUD | `tax_sud.cob` | taxableStr | pitStr | same tier loop as PRL-CALC |
| ESG-VAL | `esg_val.cob` | yearsStr, monthlyStr | accrualStr | `<3yr 0.33*int(years)`, `3-5 0.5*y`, `5-10 1.0*y`, `>10 1.5*y` × monthly |

All use `FUNCTION NUMVAL` in, `PIC Z...9.99` + `FUNCTION TRIM` out → `X(15)` strings `"4229010.00"` for ctypes (`char[15]`).

## Build

```
make -C backend/cobol
# cobc -free -b -O2 -Wall -I copybooks payroll_calc.cob fx_norm.cob nsif_eng.cob tax_sud.cob esg_val.cob
# mv payroll_calc.so libpayroll.so  (28-29KB, <15MB RSS)
nm -D backend/cobol/libpayroll.so | grep -E "PAYROLL|FX|NSIF|TAX|ESG"
# PAYROLL__CALC, FX__NORM, NSIF__ENG, TAX__SUD, ESG__VAL
```

Verify: `make -C backend/cobol && ls -lh backend/cobol/libpayroll.so` → `28704 bytes` (2026-09-14)

## Tests (COMP-3 exactness)

`backend/tests/test_cobol_roundtrip.py` — loads `libcob.so.5` + `cob_init(0,None)` then `PAYROLL__CALC` via ctypes (two `char*` buffers: input 57B, output 92B). Compares vs Python `Decimal` mirror (same tiers, `ROUND_HALF_UP`).

Vectors (`dashboard/js/data.js` + `payroll.js`):

- USD 1400+220×2610.50 Y → gross `4229010.00` nsif `338320.80` taxable `3890689.20` pit `740637.84` net `3150051.36`
- SDG 850k+120k×1 Y → `970000.00` / `77600.00` / `892400.00` / `140980.00` / `751420.00`
- SAR 5200+800×696.10 N (contractor) → `4176600.00` / `0.00` / `797820.00` / `3378780.00`
- AED 4800+650×710.85 Y → `3874132.50` etc — all ✅ `COMP-3 roundtrip OK`

Edge: `0.00`, `0.01 USD`, `50000` — all zero or minimal pit, status `00`.

Run: `python3 backend/tests/test_cobol_roundtrip.py && pytest backend/tests -v`

## Money rules enforced

- `COMP-3` throughout, `ROUNDED` only at NSIF (`gross*0.08`) and final PIT
- Python `Decimal(...).quantize(Decimal("0.00"), ROUND_HALF_UP)`
- JSON `str` `"3150051.36"` never `number`
- Every run stores `fx_rate` (`S9(5)V9(4)`) + `statutory_version` (`v2026.09`) for replay
