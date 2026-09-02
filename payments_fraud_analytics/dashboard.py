"""
dashboard.py

Part D: Four-layer analytics dashboard, rendered as saved chart images in
charts/ (no live BI tool dependency). Metric definitions used here are:

- match_rate = (# txns present in BOTH ledger and gateway export with
  IDENTICAL amount_inr AND IDENTICAL status) / (total ledger txn count).
  This is separate from the four reconcile.py discrepancy categories.
- chargeback_ratio (headline, platform-wide) = count(chargeback) / count(all),
  count-based, expressed as a percentage.
- per-merchant chargeback_ratio (details layer) = count(that merchant's
  chargebacks) / count(that merchant's txns), count-based.

Run:
    python dashboard.py
"""

import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)


def load_data():
    ledger = pd.read_csv("ledger.csv", parse_dates=["transaction_time"])
    gateway = pd.read_csv("gateway_export.csv", parse_dates=["transaction_time"])
    merchants = pd.read_csv("merchants.csv")
    ledger = ledger.merge(merchants, on="merchant_id", how="left")
    return ledger, gateway, merchants



def compute_headline_metrics(ledger, gateway):
    n = len(ledger)

    total_gmv = ledger["amount_inr"].sum()
    success_rate = (ledger["status"] == "captured").mean()

    merged = pd.merge(
        ledger[["transaction_id", "amount_inr", "status"]],
        gateway[["transaction_id", "amount_inr", "status"]],
        on="transaction_id", how="inner", suffixes=("_ledger", "_gateway")
    )
    matched = (
        (merged["amount_inr_ledger"] == merged["amount_inr_gateway"]) &
        (merged["status_ledger"] == merged["status_gateway"])
    ).sum()
    match_rate = matched / n

    chargeback_ratio = (ledger["status"] == "chargeback").mean()

    return {
        "Total GMV (INR)": f"Rs {total_gmv:,.0f}",
        "Success Rate": f"{success_rate:.1%}",
        "Reconciliation Match Rate": f"{match_rate:.1%}",
        "Chargeback Ratio": f"{chargeback_ratio:.2%}",
    }


def render_headline(metrics):
    fig, ax = plt.subplots(figsize=(10, 2.2))
    ax.axis("off")
    n = len(metrics)
    for i, (label, value) in enumerate(metrics.items()):
        x = (i + 0.5) / n
        ax.text(x, 0.62, value, ha="center", va="center", fontsize=20, fontweight="bold",
                transform=ax.transAxes, color="#1a1a2e")
        ax.text(x, 0.18, label, ha="center", va="center", fontsize=11,
                transform=ax.transAxes, color="#555555")
    ax.set_title("Headline Scorecards — Paytm Payments (30-day window)", fontsize=13, pad=14)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "headline.png"), dpi=150)
    plt.close(fig)



def render_trends(ledger):
    ledger = ledger.copy()
    ledger["date"] = ledger["transaction_time"].dt.date
    daily_gmv = ledger.groupby("date")["amount_inr"].sum()
    daily_chargebacks = ledger[ledger["status"] == "chargeback"].groupby("date").size()
    daily_chargebacks = daily_chargebacks.reindex(daily_gmv.index, fill_value=0)

    fig, ax1 = plt.subplots(figsize=(11, 4.5))
    ax1.bar(daily_gmv.index.astype(str), daily_gmv.values, color="#2e6f95", alpha=0.75, label="Daily GMV (INR)")
    ax1.set_ylabel("Daily GMV (INR)", color="#2e6f95")
    ax1.tick_params(axis="x", rotation=75, labelsize=7)
    ax1.tick_params(axis="y", labelcolor="#2e6f95")

    ax2 = ax1.twinx()
    ax2.plot(daily_gmv.index.astype(str), daily_chargebacks.values, color="#c0392b",
              marker="o", linewidth=2, label="Daily Chargeback Count")
    ax2.set_ylabel("Daily Chargeback Count", color="#c0392b")
    ax2.tick_params(axis="y", labelcolor="#c0392b")

    fig.suptitle("Trends — Daily GMV vs Daily Chargeback Count", fontsize=13)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "trends.png"), dpi=150)
    plt.close(fig)

    return daily_gmv, daily_chargebacks



def render_breakdown_payment_method(ledger):
    gmv_by_method = ledger.groupby("payment_method")["amount_inr"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(gmv_by_method.index, gmv_by_method.values, color="#3f7d5c")
    ax.set_ylabel("GMV (INR)")
    ax.set_title("GMV by Payment Method")
    for i, v in enumerate(gmv_by_method.values):
        ax.text(i, v, f"{v:,.0f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "breakdown_payment_method.png"), dpi=150)
    plt.close(fig)
    return gmv_by_method


def render_breakdown_category(ledger):
    gmv_by_category = ledger.groupby("category")["amount_inr"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(gmv_by_category.index[::-1], gmv_by_category.values[::-1], color="#8e5b9c")
    ax.set_xlabel("GMV (INR)")
    ax.set_title("GMV by Merchant Category")
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "breakdown_category.png"), dpi=150)
    plt.close(fig)
    return gmv_by_category



def render_merchant_details(ledger):
    grp = ledger.groupby(["merchant_id", "merchant_name"])
    summary = grp.agg(
        transaction_count=("transaction_id", "count"),
        total_gmv=("amount_inr", "sum"),
        chargeback_count=("status", lambda s: (s == "chargeback").sum()),
    ).reset_index()
    summary["chargeback_ratio"] = summary["chargeback_count"] / summary["transaction_count"]
    summary["flag"] = summary["chargeback_ratio"].apply(lambda r: "HIGH RISK" if r > 0.01 else "")
    top10 = summary.sort_values("transaction_count", ascending=False).head(10).reset_index(drop=True)

    display_df = top10.copy()
    display_df["total_gmv"] = display_df["total_gmv"].apply(lambda v: f"Rs {v:,.0f}")
    display_df["chargeback_ratio"] = display_df["chargeback_ratio"].apply(lambda r: f"{r:.2%}")
    display_df = display_df[["merchant_id", "merchant_name", "transaction_count", "total_gmv",
                              "chargeback_count", "chargeback_ratio", "flag"]]

    fig, ax = plt.subplots(figsize=(11, 0.55 * len(display_df) + 1.3))
    ax.axis("off")
    table = ax.table(cellText=display_df.values, colLabels=display_df.columns,
                      loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.6)

    # conditional highlighting for the high-risk flag column
    flag_col_idx = list(display_df.columns).index("flag")
    for row_i in range(len(display_df)):
        if display_df.iloc[row_i]["flag"] == "HIGH RISK":
            for col_i in range(len(display_df.columns)):
                table[(row_i + 1, col_i)].set_facecolor("#f8d7da")
            table[(row_i + 1, flag_col_idx)].set_text_props(color="#a11", fontweight="bold")

    for col_i in range(len(display_df.columns)):
        table[(0, col_i)].set_facecolor("#2e2e40")
        table[(0, col_i)].set_text_props(color="white", fontweight="bold")

    ax.set_title("Top 10 Merchants by Transaction Count (Details Layer)", fontsize=13, pad=18)
    fig.tight_layout()
    fig.savefig(os.path.join(CHARTS_DIR, "merchant_details.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return top10


def main():
    ledger, gateway, merchants = load_data()

    headline_metrics = compute_headline_metrics(ledger, gateway)
    render_headline(headline_metrics)

    daily_gmv, daily_chargebacks = render_trends(ledger)
    gmv_by_method = render_breakdown_payment_method(ledger)
    gmv_by_category = render_breakdown_category(ledger)
    top10 = render_merchant_details(ledger)

    print("Headline metrics:")
    for k, v in headline_metrics.items():
        print(f"  {k}: {v}")
    print("\nGMV by payment method:")
    print(gmv_by_method.to_string())
    print("\nGMV by category:")
    print(gmv_by_category.to_string())
    print("\nTop 10 merchants by transaction count:")
    print(top10.to_string(index=False))
    print(f"\nCharts saved to {os.path.abspath(CHARTS_DIR)}/")


if __name__ == "__main__":
    main()
