"""OTP authentication: generation, email dispatch, verification, session management."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import streamlit as st

import os

from db import OtpToken, User, UserPassword, UserSession, get_session

MAX_ATTEMPTS = 5
SESSION_TTL_DAYS = 30
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

def send_budget_approval_email(approver_email: str, project_name: str,
                               requester_email: str, version_label: str) -> bool:
    """Send budget approval request email. Returns True if sent, False if SMTP not configured."""
    import smtplib
    import sys
    from email.mime.text import MIMEText
    cfg = st.secrets.get("email", {})
    host     = cfg.get("smtp_host", cfg.get("host", "localhost"))
    port     = int(cfg.get("smtp_port", cfg.get("port", 587)))
    smtp_user = cfg.get("smtp_user", cfg.get("username", ""))
    password = cfg.get("smtp_password", cfg.get("password", ""))
    subject  = f"[Aprobación requerida] Presupuesto {version_label} — {project_name}"
    body = (
        f"Hola,\n\n"
        f"{requester_email} ha enviado el presupuesto {version_label} del proyecto '{project_name}' "
        f"para tu aprobación.\n\n"
        f"Ingresa al portal para revisarlo y aprobarlo o rechazarlo en la pestaña "
        f"'Versiones de Presupuesto'.\n\n"
        f"Este es un mensaje automático."
    )
    if not smtp_user or smtp_user == "PENDIENTE" or not password or password == "PENDIENTE":
        print(f"\n[NOTIF] Aprobación de presupuesto solicitada por {requester_email} → {approver_email}\n",
              file=sys.stderr, flush=True)
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"]    = cfg.get("from_address", smtp_user)
        msg["To"]      = approver_email
        with smtplib.SMTP(host, port) as s:
            s.starttls()
            s.login(smtp_user, password)
            s.send_message(msg)
        return True
    except Exception:
        return False


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
    window_start = datetime.utcnow() - timedelta(minutes=OTP_RATE_WINDOW_MINUTES)  # noqa: DTZ003
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
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES)

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
    now = datetime.utcnow()

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


# ---------------------------------------------------------------------------
# Password authentication
# ---------------------------------------------------------------------------

def validate_password_strength(password: str) -> list[str]:
    """Return list of error messages; empty list means password is valid."""
    import re
    errors = []
    if len(password) < 8:
        errors.append("Mínimo 8 caracteres.")
    if not re.search(r"[A-Z]", password):
        errors.append("Debe contener al menos una letra mayúscula.")
    if not re.search(r"[a-z]", password):
        errors.append("Debe contener al menos una letra minúscula.")
    if not re.search(r"\d", password):
        errors.append("Debe contener al menos un número.")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]", password):
        errors.append("Debe contener al menos un carácter especial (!@#$%...).")
    return errors


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return salt.hex() + ":" + key.hex()


def _verify_password_hash(password: str, stored: str) -> bool:
    try:
        salt_hex, key_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
        return key.hex() == key_hex
    except Exception:
        return False


def set_password(user_id: int, password: str, force_change: bool = False) -> None:
    h = _hash_password(password)
    with get_session() as session:
        existing = session.get(UserPassword, user_id)
        if existing:
            existing.password_hash = h
            existing.must_change = force_change
        else:
            session.add(UserPassword(user_id=user_id, password_hash=h, must_change=force_change))


def must_change_password(user_id: int) -> bool:
    with get_session() as session:
        pwd = session.get(UserPassword, user_id)
        return bool(pwd and pwd.must_change)


def clear_must_change(user_id: int) -> None:
    with get_session() as session:
        pwd = session.get(UserPassword, user_id)
        if pwd:
            pwd.must_change = False


def verify_current_password(user_id: int, password: str) -> bool:
    with get_session() as session:
        pwd = session.get(UserPassword, user_id)
        if not pwd:
            return False
        return _verify_password_hash(password, pwd.password_hash)


def login_with_password(email: str, password: str) -> str:
    """Return 'ok', 'no_password', or 'invalid'."""
    email = email.strip().lower()
    with get_session() as session:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            return "invalid"
        pwd = session.get(UserPassword, user.id)
        if not pwd:
            return "no_password"
        if not _verify_password_hash(password, pwd.password_hash):
            return "invalid"
        st.session_state["user_id"] = user.id
        st.session_state["user_email"] = user.email
        return "ok"


def user_has_password(email: str) -> bool:
    email = email.strip().lower()
    with get_session() as session:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            return False
        return session.get(UserPassword, user.id) is not None


def create_persistent_session(user_id: int) -> str:
    token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(days=SESSION_TTL_DAYS)
    with get_session() as session:
        session.add(UserSession(user_id=user_id, session_token=token, expires_at=expires_at))
    return token


def validate_persistent_session(token: str) -> dict | None:
    with get_session() as session:
        us = session.query(UserSession).filter_by(session_token=token).first()
        if not us or us.expires_at <= datetime.utcnow():
            return None
        user = session.get(User, us.user_id)
        if not user:
            return None
        return {"id": user.id, "email": user.email}


def invalidate_persistent_session(token: str) -> None:
    with get_session() as session:
        us = session.query(UserSession).filter_by(session_token=token).first()
        if us:
            session.delete(us)


def logout() -> None:
    for key in ("user_id", "user_email", "current_project_id", "lang"):
        st.session_state.pop(key, None)
    st.rerun()
