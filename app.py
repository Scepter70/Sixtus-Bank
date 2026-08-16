from __future__ import annotations

import hashlib
import hmac
import secrets
import os
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any, List

import streamlit as st
from sqlalchemy import select, update, insert, func

from db import (
    engine,
    metadata,
    users,
    wallets,
    transactions,
    exchange_transactions,
    get_db as sqlalchemy_get_db,
)


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
DEFAULT_ADMIN_PASSWORD = os.environ.get("SIXTUS_ADMIN_PASSWORD", "admin123")
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


def generate_account_number(connection: Any) -> str:
    while True:
        candidate = f"HB-{secrets.randbelow(900000) + 100000}"
        exists = connection.execute(select(users.c.id).where(users.c.account_number == candidate)).first()
        if exists is None:
            return candidate


def ensure_user_wallets(
    connection: Any, user_id: int, usd_balance_cents: int = 0
) -> None:
    for currency in SUPPORTED_CURRENCIES:
        starting_balance = usd_balance_cents if currency == "USD" else 0
        exists = connection.execute(
            select(wallets.c.id).where((wallets.c.user_id == user_id) & (wallets.c.currency == currency))
        ).first()
        if not exists:
            connection.execute(
                wallets.insert().values(user_id=user_id, currency=currency, balance_cents=starting_balance)
            )


def get_wallets(user_id: int) -> List[Any]:
    with sqlalchemy_get_db() as connection:
        rows = connection.execute(select(wallets).where(wallets.c.user_id == user_id)).fetchall()
    # maintain preferred currency order
    order = ["USD", "EUR", "GBP", "CAD", "AUD", "CHF", "JPY", "NGN"]
    sorted_rows = sorted(rows, key=lambda r: order.index(r.currency) if r.currency in order else len(order))
    return [r._asdict() for r in sorted_rows]


def get_wallet_balance(user_id: int, currency: str) -> int:
    with sqlalchemy_get_db() as connection:
        row = connection.execute(
            select(wallets.c.balance_cents).where((wallets.c.user_id == user_id) & (wallets.c.currency == currency))
        ).first()
    return row.balance_cents if row else 0


def authenticate(username: str, password: str) -> Any | None:
    with sqlalchemy_get_db() as connection:
        user = connection.execute(select(users).where(users.c.username == username.strip())).first()
    if user and verify_password(password, user.password_hash):
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

    with sqlalchemy_get_db() as connection:
        user = connection.execute(select(users.c.id, users.c.balance_cents).where((users.c.id == user_id) & (users.c.role == 'customer'))).first()
        if user is None:
            raise ValueError("Customer account not found.")

        ensure_user_wallets(connection, user_id, user.balance_cents)
        wallet = connection.execute(select(wallets.c.balance_cents).where((wallets.c.user_id == user_id) & (wallets.c.currency == currency))).first()
        current_balance = wallet.balance_cents if wallet else 0
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
            update(wallets).where((wallets.c.user_id == user_id) & (wallets.c.currency == currency)).values(balance_cents=new_balance)
        )
        if currency == "USD":
            connection.execute(
                update(users).where(users.c.id == user_id).values(balance_cents=new_balance)
            )
        connection.execute(
            transactions.insert().values(
                user_id=user_id,
                transaction_type=transaction_type,
                currency=currency,
                amount_cents=amount_cents,
                balance_after_cents=new_balance,
                note=note.strip() or None,
                created_at=now_iso(),
            )
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

    with sqlalchemy_get_db() as connection:
        user = connection.execute(select(users.c.id, users.c.balance_cents).where((users.c.id == user_id) & (users.c.role == 'customer'))).first()
        if user is None:
            raise ValueError("Customer account not found.")

        ensure_user_wallets(connection, user_id, user.balance_cents)
        source = connection.execute(select(wallets.c.balance_cents).where((wallets.c.user_id == user_id) & (wallets.c.currency == from_currency))).first()
        target = connection.execute(select(wallets.c.balance_cents).where((wallets.c.user_id == user_id) & (wallets.c.currency == to_currency))).first()
        if source is None or target is None:
            raise ValueError("Currency wallet not found.")
        if source.balance_cents < amount_cents:
            raise ValueError(f"Not enough {from_currency} to complete this exchange.")

        connection.execute(
            update(wallets).where((wallets.c.user_id == user_id) & (wallets.c.currency == from_currency)).values(balance_cents=source.balance_cents - amount_cents)
        )
        connection.execute(
            update(wallets).where((wallets.c.user_id == user_id) & (wallets.c.currency == to_currency)).values(balance_cents=target.balance_cents + converted_cents)
        )
        if from_currency == "USD":
            connection.execute(
                update(users).where(users.c.id == user_id).values(balance_cents=users.c.balance_cents - amount_cents)
            )
        if to_currency == "USD":
            connection.execute(
                update(users).where(users.c.id == user_id).values(balance_cents=users.c.balance_cents + converted_cents)
            )
        connection.execute(
            exchange_transactions.insert().values(
                user_id=user_id,
                from_currency=from_currency,
                from_amount_cents=amount_cents,
                to_currency=to_currency,
                to_amount_cents=converted_cents,
                exchange_rate=str(rate),
                note=note.strip() or None,
                created_at=now_iso(),
            )
        )
    return converted_cents, rate


def get_user(user_id: int) -> Any | None:
    with sqlalchemy_get_db() as connection:
        return connection.execute(select(users).where(users.c.id == user_id)).first()


def get_transactions(user_id: int, limit: int = 10) -> List[Any]:
    with sqlalchemy_get_db() as connection:
        rows = connection.execute(select(transactions).where(transactions.c.user_id == user_id).order_by(transactions.c.id.desc()).limit(limit)).fetchall()
    return [r._asdict() for r in rows]


def get_exchange_transactions(user_id: int, limit: int = 10) -> List[Any]:
    with sqlalchemy_get_db() as connection:
        rows = connection.execute(select(exchange_transactions).where(exchange_transactions.c.user_id == user_id).order_by(exchange_transactions.c.id.desc()).limit(limit)).fetchall()
    return [r._asdict() for r in rows]


def get_customers() -> List[Any]:
    with sqlalchemy_get_db() as connection:
        rows = connection.execute(select(users).where(users.c.role == 'customer').order_by(users.c.created_at.desc())).fetchall()
    return [r._asdict() for r in rows]


def get_customer_by_account(account_number: str) -> Any | None:
    with sqlalchemy_get_db() as connection:
        return connection.execute(select(users).where((users.c.account_number == account_number.strip().upper()) & (users.c.role == 'customer'))).first()


def get_total_deposits() -> int:
    with sqlalchemy_get_db() as connection:
        rows = connection.execute(select(users.c.balance_cents).where(users.c.role == 'customer')).fetchall()
    return sum(r.balance_cents for r in rows)


def get_transaction_count() -> int:
    with sqlalchemy_get_db() as connection:
        row = connection.execute(select(func.count()).select_from(transactions)).first()
    return int(row[0])


def get_exchange_count() -> int:
    with sqlalchemy_get_db() as connection:
        row = connection.execute(select(func.count()).select_from(exchange_transactions)).first()
    return int(row[0])


def get_customer_currency_summary(user_id: int) -> str:
    wallet_summary: List[str] = []
    for wallet in get_wallets(user_id):
        if wallet['balance_cents'] > 0:
            wallet_summary.append(format_money(wallet['balance_cents'], wallet['currency']))
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
        st.write(f"**{user.full_name}**")
        st.caption(f"{user.role.title()} · {user.account_number}")
        if st.button("Sign out", use_container_width=True):
            st.session_state.user_id = None
            st.rerun()

    if user.role == "admin":
        show_admin_dashboard(user)
    else:
        show_customer_dashboard(user)


if __name__ == "__main__":
    main()
