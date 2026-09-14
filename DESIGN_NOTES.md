# DESIGN_NOTES.md — SMCPE

## Direction tried
- Mode: Corporate/Enterprise (primary) + Convention-Plus (dashboard patterns). No expressive marketing hero — trust beats spectacle for payroll.
- Research-backed: Fintech Trust blue-green (uicolors), Stripe #533AFD system tokens, Coinbase semantic tokens, Wise light/dark dashboard.
- Theme: custom "Trust Navy + Emerald Ledger" — navy sidebar #0B1B30, paper bg #F4F6F9, primary #1D4ED8, success #047857. Strict semantic: green=positive/posted, red=deduction/negative always with − sign + label, never decorative.
- Type: Swiss Classic — Inter Tight display + Inter body + JetBrains Mono tabular figures. 2 families + mono for money only.
- Layout: Symmetric Balance + Bento KPIs + Stacked compliance blocks.

## Signature element
- Net-Pay Waterfall Ledger: Gross → NSIF 8% → Taxable → PIT → Net, recomputed live per currency (SDG/USD/SAR) mirroring payroll_calc.cob COMP-3 math. Why: proves exactness, domain-specific, memorable without gimmicks.

## What user reacted to (to track)
- TBD: light vs dark table preference, WhatsApp approval prominence, Bankak file format details.

## Avoid repeating
- No purple-blue gradient hero, no uniform rounded-16 cards, no emoji icons (inline SVG only), no lorem, no auto-animation, no pure #fff on #000.
- Keep pages <50KB spirit: vanilla CSS, no Tailwind CDN, no chart lib (CSS bars), text payslip 7KB fallback.

## Surfaces covered in index.html
Dashboard, Employees, Payroll Run wizard, Payslips + delivery log, FX Rates, Reports (NSIF/PIT/ESG/Zakat), Bank Export (Bankak fixed-width), Tenants & Users, Audit Log, Statutory Tables settings. Missing (next): public landing, login, mobile USSD fallback.
