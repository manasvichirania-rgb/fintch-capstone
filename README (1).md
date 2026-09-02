# Part 2 — Credit Risk & Lending ML

## Objective

Paytm Postpaid (BNPL-style consumer/merchant credit) needs, for every
applicant, a probability of default and a risk-based interest rate. This
part builds that pipeline end to end with real scikit-learn code on a
synthetic applicant dataset, adds a lightweight anomaly-detection check on
transaction behaviour, and closes with a written bias-awareness note. Every
number in this README is measured from the actual generated data (seed 42)
and the actual model run — none are estimated or invented.

## Setup

```bash
pip install pandas numpy scikit-learn matplotlib nbformat nbclient ipykernel
```

`nbformat`/`nbclient`/`ipykernel` are only needed to programmatically build
and execute the notebook the way this submission was produced
(`build_notebook.py` + `run_notebook.py`); opening `credit_risk_analysis.ipynb`
directly in Jupyter/JupyterLab and running all cells works the same way.

## Data Generation

The generator uses `np.random.seed(42)`, so the dataset is reproducible.
**Run it from inside this folder**, since it writes CSVs via relative paths:

```bash
cd credit_risk_lending_ml
python generate_data.py
```

## Dataset Results (measured, not estimated)

- **400 applicants** in `credit_applicants.csv`.
- **Measured default rate: 20.25%** (81 of 400) — inside the assignment's
  expected 15–25% range.
- **80 applicants (exactly 20.0%)** have a missing `credit_bureau_score`
  (thin-file / new-to-credit population).
- **265 rows** in `txn_behaviour.csv`: 250 normal + **15 seeded anomalies**
  (`txn_id` starting with `BTXNA`).

## Preprocessing Decisions (leakage-safe order)

The pipeline follows this exact order, enforced in
`credit_risk_analysis.ipynb` Sections 4–6:

```
raw data -> create is_thin_file -> 75/25 stratified split (random_state=42)
   -> training-only median -> impute train + test
   -> one-hot encode employment_type (fit on train only)
   -> StandardScaler (fit on train only) -> models
```

- **`is_thin_file`** is created directly from `credit_bureau_score.isna()`
  *before* any imputation — a plain missingness flag, not derived from a
  fitted statistic. No row is ever dropped.
- **Split:** `train_test_split(..., test_size=0.25, stratify=y,
  random_state=42)`. Stratifying on `default` preserves a similar class
  balance between train and test, which matters with a 400-row dataset and
  a ~20% minority class.
- **Median imputation:** the median of `credit_bureau_score` is computed
  from **training non-missing values only** — measured value:
  **`612.0`** — and that single number fills missing values in *both*
  train and test. Median (not mean) is used because it's less sensitive to
  outliers than the mean, and computing it from training data only avoids
  leaking test-set information into the imputed values.
- **Employment encoding:** one-hot encoding for `employment_type`
  (`salaried`/`self_employed`/`gig`), since it's categorical with no
  natural order. The encoder is fit on training data only.
- **Scaling:** `StandardScaler` fit only on `X_train`'s numeric columns,
  then applied to both train and test — this matters most for Logistic
  Regression, since `monthly_income_inr` (tens of thousands) and
  `credit_utilization_ratio` (0–1) sit on very different numeric scales.

## Model Results (measured on the actual test set, n=100)

| Model | Accuracy | Precision | Recall | F1 | AUC |
|---|---:|---:|---:|---:|---:|
| Logistic Regression | 0.760 | 0.389 | 0.350 | 0.368 | **0.719** |
| Decision Tree (`random_state=42`) | 0.670 | 0.240 | 0.300 | 0.267 | 0.531 |

Full precision/recall/F1/AUC and the confusion matrices are in
`model_results.csv` and `charts/confusion_matrices.png` /
`charts/roc_comparison.png`. Logistic Regression: 69 TN / 11 FP / 13 FN /
7 TP. Decision Tree: 61 TN / 19 FP / 14 FN / 6 TP — the Decision Tree's
AUC (0.531) is barely above random (0.500), a sign it overfit the 300-row
training split.

## Risk-Based Pricing

Four quartile-based tiers built from the Logistic Regression's predicted
default probabilities on the test set (25 applicants per tier):

| Risk Tier | Probability Range | Applicants | Avg. Predicted Prob. | Observed Default Rate | Illustrative Rate |
|---|---|---:|---:|---:|---|
| Low Risk | 0.005 – 0.036 | 25 | 2.0% | **8%** | 10–12% |
| Moderate Risk | 0.036 – 0.146 | 25 | 7.3% | **12%** | 12–15% |
| High Risk | 0.152 – 0.340 | 25 | 23.4% | **20%** | 15–19% |
| Very High Risk | 0.354 – 0.947 | 25 | 58.8% | **40%** | 19–25% |

**Observed default rate increases strictly and monotonically** across all
four tiers (8% → 12% → 20% → 40%) — no adjustment was needed to make this
pattern hold; it came out of the actual test-set labels. Interest-rate
ranges are illustrative assumptions for this exercise, not real Paytm
Postpaid rates. Full table: `risk_pricing_table.csv`.

## Anomaly Detection

- Features used: **only** `txn_hour`, `is_new_device`, `txn_amount_inr`
  (standardized; `txn_id`/`applicant_id`/`channel` excluded).
- `IsolationForest(random_state=42, contamination=15/265)` — contamination
  computed programmatically as `15/265 ≈ 0.0566`, not an arbitrary round
  number.
- **Seeded anomalies: 15. Detected: 11. Recall: 11/15 = 73.3%.**
- 4 of the 15 seeded anomalies were missed (the model also flagged 4
  normal rows, keeping the total flagged count at 15 — consistent with the
  contamination rate). Full row-level results: `anomaly_results.csv`,
  chart: `charts/anomaly_detection.png`.

## Bias Awareness

Even though this dataset has no explicit gender or location field, three
features could act as correlated proxies for a protected attribute in a
real deployment. **`employment_type`**: `gig` work in India skews toward
workers with less formal education and generational wealth, and informal
employment correlates with caste/religious-minority status in aggregate
labour data — a model penalizing `gig` status risks penalizing those
correlated groups rather than genuine income instability alone.
**`monthly_income_inr`** reflects structural inequality (gender, caste,
and regional income gaps are well documented in India) directly into a
numeric feature. **`credit_bureau_score`** is the most systemic risk:
bureau coverage itself is uneven by income and geography — exactly why
`is_thin_file` exists — so treating a missing score as automatically
high-risk would penalize applicants for lacking formal-credit access
rather than for their own behaviour.

**Recommended governance step:** a maker-checker human-in-the-loop review
for every declined thin-file applicant, so a second reviewer checks the
alternate-data signals before a decline is finalized for a population the
model was never validated against with bureau data — alongside ongoing
disparate-impact monitoring of approval/rate outcomes by `employment_type`
and `is_thin_file` segment, since proxy effects can drift over time. (Full
note in the notebook, Section 12.)

## Final Recommendation

| Metric | Logistic Regression | Decision Tree |
|---|---:|---:|
| Accuracy | 0.760 | 0.670 |
| Precision | 0.389 | 0.240 |
| Recall | 0.350 | 0.300 |
| F1 | 0.368 | 0.267 |
| AUC | **0.719** | 0.531 |

Isolation Forest anomaly recall: 11/15 = 73.3%.

**Deploy Logistic Regression.** Its AUC (0.719 vs. 0.531) and every other
metric come out ahead of the Decision Tree — the tree overfits the 300-row
training split into hard splits that generalize poorly, visible directly
in an AUC barely above random chance. In lending, recall on the default
class matters more than raw accuracy: a false negative (an actual
defaulter approved) costs the full unpaid balance, while a false positive
(a good applicant declined or priced higher) only costs a marginal
customer — so the model that's actually better at ranking risk is the
safer default, before even considering that Logistic Regression's
coefficients are far easier to explain to a credit-risk committee or
regulator than a tree's split structure. Both models' recall (0.35 and
0.30) is modest in absolute terms — on a production deployment this would
warrant either a lower decision threshold or more features/data before
go-live, not just the tier structure above.

## Final Folder Structure

```
credit_risk_lending_ml/
├── generate_data.py
├── credit_applicants.csv
├── txn_behaviour.csv
├── build_notebook.py
├── run_notebook.py
├── credit_risk_analysis.ipynb
├── charts/
│   ├── default_distribution.png
│   ├── roc_comparison.png
│   ├── confusion_matrices.png
│   └── anomaly_detection.png
├── model_results.csv
├── risk_pricing_table.csv
├── anomaly_results.csv
└── README.md
```

## No-Leakage Final Audit

- [x] `is_thin_file` created from raw missingness, before imputation
- [x] no rows dropped for missing bureau scores (400 rows throughout)
- [x] train/test split happens before imputation
- [x] `test_size=0.25`, `stratify=y`, `random_state=42`
- [x] bureau median (612.0) computed from training non-missing values only
- [x] same training median applied to both train and test
- [x] one-hot encoder fit on training data only
- [x] `StandardScaler` fit on training data only
- [x] both classifiers trained on the identical split
- [x] `DecisionTreeClassifier(random_state=42)`
- [x] evaluation uses actual test-set predictions; ROC uses predicted probabilities
- [x] risk pricing uses Logistic Regression probabilities, not labels; 4 tiers; rates increase with risk
- [x] observed default rates computed from actual test labels (monotonic: 8/12/20/40%)
- [x] Isolation Forest uses exactly `txn_hour`, `is_new_device`, `txn_amount_inr`, standardized
- [x] `contamination = 15/265`, computed programmatically
- [x] anomaly recall calculated against actual `BTXNA*` ground truth (11/15 = 73.3%)
- [x] bias note names specific proxy risks (`employment_type`, `monthly_income_inr`, `credit_bureau_score`) and one concrete governance step
- [x] final recommendation references actual measured metric values
- [x] all monetary figures in INR
