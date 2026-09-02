"""
run_sql_queries.py

Executes each of the queries defined below (identical in logic to
fraud_queries.sql) against paytm_payments.db and writes the results to
sql_outputs.txt. 

Run:
    python run_sql_queries.py
"""

import sqlite3
import pandas as pd

DB_PATH = "paytm_payments.db"
OUT_PATH = "sql_outputs.txt"

QUERIES = [
    ("QUERY 1 - Chargeback impact", """
        SELECT
            COUNT(*)                       AS chargeback_txn_count,
            COUNT(DISTINCT user_id)        AS unique_users_affected,
            SUM(amount_inr)                AS total_chargeback_amount_inr
        FROM transactions
        WHERE status = 'chargeback'
    """),
    ("QUERY 2 - Burner accounts (0 <= account age days < 30, chargeback only)", """
        SELECT
            t.transaction_id,
            t.user_id,
            u.signup_date,
            t.transaction_time,
            CAST(julianday(t.transaction_time) - julianday(u.signup_date) AS INTEGER) AS account_age_days,
            t.amount_inr,
            t.status
        FROM transactions t
        INNER JOIN users u ON t.user_id = u.user_id
        WHERE t.status = 'chargeback'
            AND julianday(t.transaction_time) - julianday(u.signup_date) >= 0
            AND julianday(t.transaction_time) - julianday(u.signup_date) < 30
        ORDER BY account_age_days ASC
    """),
    ("QUERY 3 - Velocity attacks (3+ txns in any 10-minute bucket)", """
        SELECT
            user_id,
            time_bucket,
            COUNT(*)                            AS txns_in_window,
            MIN(transaction_time)               AS cluster_start,
            GROUP_CONCAT(transaction_id)        AS transaction_ids
        FROM (
            SELECT
                transaction_id,
                user_id,
                transaction_time,
                CAST(strftime('%s', transaction_time) AS INTEGER) / 600 AS time_bucket
            FROM transactions
        ) bucketed
        GROUP BY user_id, time_bucket
        HAVING COUNT(*) >= 3
        ORDER BY cluster_start ASC
    """),
    ("QUERY 4 - Top 10 merchants by GMV (LEFT JOIN)", """
        SELECT
            m.merchant_id,
            m.merchant_name,
            m.category,
            m.region,
            COUNT(t.transaction_id)    AS transaction_count,
            SUM(t.amount_inr)          AS total_gmv_inr
        FROM merchants m
        LEFT JOIN transactions t ON m.merchant_id = t.merchant_id
        GROUP BY m.merchant_id, m.merchant_name, m.category, m.region
        ORDER BY total_gmv_inr DESC
        LIMIT 10
    """),
    ("QUERY 5 - Merchants with unusually high chargeback counts", """
        SELECT
            merchant_id,
            COUNT(*) AS chargeback_count
        FROM transactions
        WHERE status = 'chargeback'
        GROUP BY merchant_id
        HAVING COUNT(*) >= 2
        ORDER BY chargeback_count DESC
    """),
    ("QUERY 6a - DISTINCT payment methods among high-risk (risk_score >= 80) txns", """
        SELECT DISTINCT payment_method
        FROM transactions
        WHERE risk_score >= 80
    """),
    ("QUERY 6b - 15 most recent high-risk transactions (risk_score >= 80)", """
        SELECT
            transaction_id, user_id, merchant_id, transaction_time,
            amount_inr, payment_method, status, risk_score
        FROM transactions
        WHERE risk_score >= 80
        ORDER BY transaction_time DESC
        LIMIT 15
    """),
    ("QUERY 7 - Users with more than one distinct transaction status", """
        SELECT
            t.user_id,
            COUNT(DISTINCT t.status)   AS distinct_statuses,
            GROUP_CONCAT(DISTINCT t.status) AS statuses_seen,
            COUNT(*)                  AS total_txns
        FROM transactions t
        INNER JOIN users u ON t.user_id = u.user_id
        GROUP BY t.user_id
        HAVING COUNT(DISTINCT t.status) > 1
        ORDER BY total_txns DESC
        LIMIT 15
    """),
    ("QUERY 8 - GMV and average ticket size by merchant category", """
        SELECT
            m.category,
            COUNT(t.transaction_id)  AS transaction_count,
            SUM(t.amount_inr)        AS category_gmv_inr,
            ROUND(AVG(t.amount_inr), 2) AS avg_txn_amount_inr
        FROM transactions t
        INNER JOIN merchants m ON t.merchant_id = m.merchant_id
        GROUP BY m.category
        ORDER BY category_gmv_inr DESC
    """),
]


def main():
    conn = sqlite3.connect(DB_PATH)
    out_lines = []

    for label, sql in QUERIES:
        sql = sql.strip()
        out_lines.append("=" * 90)
        out_lines.append(label)
        out_lines.append("=" * 90)
        out_lines.append(f"\nSQL:\n{sql}\n")
        df = pd.read_sql_query(sql, conn)
        out_lines.append(f"Rows returned: {len(df)}")
        out_lines.append(df.to_string(index=False))
        out_lines.append("")

    burner_check = pd.read_sql_query("""
        SELECT t.transaction_id
        FROM transactions t
        INNER JOIN users u ON t.user_id = u.user_id
        WHERE t.status = 'chargeback'
            AND julianday(t.transaction_time) - julianday(u.signup_date) >= 0
            AND julianday(t.transaction_time) - julianday(u.signup_date) < 30
    """, conn)
    seeded_burner = pd.read_sql_query(
        "SELECT transaction_id FROM transactions WHERE transaction_id LIKE 'TXN2%'", conn)

    velocity_check = pd.read_sql_query("""
        SELECT user_id, CAST(strftime('%s', transaction_time) AS INTEGER) / 600 AS bucket, COUNT(*) AS c
        FROM transactions
        GROUP BY user_id, bucket
        HAVING COUNT(*) >= 3
    """, conn)
    seeded_velocity_users = pd.read_sql_query(
        "SELECT DISTINCT user_id FROM transactions WHERE transaction_id LIKE 'TXN3%'", conn)

    out_lines.append("=" * 90)
    out_lines.append("Fraud pattern check")
    out_lines.append("=" * 90)
    out_lines.append(f"Seeded burner rows (TXN2xxxxx) in ledger: {len(seeded_burner)}")
    out_lines.append(f"Burner query (Query 2) rows returned: {len(burner_check)}")
    out_lines.append(f"All 15 seeded burner rows surfaced: "
                      f"{set(seeded_burner['transaction_id']) <= set(burner_check['transaction_id'])}")
    out_lines.append("")
    out_lines.append(f"Seeded velocity clusters (distinct victim users, TXN3xxxxx): {len(seeded_velocity_users)}")
    out_lines.append(f"Velocity query (Query 3) qualifying (user, bucket) groups: {len(velocity_check)}")
    out_lines.append(f"All 8 seeded victim users appear as qualifying groups: "
                      f"{set(seeded_velocity_users['user_id']) <= set(velocity_check['user_id'])}")

    conn.close()

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(out_lines))

    print(f"Wrote {OUT_PATH}")
    print(f"Burner check -> seeded: {len(seeded_burner)}, surfaced: {len(burner_check)}")
    print(f"Velocity check -> seeded clusters: {len(seeded_velocity_users)}, qualifying groups: {len(velocity_check)}")


if __name__ == "__main__":
    main()
