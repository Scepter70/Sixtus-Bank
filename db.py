from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import (
    CheckConstraint,
    Column,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    UniqueConstraint,
    text,
)

# Database file (used for sqlite fallback)
DB_PATH = Path(__file__).with_name("banking.db")

DATABASE_URL = os.environ.get("DATABASE_URL") or f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()

# Table definitions (compatible with Postgres and SQLite via SQLAlchemy)
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String, nullable=False, unique=True),
    Column("full_name", String, nullable=False),
    Column("password_hash", String, nullable=False),
    Column("role", String, nullable=False),
    Column("account_number", String, nullable=False, unique=True),
    Column("balance_cents", Integer, nullable=False, default=0),
    Column("created_at", String, nullable=False),
    CheckConstraint("role IN ('customer','admin')", name="ck_users_role"),
)

transactions = Table(
    "transactions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("transaction_type", String, nullable=False),
    Column("currency", String, nullable=False, server_default="USD"),
    Column("amount_cents", Integer, nullable=False),
    Column("balance_after_cents", Integer, nullable=False),
    Column("note", Text),
    Column("created_at", String, nullable=False),
    CheckConstraint("transaction_type IN ('deposit','withdrawal')", name="ck_transactions_type"),
)

wallets = Table(
    "wallets",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("currency", String, nullable=False),
    Column("balance_cents", Integer, nullable=False, default=0),
    UniqueConstraint("user_id", "currency", name="uq_wallets_user_currency"),
)

exchange_transactions = Table(
    "exchange_transactions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, nullable=False),
    Column("from_currency", String, nullable=False),
    Column("from_amount_cents", Integer, nullable=False),
    Column("to_currency", String, nullable=False),
    Column("to_amount_cents", Integer, nullable=False),
    Column("exchange_rate", String, nullable=False),
    Column("note", Text),
    Column("created_at", String, nullable=False),
)


@contextmanager
def get_db():
    """Yield a SQLAlchemy Connection inside a transaction. The calling code
    can use connection.execute(text(sql), params) and fetch results. The
    transaction will be committed automatically when the context exits.
    """
    with engine.begin() as conn:
        # For SQLite, ensure foreign keys are enabled.
        if engine.url.get_backend_name() == "sqlite":
            conn.execute(text("PRAGMA foreign_keys = ON"))
        yield conn
