# Part 1 — Payments & Fraud Analytics

Synthetic Paytm UPI/wallet/QR merchant-payments dataset, analyzed across four
layers: an Excel merchant workbook, a SQL fraud-detection database, a Python
reconciliation engine, and a four-layer analytics dashboard. The figures below come from the generated data and the model runs.

## Objective

Paytm's payments operations team needs three things every fraud/ops analyst
has to be able to do: cross-reference merchant data in a spreadsheet the way
regional-ops teams actually work, query a relational schema in SQL to catch
fraud patterns, and turn cleaned data into an executive-ready dashboard. This
part builds all three, plus a ledger-vs-gateway payment-reconciliation
engine, against one synthetic 547-row transaction ledger.

## Setup

```bash
pip install pandas numpy matplotlib openpyxl
```

`sqlite3` is part of the Python standard library — no extra install needed.

## Data generation

The generator uses a fixed random seed (42) so the dataset — and every
downstream count in this README — is reproducible. **Run it from inside this
folder**, since it writes CSVs via relative paths:

```bash
cd payments_fraud_analytics
python generate_data.py
```

Output (all committed to this folder): `merchants.csv` (40 rows),
`users.csv` (365 rows — 350 original + 15 burner accounts injected later),
`ledger.csv` (547 rows: 500 baseline + 15 burner-account chargebacks + 32
velocity-attack rows across 8 clusters of 4), `gateway_export.csv` (530
rows, built from the ledger with injected discrepancies).

## Database setup

```bash
python database_setup.py
```

Rebuilds `paytm_payments.db` from the three CSVs with `merchants`, `users`,
and `transactions` tables (declared primary keys, foreign keys from
`transactions` to both `users` and `merchants`).

## SQL execution

```bash
python run_sql_queries.py
```

Runs all 9 statements in `fraud_queries.sql` (8 labeled queries, one split
into a distinct-values query and a top-N query) and writes their live output
to `sql_outputs.txt`, along with a short check for the two seeded fraud patterns.

**Measured results:**
- **Chargeback impact:** 28 chargeback transactions, 27 unique users
  affected, INR 54,472 total chargeback amount.
- **Burner accounts:** the query surfaces **all 15** seeded burner-account
  rows (`transaction_id LIKE 'TXN2%'`), using the strict
  `0 <= account_age_days < 30` boundary.
- **Velocity attacks:** grouping by `user_id` and a floored 10-minute time
  bucket surfaces **all 8** seeded clusters as distinct qualifying groups.

## Reconciliation

```bash
python reconcile.py
```

`reconcile_payments(ledger_df, gateway_df)` returns four DataFrames using
set operations on `transaction_id` and `pd.merge` for the pairwise
comparisons. Results are written to `reconciliation_results.txt`.

**Measured discrepancy counts** (547-row ledger; injected rates in
parentheses): missing in gateway — 27 rows, 4.9% (~5% target); extra in
gateway — 10 rows, 1.8% (~2% target); amount mismatches — 16 rows, 2.9%
(~3% target); status mismatches — 9 rows, 1.6% (~2% target). All four land
close to the injection rates in `generate_data.py`.

## Dashboard

```bash
python dashboard.py
```

Saves five chart images to `charts/`. Metric definitions used here are: `match_rate` requires identical `amount_inr` **and**
identical `status` for a transaction present in both files (a stricter,
separate number from the four reconciliation categories above); both
`chargeback_ratio` figures are count-based, never amount-based.

### Headline layer (`charts/headline.png`)

**Total GMV: INR 382,603. Success rate: 85.6%. Reconciliation match rate:
90.5%. Chargeback ratio: 5.12%.** The match rate (90.5%) is noticeably lower
than "1 minus the missing-transaction rate" (95.1%) would suggest, because
it also penalizes the amount and status mismatches that reconciliation
catches separately — this is the intended effect of requiring both fields
to match exactly. The chargeback ratio is inflated relative to a typical
production book because the dataset deliberately injects 15 burner-account
chargebacks on top of the organic ~2% baseline chargeback rate.

### Trends layer (`charts/trends.png`)

Daily GMV fluctuates in the ~INR 4,000–28,000 range with no strong weekly
pattern, which is expected from independently randomized baseline
transactions rather than real seasonal demand. Daily chargeback count
spikes on 2026-01-23 (4 chargebacks) and 2026-01-29 (3 chargebacks) —
both dates fall inside the day-10-to-29 window used to inject the 15
burner-account frauds, so these spikes are a direct artifact of that
injection rather than an organic fraud trend.

### Breakdown layer

**By payment method** (`charts/breakdown_payment_method.png`): UPI leads
GMV at INR 172,274, consistent with its 55% weighting in the generator and
its dominance in real Indian retail payments; Card (INR 102,429), Wallet
(INR 71,304), and Netbanking (INR 36,596) follow the same order as their
underlying sampling weights.

**By merchant category** (`charts/breakdown_category.png`): ecommerce (INR
79,896), travel (INR 75,250), and grocery (INR 71,936) are the top three
categories by GMV. Because category is assigned to merchants uniformly at
random rather than weighted by realistic transaction frequency, the spread
across the seven categories is fairly even — recharge is the clear outlier
at only INR 15,125, reflecting fewer merchants landing in that category by
chance rather than any genuine demand signal.

### Details layer (`charts/merchant_details.png`)

Of the top 10 merchants by transaction count, 6 are flagged **HIGH RISK**
(per-merchant chargeback ratio > 1%) — notably Merchant_027 and
Merchant_029, both above 15%. This is a substantially higher flag rate than
a real merchant book would show; it reflects the small sample size (a
merchant with just 16–20 transactions only needs 1–2 chargebacks to cross
the 1% threshold) rather than a genuine merchant-quality problem, and is
worth noting as a limitation of applying this rule to a 30-day synthetic
sample.

## 8. Excel workbook

`merchant_workbook.xlsx` (built by `build_workbook.py`, then recalculated
with LibreOffice via the xlsx skill's `recalc.py` — 5,235 formulas, 0
errors) has six sheets: `README`, `Merchants`, `Fee_Tiers`,
`Daily_Merchant`, `Transactions_View`, `Pivot_Summary`.

- **VLOOKUP** (`Transactions_View` columns I–K): merchant_name, category,
  and region pulled from `Merchants!$A$2:$D$41` (fixed absolute range),
  each wrapped in `IFERROR(...,"Merchant not found")`.
- **HLOOKUP** (`Transactions_View` column M): payment-method fee tier
  pulled from a horizontal reference table on `Fee_Tiers!$B$1:$E$2` — UPI
  0.30%, Wallet 0.60%, Card 1.80%, Netbanking 0.90%. These are illustrative
  assumptions for this assignment, documented on the `Fee_Tiers` sheet and
  the `README` sheet — not real Paytm MDR rates.
- **Nested IF/AND classification** (`Transactions_View` column O): a
  transaction is labeled "High-Value Merchant Day" when its merchant's
  total transaction amount on that calendar day (pulled from the
  `Daily_Merchant` table, column N) exceeds INR 5,000 **and** the
  merchant's region is not "East". 10 of the 547 rows are classified this
  way — independently verified against a pandas recomputation.
- **Pivot tables**: `openpyxl` cannot reliably write a native Excel
  PivotTable object from scratch (this is a documented library limitation,
  not a shortcut — see the `README` sheet inside the workbook for the full
  explanation). As the closest valid substitute, `Daily_Merchant` and
  `Pivot_Summary` are built as **live SUMIFS/COUNTIFS cross-tabs** that
  recalculate automatically if the underlying transaction data changes,
  the same way a refreshed pivot table would — nothing is hardcoded.
  `Pivot_Summary` Section 1 gives total `amount_inr` and transaction count
  by `merchant_id` and `status`; Section 2 gives a transaction-count-vs-
  unique-days comparison for all 40 merchants (well beyond the minimum of
  5 required).

## Design decisions

- **Fee-tier assumptions:** stated above and inside `Fee_Tiers`/`README`
  sheets — illustrative only.
- **High-Value Merchant Day rule:** stated above — daily total (via the
  Daily_Merchant summary) > INR 5,000 and region ≠ East.
- **Pivot design:** SUMIFS/COUNTIFS live cross-tabs in place of a native
  Excel PivotTable object, for the reason documented in Section 8 above and
  inside the workbook's `README` sheet.
- **Dashboard metric definitions:** `match_rate` requires identical
  `amount_inr` *and* identical `status`, kept fully separate from the four
  `reconcile_payments()` discrepancy categories; both `chargeback_ratio`
  figures (platform-wide and per-merchant) are count-based.
- **Chart choices:** bar+line combo chart for the trends layer (GMV as
  bars, chargeback count as an overlaid line, since the two series have
  very different scales); grouped bar charts for the two breakdown views;
  a rendered table image (not a live DataFrame) with conditional
  highlighting for the details layer, per the assignment's explicit
  requirement.
- **Reconciliation approach:** set operations on `transaction_id` for the
  missing/extra categories, `pd.merge` (inner join) for the pairwise
  amount/status comparisons, with the amount difference computed as
  `gateway - ledger`.

## Final folder structure

```
payments_fraud_analytics/
├── generate_data.py
├── merchants.csv
├── users.csv
├── ledger.csv
├── gateway_export.csv
├── merchant_workbook.xlsx
├── build_workbook.py
├── database_setup.py
├── paytm_payments.db
├── fraud_queries.sql
├── run_sql_queries.py
├── sql_outputs.txt
├── reconcile.py
├── reconciliation_results.txt
├── dashboard.py
├── charts/
│   ├── headline.png
│   ├── trends.png
│   ├── breakdown_payment_method.png
│   ├── breakdown_category.png
│   └── merchant_details.png
└── README.md
```

## Final checks

- `generate_data.py` reproduces the exact 547-row ledger (500 + 15 + 32), 40 merchants, 365 users, 530-row gateway export — seed 42
- `merchant_workbook.xlsx`: VLOOKUP with `$` absolute range + IFERROR; HLOOKUP; nested IF/AND rule (10/547 rows classified, verified against pandas); pivot-equivalent summaries with count-vs-unique-days for all 40 merchants
- SQLite schema with PK/FK; 9 executed queries covering SELECT/WHERE/ORDER BY/LIMIT/DISTINCT/GROUP BY/HAVING/INNER JOIN/LEFT JOIN; burner query surfaces all 15 seeded rows; velocity query surfaces all 8 seeded clusters
- `reconcile_payments()` returns all four discrepancy DataFrames with counts matching the ~5%/~3%/~2%/~2% injection rates
- All four dashboard layers saved as images with 2–4 sentence interpretations; details layer is an image, not a printed DataFrame; match_rate and chargeback_ratio use the exact stated definitions
- README documents install/run steps and every design decision
- All monetary values in INR — no `$`/USD anywhere
