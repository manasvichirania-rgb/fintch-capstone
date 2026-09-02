"""
reconcile.py

Part C: Python payment reconciliation.

reconcile_payments(ledger_df, gateway_df) compares the internal ledger
against the payment gateway's export and returns four DataFrames:

    1. missing_in_gateway   - transaction_ids present in the ledger but
                               absent from the gateway export
    2. extra_in_gateway     - transaction_ids present in the gateway export
                               but absent from the ledger
    3. amount_mismatches    - transaction_ids present in both, but with a
                               different amount_inr (difference computed)
    4. status_mismatches    - transaction_ids present in both, but with a
                               different status


"""

import pandas as pd


def reconcile_payments(ledger_df: pd.DataFrame, gateway_df: pd.DataFrame):
    """Compare a ledger DataFrame against a gateway-export DataFrame.

    Both DataFrames are expected to have at least: transaction_id,
    amount_inr, status.

    Returns
    -------
    (missing_in_gateway, extra_in_gateway, amount_mismatches, status_mismatches)
    """

    ledger_ids = set(ledger_df["transaction_id"])
    gateway_ids = set(gateway_df["transaction_id"])

    # Find transactions missing from the gateway
    missing_ids = ledger_ids - gateway_ids
    missing_in_gateway = ledger_df[ledger_df["transaction_id"].isin(missing_ids)].copy()

    # Find transactions that appear only in the gateway
    extra_ids = gateway_ids - ledger_ids
    extra_in_gateway = gateway_df[gateway_df["transaction_id"].isin(extra_ids)].copy()

    # Compare rows that appear in both files
    both_ids = ledger_ids & gateway_ids
    ledger_both = ledger_df[ledger_df["transaction_id"].isin(both_ids)]
    gateway_both = gateway_df[gateway_df["transaction_id"].isin(both_ids)]

    merged = pd.merge(
        ledger_both, gateway_both,
        on="transaction_id", how="inner",
        suffixes=("_ledger", "_gateway")
    )

    # Amount mismatches
    amt_mismatch_mask = merged["amount_inr_ledger"] != merged["amount_inr_gateway"]
    amount_mismatches = merged.loc[amt_mismatch_mask, [
        "transaction_id", "amount_inr_ledger", "amount_inr_gateway"
    ]].copy()
    amount_mismatches["amount_difference_inr"] = (
        amount_mismatches["amount_inr_gateway"] - amount_mismatches["amount_inr_ledger"]
    )

    # Status mismatches
    status_mismatch_mask = merged["status_ledger"] != merged["status_gateway"]
    status_mismatches = merged.loc[status_mismatch_mask, [
        "transaction_id", "status_ledger", "status_gateway"
    ]].copy()

    return missing_in_gateway, extra_in_gateway, amount_mismatches, status_mismatches


def main():
    ledger = pd.read_csv("ledger.csv")
    gateway = pd.read_csv("gateway_export.csv")

    missing_in_gateway, extra_in_gateway, amount_mismatches, status_mismatches = \
        reconcile_payments(ledger, gateway)

    n = len(ledger)
    lines = []
    lines.append("=" * 80)
    lines.append("RECONCILIATION RESULTS: ledger.csv vs gateway_export.csv")
    lines.append("=" * 80)
    lines.append(f"Ledger row count: {n}")
    lines.append(f"Gateway export row count: {len(gateway)}")
    lines.append("")
    lines.append(f"1. Missing in gateway (present in ledger, absent from gateway): "
                  f"{len(missing_in_gateway)} rows ({len(missing_in_gateway)/n:.1%} of ledger)")
    lines.append(f"2. Extra in gateway (present in gateway, absent from ledger): "
                  f"{len(extra_in_gateway)} rows ({len(extra_in_gateway)/n:.1%} of ledger)")
    lines.append(f"3. Amount mismatches (same transaction_id, different amount_inr): "
                  f"{len(amount_mismatches)} rows ({len(amount_mismatches)/n:.1%} of ledger)")
    lines.append(f"4. Status mismatches (same transaction_id, different status): "
                  f"{len(status_mismatches)} rows ({len(status_mismatches)/n:.1%} of ledger)")
    lines.append("")
    lines.append("Expected injection rates from generate_data.py: ~5% missing, ~3% amount "
                  "mismatch, ~2% extra, ~2% status mismatch (each computed on the 547-row "
                  "ledger). Measured counts above should be close to these rates; minor "
                  "differences can occur where an injected amount-mismatch or status-flip "
                  "landed on a row that was also dropped in the missing-transaction step.")
    lines.append("")
    lines.append("-" * 80)
    lines.append("Sample: missing_in_gateway (first 5)")
    lines.append("-" * 80)
    lines.append(missing_in_gateway.head().to_string(index=False))
    lines.append("")
    lines.append("-" * 80)
    lines.append("Sample: extra_in_gateway (first 5)")
    lines.append("-" * 80)
    lines.append(extra_in_gateway.head().to_string(index=False))
    lines.append("")
    lines.append("-" * 80)
    lines.append("Sample: amount_mismatches (first 5)")
    lines.append("-" * 80)
    lines.append(amount_mismatches.head().to_string(index=False))
    lines.append("")
    lines.append("-" * 80)
    lines.append("Sample: status_mismatches (first 5)")
    lines.append("-" * 80)
    lines.append(status_mismatches.head().to_string(index=False))

    report = "\n".join(lines)
    with open("reconciliation_results.txt", "w") as f:
        f.write(report)

    print(report)


if __name__ == "__main__":
    main()
