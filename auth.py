"""OTP authentication: generation, email dispatch, verification, session management."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import streamlit as st

from db import OtpToken, User, get_session

MAX_ATTEMPTS = 5
OTP_TTL_MINUTES = 10
MAX_OTP_REQUESTS = 3        # max OTP sends per window per email
OTP_RATE_WINDOW_MINUTES = 15


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def _hash_token(token: str) -> str:
    secret = st.secrets.get("app", {}).get("secret_key", "dev-secret")
    return hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def _generate_raw_token() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


# ---------------------------------------------------------------------------
# Email dispatch
# ---------------------------------------------------------------------------

def _send_email(to_email: str, token: str) -> None:
    cfg = st.secrets.get("email", {})
    provider = cfg.get("provider", "smtp")

    if provider == "sendgrid":
        import urllib.request, json as _json
        payload = _json.dumps({
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": cfg["from_address"]},
            "subject": "Codigo de acceso",
            "content": [{"type": "text/plain", "value": f"Tu codigo: {token}. Valido 10 minutos."}],
        }).encode()
        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send",
            data=payload,
            headers={"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req)
    else:
        import smtplib
        import sys
        from email.mime.text import MIMEText
        host = cfg.get("smtp_host", cfg.get("host", "localhost"))
        port = int(cfg.get("smtp_port", cfg.get("port", 587)))
        user = cfg.get("smtp_user", cfg.get("username", ""))
        password = cfg.get("smtp_password", cfg.get("password", ""))
        if not user or user == "PENDIENTE" or not password or password == "PENDIENTE":
            print(f"\n[DEV MODE] OTP para {to_email}: {token}\n", file=sys.stderr, flush=True)
            return
        msg = MIMEText(f"Tu codigo de acceso: {token}\nValido por {OTP_TTL_MINUTES} minutos.")
        msg["Subject"] = "Codigo de acceso"
        msg["From"] = cfg.get("from_address", "noreply@localhost")
        msg["To"] = to_email
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(user, password)
            s.send_message(msg)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class RateLimitError(Exception):
    pass


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def _is_rate_limited(session, user_id: int) -> bool:
    window_start = datetime.now(timezone.utc) - timedelta(minutes=OTP_RATE_WINDOW_MINUTES)
    recent = (
        session.query(OtpToken)
        .filter(OtpToken.user_id == user_id, OtpToken.created_at >= window_start)
        .count()
    )
    return recent >= MAX_OTP_REQUESTS


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_otp(email: str) -> None:
    email = email.strip().lower()
    token = _generate_raw_token()
    token_hash = _hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)

    with get_session() as session:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            user = User(email=email)
            session.add(user)
            session.flush()

        if user.id and _is_rate_limited(session, user.id):
            raise RateLimitError()

        session.query(OtpToken).filter_by(user_id=user.id, used=False).update({"used": True})
        session.add(OtpToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at))

    _send_email(email, token)


def verify_otp(email: str, token: str) -> str:
    """Return 'ok', 'expired', or 'invalid'."""
    email = email.strip().lower()
    token_hash = _hash_token(token.strip())
    now = datetime.now(timezone.utc)

    with get_session() as session:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            return "invalid"

        # Check if a token exists but is expired (no TTL filter)
        latest = (
            session.query(OtpToken)
            .filter_by(user_id=user.id, used=False)
            .order_by(OtpToken.created_at.desc())
            .first()
        )
        if not latest:
            return "invalid"
        if latest.expires_at <= now:
            return "expired"
        if latest.attempt_count >= MAX_ATTEMPTS:
            return "invalid"

        latest.attempt_count += 1
        if latest.token_hash == token_hash:
            latest.used = True
            session.commit()
            st.session_state["user_id"] = user.id
            st.session_state["user_email"] = user.email
            return "ok"

        session.commit()
        return "invalid"


def get_current_user() -> dict | None:
    if "user_id" not in st.session_state:
        return None
    return {"id": st.session_state["user_id"], "email": st.session_state["user_email"]}


def require_auth() -> dict:
    user = get_current_user()
    if not user:
        st.stop()
    return user


def logout() -> None:
    for key in ("user_id", "user_email", "current_project_id", "lang"):
        st.session_state.pop(key, None)
    st.rerun()
