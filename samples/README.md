# Samples — بيانات تجريبية موثوقة | Production-Ready Test Data

> **Synthetic only — مصنّعة بالكامل** — كل الأسماء والأرقام الوطنية والحسابات البنكية وهمية ومولّدة للاختبار فقط. لا يوجد شخص حقيقي.  
> **مصنّعة بالكامل — لا يوجد أشخاص حقيقيون** — جميع الأسماء والأرقام وهمية للاختبار فقط.

*Read in your language: [English](#english) | [العربية](#العربية)*

---

## English

### Trust & isolation

- **Demo tenant `DEMO`** is seeded (`tenants` `DEMO | Demo Trading`) — import samples there in production to keep `NA` (Nile Agro) clean. On this localhost demo, `owner@nileagro.sd` (NA) can import to NA directly — data is clearly marked `SD-00xx` / `SD-40xx` sample IDs, not live.
- **Money is exact** — all totals below are from `libpayroll.so` COMP-3, cross-checked vs Python `Decimal`. No float drift. Every string is `"0.00"` (2 decimals), FX `"0.0000"` (4 decimals).
- **Versioned & replayable** — `statutory_version v2026.09` and `FX 2026-09-25` (`USD 2610.5000`, `SAR 696.1000`, `AED 710.8500`), so `POST /api/runs` → `compute` is deterministic and auditable.

### What is inside

| File | What it tests | Key edges & expected totals |
|------|---------------|-----------------------------|
| `employees_sample.csv` (12 rows) | Import, NSIF 8/17, multi-currency, tax | `SD-0042` USD 1400+220 Y → `gross 4,229,010.00` `pit 740,637.84`; `SD-0044` SAR 5200+800 **N** contractor → `0.00 NSIF`; `SD-0050` 65k N below nisab; `SD-0051` `0.00` zero; `SD-0052` 5000 USD high; `SD-0053` 50k → `0.00` pit |
| `employees_42.csv` (42 rows) | Load & perf, 11ms/1k, 3 currencies, 15% N, hires 2014–2024 for ESG | 42 rows → `gross 186,090,341.70` `nsif_emp 12,367,681.67` `pit 33,260,581.90` `net 140,462,078.13` |
| `fx_rates.json` / `fx_rates.csv` | FX lock + history | 3 dates × 3 currencies, `source locked/CBOS` |
| `statutory_v2026.09.json` | Tax/NSIF without recompile | `tax_free 50000`, tiers `5%→100k, 10%→200k, 15%→400k, 20%→` |
| `payroll_run_2026-09_12.json` | Expected totals for 12-row run (assert) | `gross 43,011,522.50` `nsif_emp 3,101,593.80` `pit 7,623,035.74` `net 32,286,892.96` via `cobol` |
| `payroll_run_2026-09_42_expected.json` | Expected for 42 | `gross 186,090,341.70` `net 140,462,078.13` |
| `bank_file_sample.txt` | Bankak `H|D|T` fixed-width | `H|NA|202609|000012|43011522.50` + 12 `D` + `T|000012|32286892.96|COMP3-EXACT` |
| `payslip_sample_SD-0042.txt` | 7KB text payslip (WhatsApp) | 780 bytes, FX + statutory, `net 3,150,051.36` |
| `manifest.json` + `checksums.sha256` | Machine index + integrity | Row counts, totals, `sha256sum -c` |

### How to test every feature (5 min, localhost)

```bash
# 1. Login
curl -s -X POST http://localhost/api/auth/login -H "Content-Type: application/json" -d '{"email":"owner@nileagro.sd","password":"admin123"}' | jq
TOKEN=$(curl -s -X POST http://localhost/api/auth/login -H "Content-Type: application/json" -d '{"email":"owner@nileagro.sd","password":"admin123"}' | jq -r .access_token)

# 2. Import 12 sample
curl -s -H "Authorization: Bearer $TOKEN" -F file=@samples/employees_sample.csv http://localhost/api/employees/import | jq
# → {"imported":12,"warnings":0}

# 3. Lock FX (idempotent)
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"date":"2026-09-25","rates":{"USD":"2610.5000","SAR":"696.1000","AED":"710.8500"}}' http://localhost/api/fx/lock | jq

# 4. Run + assert vs sample
RID=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"period":"2026-09"}' http://localhost/api/runs | jq -r .run_id)
curl -s -X POST -H "Authorization: Bearer $TOKEN" http://localhost/api/runs/$RID/compute | jq .totals
# Compare: cat samples/payroll_run_2026-09_12.json | jq .totals

# 5. Reports
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost/api/reports/nsif?run_id=$RID" | jq .totals
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost/api/reports/pit?run_id=$RID" | jq
curl -s -H "Authorization: Bearer $TOKEN" http://localhost/api/reports/esg | jq '.esg[0]'

# 6. Bank
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost/api/bank/file?run_id=$RID" | head
diff <(curl -s -H "Authorization: Bearer $TOKEN" "http://localhost/api/bank/file?run_id=$RID") samples/bank_file_sample.txt && echo "bank OK"

# 7. Payslips
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost/api/payslips?run_id=$RID" | jq '.payslips|length'
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost/api/payslips/SD-0042?run_id=$RID" | head

# 8. Statutory (no recompile)
curl -s -H "Authorization: Bearer $TOKEN" http://localhost/api/statutory | jq

# 9. 42-row load (perf)
curl -s -H "Authorization: Bearer $TOKEN" -F file=@samples/employees_42.csv http://localhost/api/employees/import | jq
```

### Via dashboard (trustworthy UI)

1. Open `http://localhost/app/login.html` → `owner@nileagro.sd` / `admin123` → `http://localhost/app/samples.html`.
2. Top card shows **blue DEMO badge** + 4 bullet trust points (synthetic, exact, versioned, checksummed) + links to `/samples/` folder + `manifest.json`.
3. Click **“Load 12 sample”** or **“Load 42”** → `POST /api/employees/import` with `FormData`, shows `✓ 12 imported, 0 warnings` in green or `✕` in red (never silent).
4. Every import links to **Employees** and **Run payroll**; bank preview shows **“Verified vs sample”** when `COMP3-EXACT` and totals match.

### For a new VPS

`git clone` already includes `samples/` — no DB needed. To replay exactly: import `employees_sample.csv` + `POST /api/fx/lock` with `fx_rates.json` → `POST /api/runs` → `compute` → `diff` vs `payroll_run_2026-09_12.json`. `samples/` is served at `http://localhost/samples/` via Nginx `alias` (and `dashboard/samples/` for offline). All `UTF-8`, `text/csv` with header, `hire_date YYYY-MM-DD`, `currency SDG|USD|SAR|AED`, `nsif Y/N`.

### Checksums (CI)

```bash
# Exclude checksums.sha256 itself to avoid self-reference
sha256sum samples/bank_file_sample.txt samples/employees_42.csv samples/employees_sample.csv samples/fx_rates.csv samples/fx_rates.json samples/manifest.json samples/payroll_run_2026-09_12.json samples/payroll_run_2026-09_42_expected.json samples/payslip_sample_SD-0042.txt samples/README.md samples/statutory_v2026.09.json > samples/checksums.sha256
sha256sum -c samples/checksums.sha256 # must be all OK
```

---

## العربية

### الثقة والعزل

- **عميل تجريبي `DEMO`** مُحمّل مسبقاً (`DEMO | Demo Trading`) — استورد العينات هناك في الإنتاج لتحافظ على `NA` (النيل الزراعية) نظيفاً. في عرض `localhost` الحالي، يمكن لـ `owner@nileagro.sd` الاستيراد إلى `NA` مباشرة — البيانات موسومة بوضوح بمعرّفات `SD-00xx` / `SD-40xx` وليست بيانات حيّة.
- **المبالغ دقيقة** — كل الإجماليات من `libpayroll.so` بفاصلة ثابتة COMP-3 ومطابقة مع `Decimal` في بايثون. بلا انحراف. كل مبلغ نص `"0.00"` بمنزلتين، والصرف `"0.0000"` بأربع.
- **مُصدَرة ومُعاد تشغيلها حتمياً** — `statutory_version v2026.09` وسعر `25 سبتمبر 2026` (`دولار 2610.5000`، `ريال 696.1000`، `درهم 710.8500`)، لذا `POST /api/runs` ← `compute` حتمي وقابل للتدقيق.

### ماذا في الداخل

| الملف | ما يختبره | الحالات الحدّية والإجماليات المتوقعة |
|-------|-----------|----------------------------------------|
| `employees_sample.csv` (12) | الاستيراد، التأمينات 8/17، تعدد العملات، الضرائب | `SD-0042` دولار 1400+220 Y → `4,229,010.00` `740,637.84`؛ `SD-0044` ريال 5200+800 **N** متعاقد → `0.00` تأمينات؛ `SD-0050` 65k N تحت النصاب؛ `SD-0051` `0.00` صفر؛ `SD-0052` 5000 دولار مرتفع؛ `SD-0053` 50k → `0.00` ضريبة |
| `employees_42.csv` (42) | الحمولة 11مللي/1000، 3 عملات، 15% متعاقدون، 2014–2024 للمكافأة | 42 → `186,090,341.70` `12,367,681.67` `33,260,581.90` `140,462,078.13` |
| `fx_rates.json` / `fx_rates.csv` | تثبيت الصرف والتاريخ | 3 تواريخ × 3 عملات، `locked/CBOS` |
| `statutory_v2026.09.json` | الضرائب بلا تجميع | `إعفاء 50000`، شرائح `5%→100k، 10%→200k، 15%→400k، 20%→` |
| `payroll_run_2026-09_12.json` | الإجماليات المتوقعة لـ 12 | `43,011,522.50` `3,101,593.80` `7,623,035.74` `32,286,892.96` عبر `cobol` |
| `bank_file_sample.txt` | ملف بنكك `H|D|T` | `H|NA|202609|000012|43011522.50` + 12 `D` + `T|...|COMP3-EXACT` |
| `payslip_sample_SD-0042.txt` | قسيمة 7 ك.ب | 780 بايت، الصرف والقانون |
| `manifest.json` + `checksums.sha256` | فهرس آلي | أعداد الصفوف والإجماليات والبصمات |

### كيف تختبر كل شيء (5 دقائق، localhost)

```bash
# 1. تسجيل دخول
TOKEN=$(curl -s -X POST http://localhost/api/auth/login -H "Content-Type: application/json" -d '{"email":"owner@nileagro.sd","password":"admin123"}' | jq -r .access_token)

# 2. استيراد 12
curl -s -H "Authorization: Bearer $TOKEN" -F file=@samples/employees_sample.csv http://localhost/api/employees/import | jq
# 3. تثبيت الصرف
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"date":"2026-09-25","rates":{"USD":"2610.5000","SAR":"696.1000","AED":"710.8500"}}' http://localhost/api/fx/lock | jq
# 4. مسير ومقارنة
RID=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"period":"2026-09"}' http://localhost/api/runs | jq -r .run_id)
curl -s -X POST -H "Authorization: Bearer $TOKEN" http://localhost/api/runs/$RID/compute | jq .totals
# قارن: cat samples/payroll_run_2026-09_12.json | jq .totals
# 5-9 نفس الإنجليزية أعلاه مع http://localhost
```

### عبر اللوحة (واجهة موثوقة)

1. افتح `http://localhost/app/login.html` ← `owner@nileagro.sd` / `admin123` ← `http://localhost/app/samples.html`.
2. البطاقة العلوية زرقاء بشارة **تجريبي** + 4 نقاط ثقة + روابط `/samples/` و `manifest.json`.
3. اضغط **“حمّل عينة 12”** أو **“حمّل عينة 42”** ← `POST /api/employees/import` مع تأكيد، تظهر `✓ 12 استيراد` بالأخضر أو `✕` بالأحمر (لا صمت).
4. كل استيراد يربط **الموظفون** و **مسير الرواتب**؛ معاينة البنك تظهر شارة **“مطابق للعينة”** عند `COMP3-EXACT`.

### لخادم جديد

`git clone` يتضمن `samples/` — لا تحتاج قاعدة. لإعادة الحالة حرفياً: استورد `employees_sample.csv` + `POST /api/fx/lock` بـ `fx_rates.json` ← `POST /api/runs` ← `compute` ← `diff` مع `payroll_run_2026-09_12.json`. `samples/` متاح على `http://localhost/samples/` عبر Nginx.

### البصمات

```bash
# استبعد checksums.sha256 نفسه لتفادي المرجع الذاتي
sha256sum samples/bank_file_sample.txt samples/employees_42.csv samples/employees_sample.csv samples/fx_rates.csv samples/fx_rates.json samples/manifest.json samples/payroll_run_2026-09_12.json samples/payroll_run_2026-09_42_expected.json samples/payslip_sample_SD-0042.txt samples/README.md samples/statutory_v2026.09.json > samples/checksums.sha256
sha256sum -c samples/checksums.sha256
```
