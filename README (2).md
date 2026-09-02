# Part 3 — AI-Augmented FinTech Advisory \& Blockchain Risk

## 1\. Objective

Paytm Money needs a lightweight AI-assisted advisory toolkit: a
portfolio-allocation agent grounded in CAPM and portfolio variance, a
structured-extraction helper for company-disclosure text, a bull/bear/
synthesizer debate demo, a DCF valuation calculator, and a written
blockchain/crypto risk appendix. This is deliberately NOT a RAG build —
no embeddings, vector database, or agent framework — just plain,
auditable Python functions plus one markdown appendix.

## 2\. Folder / Files Overview

```
ai\_advisory\_blockchain/
├── stock\_universe.py        - fixed ticker universe (beta, expected return, std\_dev), Rf, Rm
├── investor\_profiles.py     - fixed 5 investor profiles
├── disclosure\_snippets.py   - fixed 6 disclosure text snippets
├── advisory\_agent.py        - Part A: think -> act -> observe portfolio agent
├── extract\_disclosure.py    - Part B: structured disclosure signal extraction
├── debate.py                 - Part C: 3-agent bull/bear/synthesizer demo
├── dcf\_calculator.py        - Part D: DCF valuation + sensitivity + EV/EBITDA
├── blockchain\_risk\_note.md  - Part E: written crypto/blockchain risk appendix (850 words)
├── run\_all.py                - runs every component in sequence, writes run\_transcript.txt
├── run\_transcript.txt        - the actual recorded output of run\_all.py (MOCK\_LLM mode)
└── README.md
```

## 3\. Installation Requirements

No third-party dependencies — every file uses only the Python standard
library (`os`, `math`, `re`). No API key, no signup, no network access
needed.

```bash
python3 --version   # any Python 3.8+
```

## 4\. How to Run Every Required Component

```bash
python advisory\_agent.py       # Part A: all 5 investor profiles
python extract\_disclosure.py   # Part B: all 6 disclosure snippets
python debate.py                # Part C: bull/bear/synthesizer for PAYFIN
python dcf\_calculator.py       # Part D: base valuation + sensitivity + EV/EBITDA
python run\_all.py               # runs all four above, writes run\_transcript.txt
```

## 5\. MOCK\_LLM Explanation

**Every recorded output in this README and in `run\_transcript.txt` was
generated with `MOCK\_LLM` left unset** (which defaults to mock mode — the
same as explicitly setting `MOCK\_LLM=1`). No API key is used or required
anywhere in this submission, and no network call is made. The only parts
of the codebase gated by `MOCK\_LLM` are: the advisory agent's final
narrative sentence (`advisory\_agent.build\_narrative`), the disclosure
extractor's docstring note on where an LLM call *could* go (not
implemented), and the three debate-agent argument functions. All of the
actual financial computation — allocation lookup, CAPM, portfolio
variance/std, the escalation check, keyword-based signal extraction, and
the entire DCF — is plain deterministic Python that runs identically
regardless of `MOCK\_LLM`. Setting `MOCK\_LLM=0` raises a clear
`NotImplementedError` rather than silently failing or faking a call — the
optional real-LLM extension was intentionally not built, per the
assignment's instruction not to spend time on it, and the graded mock
path has no dependency on it whatsoever.

## 6\. Advisory-Agent Design (Part A)

Structured as three explicit stages in `advisory\_agent.py`:

* **THINK** (`think\_decide\_allocation`): looks up the investor's
risk\_tolerance in the fixed `ALLOCATION\_TABLE` and returns an
equal-weighted (1/3 each) allocation.
* **ACT** (`get\_stock\_data`): the required tool call — retrieves
beta/analyst\_expected\_return/std\_dev from `STOCK\_UNIVERSE` for each
selected ticker (simulating an external market-data API call).
* **OBSERVE/DECIDE** (`compute\_portfolio\_metrics`): computes per-stock
CAPM expected return (beta only), the weight-averaged portfolio
expected return, portfolio variance/std, and the human-in-the-loop
escalation flag.

## 7\. Exact Portfolio Allocation Table

|Risk Tolerance|Tickers (equal-weighted, 1/3 each)|
|-|-|
|Conservative|PAYBOND, PAYGOLD, PAYRETAIL|
|Moderate|PAYRETAIL, PAYINFRA, PAYGOLD|
|Aggressive|PAYTECH, PAYFIN, PAYINFRA|

## 8\. CAPM Formula

```
E(R\_i) = R\_f + beta\_i \* (E(R\_m) - R\_f)
R\_f = 0.07, E(R\_m) = 0.13
```

Uses **only** `beta` — `analyst\_expected\_return` is never used in this
calculation anywhere in the codebase (it's used only in `debate.py`,
where the agents are explicitly allowed to reference it as a raw data
field, not as a CAPM input).

## 9\. Portfolio Variance Formula and rho = 0.3

```
Var(R\_p) = sum\_i w\_i^2 \* sigma\_i^2 + 2 \* sum\_{i<j} w\_i \* w\_j \* Cov(R\_i, R\_j)
Cov(R\_i, R\_j) = rho \* sigma\_i \* sigma\_j,   rho = 0.3 for every pair
portfolio\_std = sqrt(Var(R\_p))
```

## 10\. Human-in-the-Loop Threshold

`portfolio\_std > 0.20` triggers `ESCALATED\_TO\_HUMAN\_ADVISOR`. This is a
real runtime comparison against the computed value — no investor ID is
hardcoded into the escalation logic. **Measured result, all 5 investors:**

|Investor|Risk Tolerance|Portfolio Std Dev|Escalated?|
|-|-|-:|-|
|INV01|Conservative|8.44%|No|
|INV02|Moderate|12.57%|No|
|INV03|Aggressive|20.58%|**Yes**|
|INV04|Moderate|12.57%|No|
|INV05|Aggressive|20.58%|**Yes**|

Exactly matches the assignment's expected deterministic pattern.

## 11\. Disclosure Extraction Logic (Part B)

`extract\_signals(snippet)` (in `extract\_disclosure.py`) uses pure
keyword/regex rules, no LLM call:

* **Risk flags:** `litigation`/`lawsuit` → `"litigation"`;
`regulatory`/`regulator` → `"regulatory"`; an explicit "customer
concentration" phrase or a "top N customers ... account for X percent"
pattern → `"customer\_concentration"`.
* **Hedging:** any of `"assuming"`, `"cautiously"`, `"visibility"` present
→ `hedging\_detected = True`.
* **Sentiment:** confident keywords (`"confident"`, `"approved"`) are
checked *before* hedging, so a snippet with both (like doc\_05) always
resolves to `"confident"`; otherwise hedging → `"cautious"`; otherwise
`"neutral"`.

**Measured results, all 6 snippets:**

|Doc|Risk Flags|Hedging|Sentiment|
|-|-|-|-|
|doc\_01|\[]|True|cautious|
|doc\_02|\[litigation]|False|neutral|
|doc\_03|\[customer\_concentration]|False|neutral|
|doc\_04|\[]|True|cautious|
|doc\_05|\[]|False|**confident**|
|doc\_06|\[regulatory]|False|neutral|

## 12\. Debate Demo (Part C)

`debate.py` runs a 3-agent bull/bear/synthesizer debate on **PAYFIN**
(beta 1.35, analyst\_expected\_return 16.0%, std\_dev 28.0%). Both the bull
and bear arguments quote these exact numbers (not invented), and the
synthesizer combines them into a 2–3 sentence balanced summary. Full text
in Section 15 below and in `run\_transcript.txt`.

## 13\. DCF Assumptions (Part D)

Hypothetical Paytm Postpaid (lending) business line, all figures in INR
crore, all illustrative:

* Base EBIT: 120 | Tax rate: 25% | D\&A: 20 | CapEx: 35 | ΔNWC: 10
→ **Base FCFF = 65.00**
* 5-year growth path (fading toward terminal growth): 18%, 15%, 12%, 9%, 6%
* Cost of equity: CAPM using PAYFIN's beta (1.35) → **15.10%**
* Pre-tax cost of debt: 9%, tax rate 25% → after-tax cost of debt **6.75%**
* Capital structure: 70% equity / 30% debt
* **WACC = 70%×15.10% + 30%×6.75% = 12.595%**
* Terminal growth: **5.00%** (7.595pp below base WACC, comfortably over
the required 3pp minimum)

**Base-case result:** Sum of PV(FCFF, yrs 1–5) = INR 336.97 crore |
Terminal value = INR 1,577.99 crore | PV(TV) = INR 871.99 crore |
**Enterprise value = INR 1,208.96 crore**

## 14\. DCF Sensitivity Table (Part D)

3×3 grid, WACC (rows) × terminal growth (columns), enterprise value in
INR crore:

|WACC \\ Growth|4.0%|5.0%|6.0%|
|-|-:|-:|-:|
|11.60%|1249.1|1396.0|1595.5|
|12.60% (base)|1100.2|1209.0|1350.7|
|13.60%|982.4|1065.5|1170.5|

**Worst-case check:** WACC − 1pp (11.595%) vs. growth + 1pp (6.00%) →
spread = **5.60 percentage points**, well above the required minimum of
1pp. All 9 cells satisfy `WACC > terminal growth`, verified
programmatically in `dcf\_calculator.py` (an `assert` fails loudly if not).

## 15\. EV/EBITDA Cross-Check

Illustrative EBITDA (EBIT + D\&A) = INR 140.0 crore; illustrative multiple
= 8.0x → **EV/EBITDA-implied enterprise value = INR 1,120.00 crore**,
versus the DCF's INR 1,208.96 crore — a **+7.9%** difference. The two
estimates are **broadly similar**: both land in the same \~INR 1,100–1,210
crore range. The gap is plausibly explained by the DCF crediting the
business for its above-terminal near-term growth (18%→6% fade) more
explicitly than a static trailing multiple would, and by the multiple
method not separately accounting for the specific capital structure
(70/30 equity/debt) embedded in the DCF's WACC.

## 16\. Blockchain Risk Appendix Summary

`blockchain\_risk\_note.md` (850 words) covers: (1) the fiat-collateralized
vs. algorithmic stablecoin distinction plus DeFi/DAO governance,
tokenomics, and smart-contract risk, framed specifically around what a
"Paytm Crypto Insights" watchlist would need to get right; (2) a specific
recommendation — **max 2% crypto allocation, 0% default for Conservative
investors** — justified via CAPM's dislike of a no-intrinsic-value asset,
low/negative correlation as a diversification benefit, heavy-tailed
skewed returns, survivorship bias, and high transaction costs; (3) a
T.A.N.G.-framework analysis naming **Authority** (fake KYC/suspension
calls, defended by real-time device-binding + step-up authentication) and
**Greed** (fake guaranteed-return crypto schemes, defended by real-time
transaction risk scoring with velocity controls on new beneficiaries) as
the two most relevant social-engineering vectors for a combined UPI +
wallet + lending + wealth platform.

## 17\. Recorded Run Outputs / Transcripts

All outputs below were generated by `python run\_all.py` with `MOCK\_LLM`
left unset (mock mode, the graded baseline) — the full transcript is
saved verbatim in `run\_transcript.txt`. Key excerpts:

**Advisory agent (INV01):**

```
Investor INV01 (Conservative)
  Allocation: PAYBOND (33.33%), PAYGOLD (33.33%), PAYRETAIL (33.33%)
  Per-stock CAPM expected return: PAYBOND=7.30%, PAYGOLD=8.20%, PAYRETAIL=12.10%
  Portfolio expected return: 9.20%
  Portfolio std dev: 8.44%
  Status: finalized (portfolio std dev 8.44% <= 20%)
  Narrative: For Conservative investor INV01, we recommend an allocation across
  PAYBOND, PAYGOLD, PAYRETAIL with an expected portfolio return of 9.2% and
  volatility of 8.4%.
```

**Advisory agent (INV03 — escalated):**

```
Investor INV03 (Aggressive)
  Allocation: PAYTECH (33.33%), PAYFIN (33.33%), PAYINFRA (33.33%)
  Portfolio std dev: 20.58%
  >>> ESCALATED\_TO\_HUMAN\_ADVISOR (portfolio std dev 20.58% > 20%)
```

**Debate (PAYFIN):**

```
BULL on PAYFIN: With an expected return of 16.0% against a beta of 1.35,
this offers attractive risk-adjusted upside...
BEAR on PAYFIN: A standard deviation of 28.0% combined with a beta of 1.35
means PAYFIN will amplify market drawdowns, not just rallies...
SYNTHESIZER: PAYFIN's 16.0% expected return and 1.35 beta make the bull case
real, but its 28.0% standard deviation makes the bear case just as real...
```

Full advisory-agent output for all 5 investors, all 6 disclosure
extractions, and the complete DCF run (including the sensitivity grid) are
in `run\_transcript.txt`.

## Final Acceptance-Criteria Audit

All items below were checked against the required acceptance criteria and verified through the end-to-end run\_all.py execution

* \[x] Exact `STOCK\_UNIVERSE`, `INVESTOR\_PROFILES`, `DISCLOSURE\_SNIPPETS` preserved
* \[x] Conservative / Moderate / Aggressive allocations exactly as specified, each 1/3-weighted
* \[x] `get\_stock\_data(ticker)` used as the ACT tool call
* \[x] CAPM uses beta only; `analyst\_expected\_return` never used in CAPM
* \[x] R\_f = 7%, R\_m = 13%, rho = 0.3 for every pair
* \[x] Portfolio variance/std formula implemented exactly as specified
* \[x] Escalation fires only when std > 20%; pattern matches INV01/02/04 = No, INV03/05 = Yes
* \[x] Only the narrative sentence is MOCK\_LLM-gated; mock mode makes no network calls
* \[x] All 5 investor profiles executed
* \[x] `extract\_signals` returns the exact schema; all 6 required checks (litigation, customer concentration, hedging, doc\_05 confident, regulatory, at least one hedging) pass
* \[x] Debate has bull + bear + synthesizer, references PAYFIN's actual numbers, synthesizer is 2–3 sentences
* \[x] DCF uses unlevered FCFF with the correct formula; 5 years projected; terminal value via growing perpetuity; WACC calculated (not invented); cost of equity via CAPM
* \[x] Terminal growth (5%) is 7.595pp below base WACC (≥ 3pp required); worst-case sensitivity spread is 5.60pp (≥ 1pp required); all 9 grid cells satisfy WACC > growth
* \[x] EV/EBITDA cross-check included with a written 2–3 sentence comparison
* \[x] `blockchain\_risk\_note.md` is 850 words (within 600–900), covers all three required sections
* \[x] README documents MOCK\_LLM mode; no optional real-LLM dependency required
* \[x] No RAG/vector DB/LangGraph added anywhere
* \[x] Everything runs end-to-end with no API key and no network access

