from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterator

import streamlit as st


def inject_theme() -> None:
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,500;0,9..144,600;1,9..144,500&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --navy: #0B1220; --navy-2: #101A2E; --surface: rgba(255,255,255,0.045);
            --line: rgba(255,255,255,0.09); --gold: #D4AF6A; --gold-2: #F1D999;
            --white: #F4F1E9; --ash: #9AA3B5; --green: #35C776; --red: #F0596A;
        }
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp {
            background-color: var(--navy);
            background-image:
                radial-gradient(45% 40% at 85% -5%, rgba(212,175,106,0.16), transparent 65%),
                radial-gradient(40% 35% at 5% 100%, rgba(212,175,106,0.10), transparent 65%),
                repeating-linear-gradient(0deg, rgba(212,175,106,0.035) 0px, transparent 1px, transparent 42px),
                repeating-linear-gradient(90deg, rgba(212,175,106,0.035) 0px, transparent 1px, transparent 42px),
                linear-gradient(155deg, var(--navy) 0%, var(--navy-2) 55%, #0C1526 100%);
            background-attachment: fixed;
        }
        #MainMenu, footer, header[data-testid="stHeader"] { background: transparent; }

        .mono { font-family:'IBM Plex Mono',monospace; }

        /* Hero */
        .hero { padding: 18px 0 8px 0; }
        .hero-eyebrow {
            display:inline-flex; align-items:center; gap:8px;
            font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:0.12em;
            text-transform:uppercase; color: var(--gold); margin-bottom:14px;
        }
        .hero-eyebrow::before {
            content:""; width:7px; height:7px; border-radius:50%; background: var(--gold);
            box-shadow: 0 0 10px 2px rgba(212,175,106,0.7);
        }
        .hero-title {
            font-family:'Fraunces', serif; font-weight:600; font-size:44px; line-height:1.1;
            color: var(--white); margin-bottom:14px; max-width: 640px;
        }
        .hero-title em {
            font-style: italic;
            background: linear-gradient(100deg, var(--gold), var(--gold-2));
            -webkit-background-clip:text; background-clip:text; color:transparent;
        }
        .hero-sub { color: var(--ash); font-size:16px; max-width: 560px; line-height:1.6; margin-bottom: 20px; }

        /* Trust strip */
        .trust-strip { display:flex; gap:28px; flex-wrap:wrap; margin: 22px 0 34px 0; }
        .trust-item { display:flex; flex-direction:column; }
        .trust-num { font-family:'Fraunces',serif; font-weight:600; font-size:24px; color:var(--gold); }
        .trust-label { font-family:'IBM Plex Mono',monospace; font-size:11px; color:var(--ash); text-transform:uppercase; letter-spacing:0.06em; }

        /* Cards */
        .glass-panel {
            background: var(--surface); backdrop-filter: blur(14px);
            border:1px solid var(--line); border-radius:16px;
            padding:24px 24px 18px 24px; margin-bottom:16px;
            animation: rise .5s ease both;
        }
        @keyframes rise { from{opacity:0; transform:translateY(10px);} to{opacity:1; transform:translateY(0);} }
        .glass-panel h3 { font-family:'Fraunces',serif; font-weight:600; font-size:18px; color:var(--white); margin:0 0 6px 0; }
        .glass-panel p.desc { color: var(--ash); font-size:13.5px; line-height:1.55; margin:0; }

        .feature-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:16px; margin: 6px 0 30px 0; }
        .feature-card {
            background: var(--surface); backdrop-filter: blur(14px); border:1px solid var(--line);
            border-radius:16px; padding:22px; transition: transform .2s ease, border-color .2s ease;
        }
        .feature-card:hover { transform: translateY(-4px); border-color: rgba(212,175,106,0.4); }
        .feature-icon {
            width:40px; height:40px; border-radius:11px; display:flex; align-items:center; justify-content:center;
            background: linear-gradient(150deg, rgba(212,175,106,0.28), rgba(212,175,106,0.06));
            font-size:19px; margin-bottom:14px;
        }
        .feature-card h4 { font-family:'Fraunces',serif; font-weight:600; font-size:16px; color:var(--white); margin:0 0 8px 0; }
        .feature-card p { color:var(--ash); font-size:13px; line-height:1.55; margin:0; }

        @media (max-width: 900px) { .feature-grid { grid-template-columns: 1fr; } }

        /* Metric cards (custom, replacing st.metric visuals) */
        .metric-row { display:flex; gap:16px; margin-bottom:18px; }
        .metric-card {
            flex:1; background: var(--surface); backdrop-filter: blur(14px);
            border:1px solid var(--line); border-radius:16px; padding:20px 22px; position:relative; overflow:hidden;
        }
        .metric-card.hero-metric::after {
            content:""; position:absolute; width:180px; height:180px; border-radius:50%;
            top:-70px; right:-60px; background: radial-gradient(circle, rgba(212,175,106,0.35), transparent 70%);
            filter: blur(4px);
        }
        .metric-label { font-family:'IBM Plex Mono',monospace; font-size:11px; letter-spacing:0.08em; text-transform:uppercase; color:var(--ash); margin-bottom:8px; position:relative; }
        .metric-value { font-family:'Fraunces',serif; font-weight:600; font-size:28px; color:var(--white); position:relative; }
        .metric-sub { font-family:'IBM Plex Mono',monospace; font-size:11.5px; color:var(--ash); margin-top:6px; position:relative; }

        /* Buttons */
        div.stButton > button, div.stFormSubmitButton > button {
            background: linear-gradient(120deg, var(--gold), #B8934E);
            color:#1A1200; border:none; border-radius:10px; font-weight:700;
            padding:0.6rem 1.2rem; transition: filter .15s ease, transform .15s ease;
        }
        div.stButton > button:hover, div.stFormSubmitButton > button:hover { filter:brightness(1.1); transform: translateY(-1px); }

        /* Tabs */
        button[data-baseweb="tab"] { font-family:'Inter',sans-serif; font-weight:500; color:var(--ash); }
        button[data-baseweb="tab"][aria-selected="true"] { color: var(--gold) !important; }
        div[data-baseweb="tab-highlight"] { background-color: var(--gold) !important; }
        div[data-baseweb="tab-border"] { background-color: var(--line) !important; }

        /* Inputs */
        div[data-baseweb="input"], div[data-baseweb="select"] > div, textarea {
            background-color: rgba(255,255,255,0.045) !important;
            border-color: var(--line) !important; border-radius:9px !important;
        }

        .version-tag {
            display:inline-flex; align-items:center; gap:6px;
            font-family:'IBM Plex Mono',monospace; font-size:10px; color: var(--ash);
            opacity: 0.55; letter-spacing:0.06em;
        }
        .foot-note { color: var(--ash); font-size:12px; text-align:center; margin-top:14px; opacity:0.6; }
    </style>
    """, unsafe_allow_html=True)


APP_TITLE = "Sixtus Bank"
DB_PATH = Path(__file__).with_name("banking.db")
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
SUPPORTED_CURRENCIES = {
    "USD": {"name": "US Dollar", "symbol": "$", "usd_per_unit": "1"},
    "EUR": {"name": "Euro", "symbol": "€", "usd_per_unit": "1.09"},
    "GBP": {"name": "British Pound", "symbol": "£", "usd_per_unit": "1.28"},
    "CAD": {"name": "Canadian Dollar", "symbol": "C$", "usd_per_unit": "0.73"},
    "AUD": {"name": "Australian Dollar", "symbol": "A$", "usd_per_unit": "0.66"},
    "CHF": {"name": "Swiss Franc", "symbol": "CHF ", "usd_per_unit": "1.12"},
    "JPY": {"name": "Japanese Yen", "symbol": "¥", "usd_per_unit": "0.0067"},
    "NGN": {"name": "Nigerian Naira", "symbol": "₦", "usd_per_unit": "0.00065"},
}
RATE_SOURCE_LABEL = "Indicative demo rates · updated for preview"


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def initialize_database() -> None:
    with get_db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('customer', 'admin')),
                account_number TEXT NOT NULL UNIQUE,
                balance_cents INTEGER NOT NULL DEFAULT 0 CHECK (balance_cents >= 0),
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                transaction_type TEXT NOT NULL CHECK (
                    transaction_type IN ('deposit', 'withdrawal')
                ),
                currency TEXT NOT NULL DEFAULT 'USD',
                amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                balance_after_cents INTEGER NOT NULL CHECK (balance_after_cents >= 0),
                note TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                currency TEXT NOT NULL,
                balance_cents INTEGER NOT NULL DEFAULT 0 CHECK (balance_cents >= 0),
                UNIQUE (user_id, currency)
            );

            CREATE TABLE IF NOT EXISTS exchange_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                from_currency TEXT NOT NULL,
                from_amount_cents INTEGER NOT NULL CHECK (from_amount_cents > 0),
                to_currency TEXT NOT NULL,
                to_amount_cents INTEGER NOT NULL CHECK (to_amount_cents > 0),
                exchange_rate TEXT NOT NULL,
                note TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        transaction_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(transactions)")
        }
        if "currency" not in transaction_columns:
            connection.execute(
                "ALTER TABLE transactions ADD COLUMN currency TEXT NOT NULL DEFAULT 'USD'"
            )
        admin = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (DEFAULT_ADMIN_USERNAME,),
        ).fetchone()
        if admin is None:
            connection.execute(
                """
                INSERT INTO users (
                    username, full_name, password_hash, role, account_number, created_at
                ) VALUES (?, ?, ?, 'admin', ?, ?)
                """,
                (
                    DEFAULT_ADMIN_USERNAME,
                    "Sixtus Bank Administrator",
                    hash_password(DEFAULT_ADMIN_PASSWORD),
                    "ADMIN-000001",
                    now_iso(),
                ),
            )
        for existing_user in connection.execute("SELECT id, balance_cents FROM users"):
            ensure_user_wallets(connection, existing_user["id"], existing_user["balance_cents"])


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"pbkdf2_sha256$120000${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, rounds_text, salt_hex, digest_hex = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            bytes.fromhex(salt_hex),
            int(rounds_text),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def parse_amount(value: str | float | int) -> int:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise ValueError("Enter an amount greater than zero.")
    return int(amount * 100)


def format_money(cents: int, currency: str = "USD") -> str:
    currency_info = SUPPORTED_CURRENCIES.get(currency, SUPPORTED_CURRENCIES["USD"])
    return f"{currency_info['symbol']}{cents / 100:,.2f}"


def currency_label(currency: str) -> str:
    info = SUPPORTED_CURRENCIES[currency]
    return f"{currency} — {info['name']}"


def currency_codes() -> list[str]:
    return list(SUPPORTED_CURRENCIES)


def get_exchange_rate(from_currency: str, to_currency: str) -> Decimal:
    if from_currency not in SUPPORTED_CURRENCIES or to_currency not in SUPPORTED_CURRENCIES:
        raise ValueError("Choose supported currencies.")
    if from_currency == to_currency:
        raise ValueError("Choose two different currencies.")
    source_usd = Decimal(SUPPORTED_CURRENCIES[from_currency]["usd_per_unit"])
    target_usd = Decimal(SUPPORTED_CURRENCIES[to_currency]["usd_per_unit"])
    return (source_usd / target_usd).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def convert_amount(
    amount_cents: int, from_currency: str, to_currency: str
) -> tuple[int, Decimal]:
    rate = get_exchange_rate(from_currency, to_currency)
    converted = (
        (Decimal(amount_cents) / Decimal(100)) * rate
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int(converted * 100), rate


def generate_account_number(connection: sqlite3.Connection) -> str:
    while True:
        candidate = f"HB-{secrets.randbelow(900000) + 100000}"
        exists = connection.execute(
            "SELECT 1 FROM users WHERE account_number = ?", (candidate,)
        ).fetchone()
        if exists is None:
            return candidate


def ensure_user_wallets(
    connection: sqlite3.Connection, user_id: int, usd_balance_cents: int = 0
) -> None:
    for currency in SUPPORTED_CURRENCIES:
        starting_balance = usd_balance_cents if currency == "USD" else 0
        connection.execute(
            """
            INSERT OR IGNORE INTO wallets (user_id, currency, balance_cents)
            VALUES (?, ?, ?)
            """,
            (user_id, currency, starting_balance),
        )


def get_wallets(user_id: int) -> list[sqlite3.Row]:
    with get_db() as connection:
        return connection.execute(
            """
            SELECT currency, balance_cents
            FROM wallets
            WHERE user_id = ?
            ORDER BY CASE currency
                WHEN 'USD' THEN 0 WHEN 'EUR' THEN 1 WHEN 'GBP' THEN 2
                WHEN 'CAD' THEN 3 WHEN 'AUD' THEN 4 WHEN 'CHF' THEN 5
                WHEN 'JPY' THEN 6 WHEN 'NGN' THEN 7 ELSE 8 END
            """,
            (user_id,),
        ).fetchall()


def get_wallet_balance(user_id: int, currency: str) -> int:
    with get_db() as connection:
        wallet = connection.execute(
            "SELECT balance_cents FROM wallets WHERE user_id = ? AND currency = ?",
            (user_id, currency),
        ).fetchone()
    return wallet["balance_cents"] if wallet else 0


def authenticate(username: str, password: str) -> sqlite3.Row | None:
    with get_db() as connection:
        user = connection.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username.strip(),)
        ).fetchone()
    if user and verify_password(password, user["password_hash"]):
        return user
    return None


def create_customer(
    username: str,
    full_name: str,
    password: str,
    initial_deposit: str | float | int,
    initial_currency: str = "USD",
) -> tuple[str, int]:
    if len(username.strip()) < 3:
        raise ValueError("Username must be at least 3 characters.")
    if not username.replace("_", "").replace("-", "").isalnum():
        raise ValueError("Username may contain letters, numbers, underscores, and hyphens.")
    if len(password) < 6:
        raise ValueError("Password must be at least 6 characters.")
    if len(full_name.strip()) < 2:
        raise ValueError("Enter the account holder's full name.")
    if initial_currency not in SUPPORTED_CURRENCIES:
        raise ValueError("Choose a supported opening currency.")

    deposit_cents = 0
    if str(initial_deposit).strip() and Decimal(str(initial_deposit)) > 0:
        deposit_cents = parse_amount(initial_deposit)

    with get_db() as connection:
        account_number = generate_account_number(connection)
        try:
            cursor = connection.execute(
                """
                INSERT INTO users (
                    username, full_name, password_hash, role, account_number,
                    balance_cents, created_at
                ) VALUES (?, ?, ?, 'customer', ?, ?, ?)
                """,
                (
                    username.strip(),
                    full_name.strip(),
                    hash_password(password),
                    account_number,
                    deposit_cents if initial_currency == "USD" else 0,
                    now_iso(),
                ),
            )
        except sqlite3.IntegrityError as error:
            if "username" in str(error).lower():
                raise ValueError("That username is already taken.") from error
            raise ValueError("Could not create the account. Please try again.") from error

        ensure_user_wallets(connection, cursor.lastrowid)
        if deposit_cents:
            connection.execute(
                """
                INSERT INTO transactions (
                    user_id, transaction_type, currency, amount_cents,
                    balance_after_cents, note, created_at
                ) VALUES (?, 'deposit', ?, ?, ?, ?, ?)
                """,
                (
                    cursor.lastrowid,
                    initial_currency,
                    deposit_cents,
                    deposit_cents,
                    "Opening deposit",
                    now_iso(),
                ),
            )
            connection.execute(
                """
                UPDATE wallets
                SET balance_cents = balance_cents + ?
                WHERE user_id = ? AND currency = ?
                """,
                (deposit_cents, cursor.lastrowid, initial_currency),
            )
    return account_number, deposit_cents


def update_balance(
    user_id: int,
    transaction_type: str,
    amount: str | float | int,
    note: str,
    currency: str = "USD",
) -> int:
    amount_cents = parse_amount(amount)
    if transaction_type not in {"deposit", "withdrawal"}:
        raise ValueError("Unsupported transaction.")
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError("Choose a supported currency.")

    with get_db() as connection:
        user = connection.execute(
            "SELECT id, balance_cents FROM users WHERE id = ? AND role = 'customer'",
            (user_id,),
        ).fetchone()
        if user is None:
            raise ValueError("Customer account not found.")

        ensure_user_wallets(connection, user_id, user["balance_cents"])
        wallet = connection.execute(
            "SELECT balance_cents FROM wallets WHERE user_id = ? AND currency = ?",
            (user_id, currency),
        ).fetchone()
        current_balance = wallet["balance_cents"]
        new_balance = (
            current_balance + amount_cents
            if transaction_type == "deposit"
            else current_balance - amount_cents
        )
        if new_balance < 0:
            raise ValueError(
                f"This withdrawal is greater than the available {currency} balance."
            )

        connection.execute(
            """
            UPDATE wallets
            SET balance_cents = ?
            WHERE user_id = ? AND currency = ?
            """,
            (new_balance, user_id, currency),
        )
        if currency == "USD":
            connection.execute(
                "UPDATE users SET balance_cents = ? WHERE id = ?",
                (new_balance, user_id),
            )
        connection.execute(
            """
            INSERT INTO transactions (
                user_id, transaction_type, currency, amount_cents,
                balance_after_cents, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                transaction_type,
                currency,
                amount_cents,
                new_balance,
                note.strip() or None,
                now_iso(),
            ),
        )
    return new_balance


def exchange_currency(
    user_id: int,
    from_currency: str,
    to_currency: str,
    amount: str | float | int,
    note: str,
) -> tuple[int, Decimal]:
    amount_cents = parse_amount(amount)
    converted_cents, rate = convert_amount(amount_cents, from_currency, to_currency)

    with get_db() as connection:
        user = connection.execute(
            "SELECT id, balance_cents FROM users WHERE id = ? AND role = 'customer'",
            (user_id,),
        ).fetchone()
        if user is None:
            raise ValueError("Customer account not found.")

        ensure_user_wallets(connection, user_id, user["balance_cents"])
        source = connection.execute(
            """
            SELECT balance_cents FROM wallets
            WHERE user_id = ? AND currency = ?
            """,
            (user_id, from_currency),
        ).fetchone()
        target = connection.execute(
            """
            SELECT balance_cents FROM wallets
            WHERE user_id = ? AND currency = ?
            """,
            (user_id, to_currency),
        ).fetchone()
        if source is None or target is None:
            raise ValueError("Currency wallet not found.")
        if source["balance_cents"] < amount_cents:
            raise ValueError(f"Not enough {from_currency} to complete this exchange.")

        connection.execute(
            """
            UPDATE wallets SET balance_cents = balance_cents - ?
            WHERE user_id = ? AND currency = ?
            """,
            (amount_cents, user_id, from_currency),
        )
        connection.execute(
            """
            UPDATE wallets SET balance_cents = balance_cents + ?
            WHERE user_id = ? AND currency = ?
            """,
            (converted_cents, user_id, to_currency),
        )
        if from_currency == "USD":
            connection.execute(
                "UPDATE users SET balance_cents = balance_cents - ? WHERE id = ?",
                (amount_cents, user_id),
            )
        if to_currency == "USD":
            connection.execute(
                "UPDATE users SET balance_cents = balance_cents + ? WHERE id = ?",
                (converted_cents, user_id),
            )
        connection.execute(
            """
            INSERT INTO exchange_transactions (
                user_id, from_currency, from_amount_cents, to_currency,
                to_amount_cents, exchange_rate, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                from_currency,
                amount_cents,
                to_currency,
                converted_cents,
                str(rate),
                note.strip() or None,
                now_iso(),
            ),
        )
    return converted_cents, rate


def get_user(user_id: int) -> sqlite3.Row | None:
    with get_db() as connection:
        return connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_transactions(user_id: int, limit: int = 10) -> list[sqlite3.Row]:
    with get_db() as connection:
        return connection.execute(
            """
            SELECT transaction_type, currency, amount_cents, balance_after_cents, note, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()


def get_exchange_transactions(user_id: int, limit: int = 10) -> list[sqlite3.Row]:
    with get_db() as connection:
        return connection.execute(
            """
            SELECT from_currency, from_amount_cents, to_currency,
                   to_amount_cents, exchange_rate, note, created_at
            FROM exchange_transactions
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()


def get_customers() -> list[sqlite3.Row]:
    with get_db() as connection:
        return connection.execute(
            """
            SELECT id, username, full_name, account_number, balance_cents, created_at
            FROM users
            WHERE role = 'customer'
            ORDER BY created_at DESC
            """
        ).fetchall()


def get_customer_by_account(account_number: str) -> sqlite3.Row | None:
    with get_db() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE account_number = ? AND role = 'customer'",
            (account_number.strip().upper(),),
        ).fetchone()


def get_total_deposits() -> int:
    with get_db() as connection:
        row = connection.execute(
            "SELECT COALESCE(SUM(balance_cents), 0) AS total FROM users WHERE role = 'customer'"
        ).fetchone()
        return row["total"]


def get_transaction_count() -> int:
    with get_db() as connection:
        row = connection.execute("SELECT COUNT(*) AS total FROM transactions").fetchone()
        return row["total"]


def get_exchange_count() -> int:
    with get_db() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM exchange_transactions"
        ).fetchone()
        return row["total"]


def get_customer_currency_summary(user_id: int) -> str:
    wallet_summary = []
    for wallet in get_wallets(user_id):
        if wallet["balance_cents"] > 0:
            wallet_summary.append(format_money(wallet["balance_cents"], wallet["currency"]))
    return " · ".join(wallet_summary) if wallet_summary else "No funded wallets"


def initialize_session() -> None:
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("login_error", None)
    st.session_state.setdefault("notice", None)


def show_header() -> None:
    left, right = st.columns([3, 1])
    with left:
        st.markdown(
            f'<div class="hero-eyebrow">{APP_TITLE.upper()} · MULTI-CURRENCY BANKING</div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            '<div style="text-align:right; margin-top:6px;">'
            '<span class="version-tag">● v1.0</span></div>',
            unsafe_allow_html=True,
        )


def show_landing() -> None:
    st.markdown("""
    <div class="hero">
        <div class="hero-title">Banking that moves<br>as fast as <em>you</em> do.</div>
        <div class="hero-sub">
            Hold, move, and exchange money across eight currencies from one account.
            Built for clarity, speed, and security — with every balance backed by
            bank-grade password hashing and a full audit trail of every transaction.
        </div>
    </div>
    <div class="trust-strip">
        <div class="trust-item"><div class="trust-num">8</div><div class="trust-label">Currencies Supported</div></div>
        <div class="trust-item"><div class="trust-num">PBKDF2</div><div class="trust-label">Password Security</div></div>
        <div class="trust-item"><div class="trust-num">100%</div><div class="trust-label">Transaction Traceability</div></div>
        <div class="trust-item"><div class="trust-num">24/7</div><div class="trust-label">Account Access</div></div>
    </div>
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">💱</div>
            <h4>Multi-Currency Wallets</h4>
            <p>Hold USD, EUR, GBP, CAD, AUD, CHF, JPY, and NGN side by side, and move between them in a single transaction.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🔐</div>
            <h4>Security by Design</h4>
            <p>Passwords are never stored in plain text — every account is protected with salted PBKDF2 hashing.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📒</div>
            <h4>Full Transaction Ledger</h4>
            <p>Every deposit, withdrawal, and exchange is logged with a timestamp and running balance — nothing is hidden.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_login() -> None:
    st.markdown(
        '<div class="glass-panel"><h3>Access your account</h3>'
        '<p class="desc">Sign in to manage your money, or open a new customer account to get started.</p></div>',
        unsafe_allow_html=True,
    )

    login_tab, create_tab = st.tabs(["Sign in", "Create account"])
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary", use_container_width=True)
            if submitted:
                user = authenticate(username, password)
                if user is None:
                    st.error("We couldn't sign you in with those details.")
                else:
                    st.session_state.user_id = user["id"]
                    st.session_state.login_error = None
                    st.rerun()

        st.info(
            "Demo administrator: username `admin`, password `admin123`. "
            "Change this before using the app beyond a demo."
        )

    with create_tab:
        with st.form("customer_registration_form", clear_on_submit=True):
            full_name = st.text_input("Full name")
            username = st.text_input("Choose a username")
            password = st.text_input("Create a password", type="password")
            submitted = st.form_submit_button(
                "Create customer account", type="primary", use_container_width=True
            )
            if submitted:
                try:
                    account_number, deposit_cents = create_customer(
                        username,
                        full_name,
                        password,
                        "",
                        "USD",
                    )
                    st.success(
                        f"Account created. Your account number is {account_number}. "
                        f"Sign in and make your first deposit to fund your account."
                    )
                    st.info("Use the username and password you just created to sign in.")
                except (ValueError, InvalidOperation):
                    st.error("Please check the information entered and try again.")


def show_customer_dashboard(user: sqlite3.Row) -> None:
    wallets = get_wallets(user["id"])
    usd_balance = next(
        (wallet["balance_cents"] for wallet in wallets if wallet["currency"] == "USD"), 0
    )
    funded_wallets = [wallet for wallet in wallets if wallet["balance_cents"] > 0]

    st.markdown(
        f'<div class="hero-eyebrow">GOOD TO SEE YOU, {user["full_name"].split()[0].upper()}</div>',
        unsafe_allow_html=True,
    )
    st.caption(f"Currency account · `{user['account_number']}` · {RATE_SOURCE_LABEL}")

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card hero-metric">
            <div class="metric-label">USD wallet</div>
            <div class="metric-value">{format_money(usd_balance, "USD")}</div>
            <div class="metric-sub">primary balance</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Funded wallets</div>
            <div class="metric-value">{len(funded_wallets)}</div>
            <div class="metric-sub">of {len(SUPPORTED_CURRENCIES)} available</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Currencies</div>
            <div class="metric-value">{len(SUPPORTED_CURRENCIES)}</div>
            <div class="metric-sub">supported worldwide</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    exchange_tab, deposit_tab, withdraw_tab, wallets_tab, history_tab = st.tabs(
        ["Exchange currency", "Deposit", "Withdraw", "My wallets", "Activity"]
    )
    with exchange_tab:
        st.write("Convert money between your Sixtus currency wallets.")
        with st.form("currency_exchange_form"):
            from_currency = st.selectbox(
                "From currency", currency_codes(), format_func=currency_label
            )
            to_currency = st.selectbox(
                "To currency", currency_codes(), index=1, format_func=currency_label
            )
            amount = st.text_input("Amount to exchange", placeholder="100.00")
            note = st.text_input(
                "Exchange note (optional)", placeholder="Travel, tuition, supplier payment"
            )
            rate = None
            if from_currency != to_currency:
                rate = get_exchange_rate(from_currency, to_currency)
                st.caption(
                    f"Indicative rate: 1 {from_currency} = {rate} {to_currency}. "
                    f"Rates are for preview and should be replaced with a live provider before production trading."
                )
            submitted = st.form_submit_button(
                "Exchange now", type="primary", use_container_width=True
            )
            if submitted:
                try:
                    converted_cents, applied_rate = exchange_currency(
                        user["id"], from_currency, to_currency, amount, note
                    )
                    st.success(
                        f"Exchange complete: {amount} {from_currency} → "
                        f"{format_money(converted_cents, to_currency)} "
                        f"({applied_rate} rate)."
                    )
                    st.rerun()
                except (ValueError, InvalidOperation) as error:
                    st.error(str(error))

    with deposit_tab:
        st.write("Add money to one of your currency wallets.")
        with st.form("customer_deposit_form"):
            currency = st.selectbox(
                "Deposit currency", currency_codes(), format_func=currency_label
            )
            amount = st.text_input("Deposit amount", placeholder="0.00")
            note = st.text_input("Note (optional)", placeholder="Paycheck, cash deposit, etc.")
            submitted = st.form_submit_button("Make deposit", type="primary")
            if submitted:
                try:
                    new_balance = update_balance(
                        user["id"], "deposit", amount, note, currency
                    )
                    st.success(
                        f"Deposit complete. New balance: {format_money(new_balance, currency)}"
                    )
                    st.rerun()
                except (ValueError, InvalidOperation) as error:
                    st.error(str(error))

    with withdraw_tab:
        st.write("Withdraw money from a currency wallet.")
        with st.form("customer_withdrawal_form"):
            currency = st.selectbox(
                "Withdrawal currency", currency_codes(), format_func=currency_label
            )
            amount = st.text_input("Withdrawal amount", placeholder="0.00")
            note = st.text_input("Note (optional)", placeholder="Travel, supplier payment, etc.")
            submitted = st.form_submit_button("Make withdrawal", type="primary")
            if submitted:
                try:
                    new_balance = update_balance(
                        user["id"], "withdrawal", amount, note, currency
                    )
                    st.success(
                        f"Withdrawal complete. New balance: {format_money(new_balance, currency)}"
                    )
                    st.rerun()
                except (ValueError, InvalidOperation) as error:
                    st.error(str(error))

    with wallets_tab:
        st.write("Your multi-currency wallet balances.")
        for wallet in wallets:
            wallet_col, amount_col = st.columns([3, 1])
            with wallet_col:
                st.write(f"**{currency_label(wallet['currency'])}**")
                st.caption(
                    "Available for exchange" if wallet["balance_cents"] else "No funds yet"
                )
            with amount_col:
                st.metric("Balance", format_money(wallet["balance_cents"], wallet["currency"]))

    with history_tab:
        transactions = get_transactions(user["id"])
        exchanges = get_exchange_transactions(user["id"])
        if not transactions and not exchanges:
            st.info("Your deposits, withdrawals, and exchanges will appear here.")
        else:
            for exchange in exchanges:
                timestamp = exchange["created_at"].replace("T", " ").replace("+00:00", " UTC")
                note = f" — {exchange['note']}" if exchange["note"] else ""
                st.write(
                    f"**Currency exchange** · "
                    f"{format_money(exchange['from_amount_cents'], exchange['from_currency'])} "
                    f"→ {format_money(exchange['to_amount_cents'], exchange['to_currency'])}  \n"
                    f"{timestamp} · Rate: 1 {exchange['from_currency']} = "
                    f"{exchange['exchange_rate']} {exchange['to_currency']}{note}"
                )
                st.divider()
            for transaction in transactions:
                timestamp = transaction["created_at"].replace("T", " ").replace("+00:00", " UTC")
                sign = "+" if transaction["transaction_type"] == "deposit" else "-"
                label = transaction["transaction_type"].title()
                note = f" — {transaction['note']}" if transaction["note"] else ""
                st.write(
                    f"**{label}** · {sign}{format_money(transaction['amount_cents'], transaction['currency'])}  \n"
                    f"{timestamp} · Balance after: "
                    f"{format_money(transaction['balance_after_cents'], transaction['currency'])}{note}"
                )
                st.divider()


def show_admin_dashboard(user: sqlite3.Row) -> None:
    st.subheader("Administrator console")
    st.caption("Create currency accounts, load wallets, and monitor exchange activity.")

    customers = get_customers()
    total_balance = get_total_deposits()
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card hero-metric">
            <div class="metric-label">Customer accounts</div>
            <div class="metric-value">{len(customers)}</div>
            <div class="metric-sub">active customers</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">USD balances</div>
            <div class="metric-value">{format_money(total_balance, "USD")}</div>
            <div class="metric-sub">total across accounts</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Currency exchanges</div>
            <div class="metric-value">{get_exchange_count()}</div>
            <div class="metric-sub">completed exchanges</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    create_tab, load_tab, rates_tab, accounts_tab = st.tabs(
        ["Create customer", "Load money", "Exchange rates", "All accounts"]
    )
    with create_tab:
        with st.form("admin_create_customer_form", clear_on_submit=True):
            full_name = st.text_input("Customer full name")
            username = st.text_input("Customer username")
            password = st.text_input("Temporary password", type="password")
            initial_deposit = st.text_input("Initial load (optional)", value="0.00")
            initial_currency = st.selectbox(
                "Initial load currency",
                currency_codes(),
                format_func=currency_label,
            )
            submitted = st.form_submit_button(
                "Create account", type="primary", use_container_width=True
            )
            if submitted:
                try:
                    account_number, deposit_cents = create_customer(
                        username,
                        full_name,
                        password,
                        initial_deposit,
                        initial_currency,
                    )
                    st.success(
                        f"Created {account_number} for {full_name.strip()}. "
                        f"Starting balance: {format_money(deposit_cents, initial_currency)}."
                    )
                except (ValueError, InvalidOperation) as error:
                    st.error(str(error))

    with load_tab:
        if not customers:
            st.info("Create a customer account before loading money.")
        else:
            with st.form("admin_load_money_form"):
                account_options = {
                    f"{customer['account_number']} — {customer['full_name']}": customer["account_number"]
                    for customer in customers
                }
                selected_label = st.selectbox("Customer account", list(account_options))
                currency = st.selectbox(
                    "Wallet currency", currency_codes(), format_func=currency_label
                )
                amount = st.text_input("Amount to load", placeholder="0.00")
                note = st.text_input("Load note (optional)", value="Admin account load")
                submitted = st.form_submit_button(
                    "Load money", type="primary", use_container_width=True
                )
                if submitted:
                    target = get_customer_by_account(account_options[selected_label])
                    if target is None:
                        st.error("That customer account could not be found.")
                    else:
                        try:
                            new_balance = update_balance(
                                target["id"], "deposit", amount, note, currency
                            )
                            st.success(
                                f"Loaded money into {target['account_number']}. "
                                f"New balance: {format_money(new_balance, currency)}."
                            )
                        except (ValueError, InvalidOperation) as error:
                            st.error(str(error))

    with rates_tab:
        st.write("Reference rates used by the exchange preview.")
        st.caption(
            f"{RATE_SOURCE_LABEL}. Replace these with a regulated live-rate provider "
            "before using this for real-money trading."
        )
        for currency in currency_codes():
            if currency == "USD":
                continue
            rate = get_exchange_rate("USD", currency)
            left_col, right_col = st.columns([2, 1])
            left_col.write(f"**{currency_label(currency)}**")
            right_col.write(f"1 USD = {rate} {currency}")

    with accounts_tab:
        if not customers:
            st.info("No customer accounts have been created yet.")
        else:
            for customer in customers:
                with st.container(border=True):
                    detail_col, balance_col = st.columns([3, 1])
                    with detail_col:
                        st.write(f"**{customer['full_name']}**")
                        st.caption(
                            f"@{customer['username']} · {customer['account_number']} · "
                            f"{get_customer_currency_summary(customer['id'])}"
                        )
                    with balance_col:
                        st.metric("USD balance", format_money(customer["balance_cents"], "USD"))


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🏦", layout="centered")
    inject_theme()
    initialize_database()
    initialize_session()
    show_header()

    if st.session_state.user_id is None:
        show_landing()
        show_login()
        st.markdown(
            '<div class="foot-note">Sixtus Bank — a portfolio demo application. '
            'Not a licensed financial institution.</div>',
            unsafe_allow_html=True,
        )
        return

    user = get_user(st.session_state.user_id)
    if user is None:
        st.session_state.user_id = None
        st.rerun()

    with st.sidebar:
        st.subheader("Your session")
        st.write(f"**{user['full_name']}**")
        st.caption(f"{user['role'].title()} · {user['account_number']}")
        if st.button("Sign out", use_container_width=True):
            st.session_state.user_id = None
            st.rerun()

    if user["role"] == "admin":
        show_admin_dashboard(user)
    else:
        show_customer_dashboard(user)


if __name__ == "__main__":
    main()

