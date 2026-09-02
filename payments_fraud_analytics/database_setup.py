"""
database_setup.py

Builds the SQLite database used by the Part 1 SQL queries.

Schema:
    merchants(merchant_id PK, merchant_name, category, region)
    users(user_id PK, signup_date)
    transactions(transaction_id PK, user_id FK -> users, merchant_id FK -> merchants,
                  transaction_time, amount_inr, payment_method, status, risk_score)

Run:
    python database_setup.py
"""

import sqlite3
import pandas as pd
import os

DB_PATH = "paytm_payments.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS merchants;

CREATE TABLE merchants (
    merchant_id     INTEGER PRIMARY KEY,
    merchant_name   TEXT NOT NULL,
    category        TEXT NOT NULL,
    region          TEXT NOT NULL
);

CREATE TABLE users (
    user_id         INTEGER PRIMARY KEY,
    signup_date     TEXT NOT NULL
);

CREATE TABLE transactions (
    transaction_id  TEXT PRIMARY KEY,
    user_id         INTEGER NOT NULL,
    merchant_id     INTEGER NOT NULL,
    transaction_time TEXT NOT NULL,
    amount_inr      INTEGER NOT NULL,
    payment_method  TEXT NOT NULL,
    status          TEXT NOT NULL,
    risk_score      INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (merchant_id) REFERENCES merchants(merchant_id)
);
"""


def build_database():
    # Start with a clean database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    merchants = pd.read_csv("merchants.csv")
    users = pd.read_csv("users.csv")
    ledger = pd.read_csv("ledger.csv")

    merchants.to_sql("merchants", conn, if_exists="append", index=False)
    users.to_sql("users", conn, if_exists="append", index=False)
    ledger.to_sql("transactions", conn, if_exists="append", index=False)

    conn.commit()

    cur = conn.cursor()
    counts = {}
    for t in ("merchants", "users", "transactions"):
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        counts[t] = cur.fetchone()[0]
    conn.close()
    return counts


if __name__ == "__main__":
    counts = build_database()
    print(f"paytm_payments.db built at: {os.path.abspath(DB_PATH)}")
    for table, n in counts.items():
        print(f"  {table}: {n} rows")
