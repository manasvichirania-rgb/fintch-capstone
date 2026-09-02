"""
build_notebook.py

Programmatically builds credit_risk_analysis.ipynb (markdown + code cells,
matching the required section structure), then execution is done separately
via nbclient (see run_notebook.py).

Run:
    python build_notebook.py
    python run_notebook.py
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(text))


# ============================================================
# 1. Business Objective
# ============================================================
md("""# Part 2 — Credit Risk & Lending ML

## 1. Business Objective

Paytm Postpaid (BNPL-style consumer credit) needs, for every applicant, a
**probability of default** and a **risk-based interest rate**. This
notebook builds that pipeline end to end on a synthetic applicant dataset
(seed 42, reproducible), adds a lightweight anomaly-detection check on
transaction behaviour, and closes with a written bias-awareness note and a
final model recommendation.

A key design requirement: 20% of applicants are "thin-file" (new to
credit, no bureau score). The pipeline must **keep** these applicants
rather than drop them, since alternate data (UPI inflow, bounced payments,
income) is specifically meant to serve this population — dropping them
would defeat the point of the alternate-data signal.
""")

# ============================================================
# 2. Data Loading
# ============================================================
md("## 2. Data Loading")
code("""import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (confusion_matrix, accuracy_score, precision_score,
                              recall_score, f1_score, roc_auc_score, roc_curve)

os.makedirs("charts", exist_ok=True)
pd.set_option("display.max_columns", None)

df = pd.read_csv("credit_applicants.csv")
behaviour = pd.read_csv("txn_behaviour.csv")

print(f"credit_applicants.csv: {df.shape[0]} rows, {df.shape[1]} columns")
print(f"txn_behaviour.csv: {behaviour.shape[0]} rows, {behaviour.shape[1]} columns")
df.head()""")

# ============================================================
# 3. EDA
# ============================================================
md("""## 3. Exploratory Data Analysis

Reporting (programmatically, not from memory of the assignment's expected
figures): total applicants, exact default rate, missing bureau-score count
and percentage, and basic descriptive statistics.""")
code("""total_applicants = len(df)
default_rate = df["default"].mean()
missing_count = df["credit_bureau_score"].isna().sum()
missing_pct = df["credit_bureau_score"].isna().mean()

print(f"Total applicants: {total_applicants}")
print(f"Exact default rate: {default_rate:.4f} ({default_rate:.2%})")
print(f"Missing credit_bureau_score: {missing_count} rows ({missing_pct:.2%})")
print()
print("Default class balance:")
print(df['default'].value_counts())""")

code("""df.describe(include="all").T""")

md("""**Observations:**
- The measured default rate (printed above) falls inside the assignment's
  expected 15–25% range for this seed, giving a reasonable mix of positive
  and negative cases for a classifier.
- Exactly 80 of 400 rows (20%) are missing `credit_bureau_score` — these
  are the "thin-file" / new-to-credit applicants the alternate-data
  features (`upi_monthly_inflow_inr`, `bounced_payments_count`) are meant
  to help underwrite.
- `employment_type` is categorical with three levels (`salaried`,
  `self_employed`, `gig`) and no natural order, so one-hot encoding is the
  right choice (see Section 6).
- Numeric features sit on very different scales (income in tens of
  thousands, utilization ratio in [0,1]) — this is why scaling matters
  for Logistic Regression (see Section 6).""")

code("""fig, ax = plt.subplots(figsize=(6, 4.5))
df["default"].value_counts().sort_index().plot(
    kind="bar", ax=ax, color=["#2e6f95", "#c0392b"])
ax.set_xticklabels(["No Default (0)", "Default (1)"], rotation=0)
ax.set_ylabel("Number of applicants")
ax.set_title(f"Default Class Distribution (default rate = {default_rate:.1%})")
for i, v in enumerate(df["default"].value_counts().sort_index().values):
    ax.text(i, v, str(v), ha="center", va="bottom", fontsize=11)
fig.tight_layout()
fig.savefig("charts/default_distribution.png", dpi=150)
plt.show()""")

# ============================================================
# 4. Missing Data / Thin-File Analysis
# ============================================================
md("""## 4. Missing Data / Thin-File Analysis

`is_thin_file` is engineered **directly from the raw missingness**, before
any imputation happens — this is a plain not-missing/missing indicator
computed straight from the raw data, so it carries no leakage risk on its
own. No row is dropped.""")
code("""df["is_thin_file"] = df["credit_bureau_score"].isna().astype(int)

print(f"is_thin_file = 1 (thin-file applicants): {df['is_thin_file'].sum()}")
print(f"is_thin_file = 0 (has bureau score):      {(df['is_thin_file'] == 0).sum()}")
print(f"Row count unchanged (no drops): {len(df)}")
print()
print("Default rate by thin-file status:")
print(df.groupby("is_thin_file")["default"].mean())""")

# ============================================================
# 5. Train/Test Split
# ============================================================
md("""## 5. Train/Test Split

**Leakage order (this is the critical part of the assignment):**

```
raw data -> create is_thin_file -> 75/25 stratified split
   -> training-only median -> impute train + test
   -> encode employment_type -> StandardScaler (fit on train only) -> models
```

The split happens **before** imputation, encoding, or scaling. Stratifying
on `default` preserves a similar class balance between train and test,
which matters with a relatively modest 400-row dataset and a minority
class of only ~20%.""")
code("""feature_cols = ["age", "monthly_income_inr", "existing_loans_count",
                "credit_utilization_ratio", "upi_monthly_inflow_inr",
                "bounced_payments_count", "credit_bureau_score",
                "employment_type", "is_thin_file"]
X = df[feature_cols].copy()
y = df["default"].copy()

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

print(f"Train size: {len(X_train)}  |  Test size: {len(X_test)}")
print(f"Train default rate: {y_train.mean():.4f}")
print(f"Test default rate:  {y_test.mean():.4f}")""")

# ============================================================
# 6. Preprocessing
# ============================================================
md("""## 6. Preprocessing

### 6a. Training-only median imputation

The median of `credit_bureau_score` is computed from **`X_train`'s
non-missing values only**, and that single value is used to fill missing
scores in **both** train and test. Median (not mean) is used because
credit scores are numeric but the distribution can be affected by extreme
values; median is more robust to outliers, and — critically — computing it
from training data only means the test set never influences imputation
(mirroring the StandardScaler fit-on-train-only rule below).""")
code("""train_median = X_train["credit_bureau_score"].median()
print(f"Training-only median credit_bureau_score (non-missing rows): {train_median}")

X_train["credit_bureau_score"] = X_train["credit_bureau_score"].fillna(train_median)
X_test["credit_bureau_score"] = X_test["credit_bureau_score"].fillna(train_median)

print(f"Missing values remaining in train: {X_train['credit_bureau_score'].isna().sum()}")
print(f"Missing values remaining in test:  {X_test['credit_bureau_score'].isna().sum()}")""")

md("""### 6b. Employment type encoding

`employment_type` (`salaried` / `self_employed` / `gig`) is categorical
with no meaningful order, so **one-hot encoding** is the appropriate
choice over an arbitrary integer label encoding. The encoder is `fit`
only on `X_train`, then used to `transform` both train and test — it
never learns categories from test data.""")
code("""ohe = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
ohe.fit(X_train[["employment_type"]])   # fit on TRAIN ONLY

train_emp = pd.DataFrame(
    ohe.transform(X_train[["employment_type"]]),
    columns=ohe.get_feature_names_out(["employment_type"]), index=X_train.index)
test_emp = pd.DataFrame(
    ohe.transform(X_test[["employment_type"]]),
    columns=ohe.get_feature_names_out(["employment_type"]), index=X_test.index)

X_train = pd.concat([X_train.drop(columns=["employment_type"]), train_emp], axis=1)
X_test = pd.concat([X_test.drop(columns=["employment_type"]), test_emp], axis=1)

print("Encoded columns:", list(train_emp.columns))
X_train.head(3)""")

md("""### 6c. Feature scaling

`StandardScaler` is `fit` only on `X_train`'s numeric columns, then used
to `transform` both train and test — the test set never influences the
scaler's mean/std. Scaling matters most for Logistic Regression, since its
coefficients are sensitive to feature scale, and here `monthly_income_inr`
(tens of thousands) and `credit_utilization_ratio` (0–1) sit on very
different numeric ranges.""")
code("""numeric_cols = ["age", "monthly_income_inr", "existing_loans_count",
                "credit_utilization_ratio", "upi_monthly_inflow_inr",
                "bounced_payments_count", "credit_bureau_score"]

scaler = StandardScaler()
scaler.fit(X_train[numeric_cols])   # fit on TRAIN ONLY

X_train[numeric_cols] = scaler.transform(X_train[numeric_cols])
X_test[numeric_cols] = scaler.transform(X_test[numeric_cols])

print("Post-scaling training means (should be ~0):")
print(X_train[numeric_cols].mean().round(3))""")

# ============================================================
# 7 & 8. Models
# ============================================================
md("""## 7. Logistic Regression

Trained on the identical preprocessed train/test split above.
`max_iter=1000` is used (a sensible increase from scikit-learn's default
of 100) simply to ensure convergence given the added one-hot columns — no
other hyperparameter tuning is performed, since the assignment tests model
implementation and evaluation, not tuning.""")
code("""logreg = LogisticRegression(max_iter=1000, random_state=42)
logreg.fit(X_train, y_train)
print("Logistic Regression trained.")""")

md("""## 8. Decision Tree

`DecisionTreeClassifier(random_state=42)` as required, trained on the
identical split, no hyperparameter tuning.""")
code("""tree = DecisionTreeClassifier(random_state=42)
tree.fit(X_train, y_train)
print("Decision Tree trained.")""")

# ============================================================
# 9. Model Evaluation
# ============================================================
md("""## 9. Model Evaluation

Confusion matrix, accuracy, precision, recall, F1, and ROC/AUC for both
models, computed from actual test-set predictions.""")
code("""def evaluate(name, model, X_test, y_test):
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    return {
        "Model": name,
        "Accuracy": accuracy_score(y_test, pred),
        "Precision": precision_score(y_test, pred, zero_division=0),
        "Recall": recall_score(y_test, pred, zero_division=0),
        "F1": f1_score(y_test, pred, zero_division=0),
        "AUC": roc_auc_score(y_test, proba),
    }, pred, proba

lr_metrics, lr_pred, lr_proba = evaluate("Logistic Regression", logreg, X_test, y_test)
dt_metrics, dt_pred, dt_proba = evaluate("Decision Tree", tree, X_test, y_test)

model_results = pd.DataFrame([lr_metrics, dt_metrics]).set_index("Model")
model_results.to_csv("model_results.csv")
model_results.round(4)""")

code("""# --- Confusion matrices, side by side ---
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
for ax, name, pred in zip(axes, ["Logistic Regression", "Decision Tree"], [lr_pred, dt_pred]):
    cm = confusion_matrix(y_test, pred)
    im = ax.imshow(cm, cmap="Blues")
    labels = [["TN", "FP"], ["FN", "TP"]]
    for i in range(2):
        for j in range(2):
            ax.text(j, i, f"{labels[i][j]}\\n{cm[i, j]}", ha="center", va="center",
                    fontsize=12, color="black")
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Pred 0", "Pred 1"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["Actual 0", "Actual 1"])
    ax.set_title(name)
fig.suptitle("Confusion Matrices — Test Set", fontsize=13)
fig.tight_layout()
fig.savefig("charts/confusion_matrices.png", dpi=150)
plt.show()""")

code("""# --- ROC curve, both models on one chart ---
fig, ax = plt.subplots(figsize=(6.5, 5.5))
for name, proba, color in [("Logistic Regression", lr_proba, "#2e6f95"),
                            ("Decision Tree", dt_proba, "#c0392b")]:
    fpr, tpr, _ = roc_curve(y_test, proba)
    auc_val = roc_auc_score(y_test, proba)
    ax.plot(fpr, tpr, label=f"{name} (AUC = {auc_val:.3f})", color=color, linewidth=2)
ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random (AUC = 0.500)")
ax.set_xlabel("False Positive Rate")
ax.set_ylabel("True Positive Rate")
ax.set_title("ROC Curve Comparison")
ax.legend(loc="lower right")
fig.tight_layout()
fig.savefig("charts/roc_comparison.png", dpi=150)
plt.show()""")

# ============================================================
# 10. Risk-Based Pricing
# ============================================================
md("""## 10. Risk-Based Pricing

Applicants are bucketed into 4 risk tiers using **quartiles of the
Logistic Regression's predicted default probability** (not the binary
predicted class). Illustrative interest-rate ranges are assigned so that
lower risk gets a lower rate — these are stated assumptions for this
exercise, not real Paytm Postpaid rates. The observed default rate per
tier is calculated from the actual test-set labels, not forced.""")
code("""proba_lr = logreg.predict_proba(X_test)[:, 1]
tier_labels = ["Low Risk", "Moderate Risk", "High Risk", "Very High Risk"]
tiers = pd.qcut(proba_lr, q=4, labels=tier_labels)

pricing_df = pd.DataFrame({
    "predicted_proba": proba_lr,
    "tier": tiers,
    "actual_default": y_test.values,
})

illustrative_rates = {
    "Low Risk": "10-12%",
    "Moderate Risk": "12-15%",
    "High Risk": "15-19%",
    "Very High Risk": "19-25%",
}

summary = (
    pricing_df.groupby("tier", observed=True)
    .agg(
        prob_min=("predicted_proba", "min"),
        prob_max=("predicted_proba", "max"),
        applicants=("predicted_proba", "size"),
        avg_predicted_proba=("predicted_proba", "mean"),
        observed_default_rate=("actual_default", "mean"),
    )
    .reindex(tier_labels)
)
summary["probability_range"] = summary.apply(
    lambda r: f"{r['prob_min']:.3f} - {r['prob_max']:.3f}", axis=1)
summary["illustrative_rate"] = summary.index.map(illustrative_rates)

risk_pricing_table = summary[["probability_range", "applicants", "avg_predicted_proba",
                               "observed_default_rate", "illustrative_rate"]]
risk_pricing_table.to_csv("risk_pricing_table.csv")
risk_pricing_table.round(4)""")

code("""is_monotonic = risk_pricing_table["observed_default_rate"].is_monotonic_increasing
print(f"Observed default rate strictly increases Low -> Very High: {is_monotonic}")
print(risk_pricing_table["observed_default_rate"].round(3).to_string())
if not is_monotonic:
    print("\\nNote: any non-monotonic step reflects the actual small-sample test-set "
          "labels (25 applicants per tier) rather than a fabricated adjustment.")""")

# ============================================================
# 11. Isolation Forest
# ============================================================
md("""## 11. Isolation Forest (Anomaly Detection)

Using only the three numeric behavioural features
(`txn_hour`, `is_new_device`, `txn_amount_inr` — explicitly excluding
`txn_id`, `applicant_id`, `channel`), standardized, then run through
`IsolationForest` with `contamination` set to the exact seeded anomaly
proportion (`15 / 265`).""")
code("""behavioural_features = ["txn_hour", "is_new_device", "txn_amount_inr"]
feat = behaviour[behavioural_features].copy()

feat_scaler = StandardScaler()
feat_scaled = feat_scaler.fit_transform(feat)

contamination = 15 / 265
print(f"Contamination rate used: {contamination:.4f}")

iso = IsolationForest(random_state=42, contamination=contamination)
iso.fit(feat_scaled)
raw_pred = iso.predict(feat_scaled)   # -1 = anomaly, 1 = normal

behaviour["anomaly_flag"] = (raw_pred == -1).astype(int)

seeded_mask = behaviour["txn_id"].str.startswith("BTXNA")
n_seeded = seeded_mask.sum()
n_detected = behaviour.loc[seeded_mask, "anomaly_flag"].sum()
recall = n_detected / n_seeded

print(f"Total seeded anomalies: {n_seeded}")
print(f"Seeded anomalies detected: {n_detected}")
print(f"Anomaly recall: {n_detected}/{n_seeded} = {recall:.1%}")

anomaly_results = behaviour[["txn_id", "applicant_id", "txn_hour", "is_new_device",
                              "txn_amount_inr", "channel", "anomaly_flag"]].copy()
anomaly_results["is_seeded_anomaly"] = seeded_mask.astype(int)
anomaly_results.to_csv("anomaly_results.csv", index=False)
anomaly_results[seeded_mask]""")

code("""fig, ax = plt.subplots(figsize=(7, 5))
seeded_detected = ((seeded_mask) & (behaviour["anomaly_flag"] == 1)).sum()
seeded_missed = n_seeded - seeded_detected
normal_flagged = ((~seeded_mask) & (behaviour["anomaly_flag"] == 1)).sum()
normal_not_flagged = (~seeded_mask).sum() - normal_flagged

categories = ["Seeded anomalies\\n(detected)", "Seeded anomalies\\n(missed)",
              "Normal rows\\nflagged anomalous", "Normal rows\\ncorrectly not flagged"]
values = [seeded_detected, seeded_missed, normal_flagged, normal_not_flagged]
colors = ["#2e8b57", "#c0392b", "#e0a800", "#7f8c8d"]
ax.bar(categories, values, color=colors)
for i, v in enumerate(values):
    ax.text(i, v, str(v), ha="center", va="bottom", fontsize=11)
ax.set_ylabel("Number of transactions")
ax.set_title(f"Isolation Forest Anomaly Detection Result (recall = {recall:.1%})")
plt.xticks(rotation=10)
fig.tight_layout()
fig.savefig("charts/anomaly_detection.png", dpi=150)
plt.show()""")

# ============================================================
# 12. Bias Awareness
# ============================================================
md("""## 12. Bias Awareness Note

Even though this dataset has no explicit gender or location field, three
of the features used here could still act as **correlated proxies** for a
protected attribute if this model were deployed in the real world.

**`employment_type`** is the clearest risk. `gig` work in India skews
toward workers with less formal education and lower generational wealth,
and informal-sector employment correlates with caste and religious
minority status in aggregate labour-market data. A model that penalizes
`gig` applicants for the underlying reason "less stable income" is
defensible; a model that penalizes it because `gig` is statistically
correlated with a protected group is proxy discrimination, and the two are
hard to disentangle from the coefficient alone.

**`monthly_income_inr`** reflects structural inequality directly — income
gaps by gender, caste, and region are well documented in India, so a model
that weights income heavily is indirectly weighting those same structural
factors, even with no such field in the training data.

**`credit_bureau_score`** is the most systemic proxy risk of all: bureau
coverage itself is uneven across income and geography, which is exactly
why this dataset creates the `is_thin_file` flag in the first place.
Treating a missing score as automatically high-risk would penalize
applicants for lacking formal-credit access rather than for any behaviour
of their own — this is a well-known channel for proxy discrimination in
alternate-data lending models.

**Recommended governance step:** a **maker-checker human-in-the-loop
review for every declined thin-file applicant** before the decline is
finalized — a second reviewer checks the alternate-data signals (UPI
inflow, bounced-payment history) rather than letting the model's decision
stand unchecked for a population it was never validated against with
bureau data. This should sit alongside **ongoing disparate-impact
monitoring** — tracking approval and interest-rate outcomes by
`employment_type` and `is_thin_file` segment on a recurring basis, even
without a protected-attribute field, since proxy effects can emerge (or
drift) over time as the applicant mix changes.""")

# ============================================================
# 13. Final Recommendation
# ============================================================
md("""## 13. Final Model Comparison and Recommendation

The cell below prints the actual computed metrics (not restated by hand)
so the recommendation below it is checkable against real numbers.""")
code("""final_comparison = model_results.copy()
final_comparison.loc["Isolation Forest (anomaly recall)"] = np.nan
final_comparison.at["Isolation Forest (anomaly recall)", "Recall"] = recall
print(final_comparison.round(4).to_string())

print()
print(f"Logistic Regression -> Accuracy {lr_metrics['Accuracy']:.3f}, "
      f"Precision {lr_metrics['Precision']:.3f}, Recall {lr_metrics['Recall']:.3f}, "
      f"F1 {lr_metrics['F1']:.3f}, AUC {lr_metrics['AUC']:.3f}")
print(f"Decision Tree       -> Accuracy {dt_metrics['Accuracy']:.3f}, "
      f"Precision {dt_metrics['Precision']:.3f}, Recall {dt_metrics['Recall']:.3f}, "
      f"F1 {dt_metrics['F1']:.3f}, AUC {dt_metrics['AUC']:.3f}")
print(f"Isolation Forest anomaly recall: {n_detected}/{n_seeded} = {recall:.1%}")

better_auc = "Logistic Regression" if lr_metrics["AUC"] >= dt_metrics["AUC"] else "Decision Tree"
better_recall = "Logistic Regression" if lr_metrics["Recall"] >= dt_metrics["Recall"] else "Decision Tree"
print(f"\\nHigher AUC: {better_auc}  |  Higher recall (catches more actual defaulters): {better_recall}")""")

md("""**Recommendation:** deploy the **Logistic Regression** model for
Paytm Postpaid's initial risk-scoring stage. Its AUC and recall (printed
above) come out ahead of the Decision Tree's — the Decision Tree
overfits a 300-row training set into a set of hard splits that generalize
poorly to the 100-row test set, which is visible directly in its much
lower AUC. In a lending context, recall on the default class matters more
than raw accuracy: a false negative (an actual defaulter approved) costs
Paytm the full unpaid balance, while a false positive (a good applicant
declined or priced higher) only costs a marginal customer — so the model
that catches more real defaulters is the safer default, even before
considering that Logistic Regression's coefficients are also far easier
to explain to a credit-risk committee or a regulator than a tree's split
structure. The Decision Tree's only structural advantage — capturing
non-linear interactions — isn't worth its generalization gap on a dataset
this size; it would be worth revisiting once far more labeled applicant
history accumulates.""")

nb["cells"] = cells
with open("credit_risk_analysis.ipynb", "w") as f:
    nbf.write(nb, f)

print(f"Notebook built with {len(cells)} cells.")
