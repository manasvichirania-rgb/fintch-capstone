-- SQL queries for the Part 1 fraud checks.

-- ============================================================
-- QUERY 1 — Chargeback impact
-- ============================================================
SELECT
    COUNT(*)                       AS chargeback_txn_count,
    COUNT(DISTINCT user_id)        AS unique_users_affected,
    SUM(amount_inr)                AS total_chargeback_amount_inr
FROM transactions
WHERE status = 'chargeback';


-- ============================================================
-- QUERY 2 — Burner accounts (seeded fraud pattern #1)
-- Users whose signup_date is on/before the transaction and strictly
-- less than 30 days before it, restricted to chargeback transactions.
-- Boundary: 0 <= (transaction_time - signup_date).days < 30
-- ============================================================
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
ORDER BY account_age_days ASC;


-- ============================================================
-- QUERY 3 — Velocity attacks (seeded fraud pattern #2)
-- Users with 3+ transactions inside any 10-minute window. We floor each
-- transaction_time to a 10-minute bucket (epoch seconds // 600) and group
-- by (user_id, bucket); any group with 3+ rows is a qualifying cluster.
-- ============================================================
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
ORDER BY cluster_start ASC;


-- ============================================================
-- QUERY 4 — Top merchants by transaction value
-- ============================================================
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
LIMIT 10;


-- ============================================================
-- QUERY 5 — Merchants with unusually high chargeback counts
-- Demonstrates: GROUP BY, HAVING, ORDER BY
-- ============================================================
SELECT
    merchant_id,
    COUNT(*) AS chargeback_count
FROM transactions
WHERE status = 'chargeback'
GROUP BY merchant_id
HAVING COUNT(*) >= 2
ORDER BY chargeback_count DESC;


-- ============================================================
-- QUERY 6 — High-risk transactions (risk_score >= 80), most recent first
-- Demonstrates: SELECT, WHERE, ORDER BY, LIMIT, DISTINCT payment methods
-- ============================================================
SELECT DISTINCT payment_method
FROM transactions
WHERE risk_score >= 80;

SELECT
    transaction_id, user_id, merchant_id, transaction_time,
    amount_inr, payment_method, status, risk_score
FROM transactions
WHERE risk_score >= 80
ORDER BY transaction_time DESC
LIMIT 15;


-- ============================================================
-- QUERY 7 — Users with multiple distinct transaction statuses
-- (e.g. a user who has both a captured and a chargeback transaction)
-- Demonstrates: GROUP BY, HAVING COUNT(DISTINCT ...), INNER JOIN
-- ============================================================
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
LIMIT 15;


-- ============================================================
-- QUERY 8 — Merchant / category GMV analysis
-- Demonstrates: INNER JOIN, GROUP BY, ORDER BY
-- ============================================================
SELECT
    m.category,
    COUNT(t.transaction_id)  AS transaction_count,
    SUM(t.amount_inr)        AS category_gmv_inr,
    ROUND(AVG(t.amount_inr), 2) AS avg_txn_amount_inr
FROM transactions t
INNER JOIN merchants m ON t.merchant_id = m.merchant_id
GROUP BY m.category
ORDER BY category_gmv_inr DESC;
