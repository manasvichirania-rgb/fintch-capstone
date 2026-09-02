# FinTech Capstone Project

This repository contains the three parts of the FinTech Capstone project covering payments and fraud analytics, credit risk and lending, and AI-augmented investment advisory with blockchain risk analysis.

## Repository Structure

```text
paytm-fintech-capstone/
├── README.md
├── payments_fraud_analytics/
├── credit_risk_lending_ml/
└── ai_advisory_blockchain/
```

Each folder contains the files and outputs for its respective part.

---

# Part 1 — Payments & Fraud Analytics

**Folder:** `payments_fraud_analytics`

This part analyses a synthetic Paytm-style payment dataset using spreadsheet analysis, SQL, reconciliation and dashboarding.

It includes:

- Synthetic payment, merchant and user data
- Excel analysis using VLOOKUP, HLOOKUP and conditional formulas
- High-value merchant day analysis
- Merchant and payment-status summaries
- SQLite database and SQL fraud analysis
- Payment gateway reconciliation
- Chargeback, burner-account and transaction-velocity analysis
- Dashboard visualisations and business interpretations

### Running Part 1

Open a terminal inside the `payments_fraud_analytics` folder:

```bash
python generate_data.py
python database_setup.py
python run_sql_queries.py
python reconcile.py
python dashboard.py
```

The Excel workbook can be opened separately for the spreadsheet analysis.

---

# Part 2 — Credit Risk & Lending ML

**Folder:** `credit_risk_lending_ml`

This part focuses on credit-risk modelling and transaction anomaly detection.

It includes:

- Credit applicant and transaction behaviour data
- Thin-file identification and missing bureau-score handling
- Stratified train/test splitting
- Training-only imputation, encoding and scaling
- Logistic Regression and Decision Tree models
- Confusion matrices, classification metrics, ROC and AUC
- Risk-tier analysis
- Isolation Forest anomaly detection
- Risk-pricing analysis

### Key results

**Logistic Regression**
- Accuracy: 76.0%
- Precision: 38.9%
- Recall: 35.0%
- F1 Score: 36.8%
- AUC: 0.719

**Decision Tree**
- Accuracy: 67.0%
- Precision: 24.0%
- Recall: 30.0%
- F1 Score: 26.7%
- AUC: 0.531

Isolation Forest detected 11 of the 15 seeded `BTXNA` anomalies, giving an anomaly recall of 73.3%.

### Running Part 2

Open a terminal inside the `credit_risk_lending_ml` folder:

```bash
python generate_data.py
python run_notebook.py
```

The notebook contains the main modelling workflow and analysis.

---

# Part 3 — AI-Augmented FinTech Advisory & Blockchain Risk

**Folder:** `ai_advisory_blockchain`

This part combines portfolio advisory, disclosure analysis, valuation and blockchain-related risk assessment.

It includes:

- Stock universe and investor profiles
- CAPM-based expected-return calculations
- Portfolio construction and risk calculation
- Human-escalation logic
- Disclosure extraction and risk flags
- Bull, Bear and Synthesizer advisory debate
- DCF valuation
- WACC and sensitivity analysis
- EV/EBITDA cross-check
- Blockchain and crypto risk analysis

The advisory workflow uses the provided mock setup and does not require an external LLM API.

### Key valuation result

For the PAYFIN DCF case:

- Base FCFF: ₹65 crore
- Cost of equity: 15.10%
- After-tax cost of debt: 6.75%
- WACC: 12.595%
- Terminal growth: 5.0%
- Base enterprise value: ₹1,208.96 crore
- EV/EBITDA implied enterprise value: ₹1,120 crore
- Difference: approximately +7.9%

### Running Part 3

Open a terminal inside the `ai_advisory_blockchain` folder:

```bash
python run_all.py
```

The individual Python files can also be run separately when required.

---

# Design Decisions

## Synthetic Data

Controlled synthetic datasets are used so that the payment, credit-risk and anomaly scenarios can be reproduced consistently. The required random seeds are used in the data-generation workflows.

## Fraud Analysis

Payment fraud analysis combines spreadsheet formulas, SQL queries, reconciliation and dashboard analysis. This allows the same transaction data to be examined from operational, database and reporting perspectives.

## Credit Risk

The credit-risk workflow keeps thin-file applicants rather than removing them. Imputation is performed using training-set information to avoid using test-set information during preprocessing. Logistic Regression and Decision Tree models are compared using the same train/test split.

## Anomaly Detection

Isolation Forest is applied to transaction behaviour variables to identify unusual transactions. The seeded `BTXNA` transactions provide a known reference point for evaluating detection performance.

## Investment Advisory

CAPM is used for expected-return calculations, while portfolio risk is calculated using the specified correlation assumption. Human escalation is triggered when portfolio standard deviation exceeds the specified threshold.

## DCF Valuation

The DCF uses FCFF, CAPM-based cost of equity, after-tax cost of debt and WACC. Sensitivity analysis is included to show how valuation changes under different assumptions.

## Blockchain Risk

The blockchain section considers stablecoins, DeFi/DAO governance, tokenomics and crypto allocation while also addressing heavy-tailed returns, survivorship bias and transaction costs.

---

# Reproducibility

Run each data-generation script from its own part folder.

For Part 1:

```bash
cd payments_fraud_analytics
python generate_data.py
```

For Part 2:

```bash
cd credit_risk_lending_ml
python generate_data.py
```

For Part 3:

```bash
cd ai_advisory_blockchain
python run_all.py
```

Generated datasets and analysis outputs are included in the repository so the completed results can also be reviewed without rerunning every step.

---

# Technologies Used

- Python
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- SQLite
- SQL
- Excel
- Jupyter Notebook

---

# Project Outcome

The three parts together demonstrate an end-to-end FinTech analytics workflow:

**Payments → Fraud & Reconciliation → Credit Risk → Lending ML → Investment Advisory → Valuation → Blockchain Risk**

The project combines data analysis, financial modelling, machine learning, database analysis and AI-assisted advisory into a single FinTech case study.
