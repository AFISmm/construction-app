"""App entry point: st.navigation router + persistent sidebar."""
from __future__ import annotations

import streamlit as st

from auth import (
    RateLimitError, create_persistent_session, get_current_user,
    invalidate_persistent_session, logout, send_otp, validate_persistent_session,
    verify_otp,
)
from db import init_db, seed_categories
from i18n import language_toggle, t
from permissions import PAGE_FILES, get_allowed_pages, get_visible_projects, is_admin
from projects import project_selector_sidebar

st.set_page_config(page_title="Control de Presupuesto", layout="wide", initial_sidebar_state="expanded")


def _restore_session() -> None:
    if "user_id" in st.session_state:
        return
    token = st.query_params.get("s")
    if not token:
        return
    user = validate_persistent_session(token)
    if user:
        st.session_state["user_id"] = user["id"]
        st.session_state["user_email"] = user["email"]
    else:
        st.query_params.pop("s", None)


def _bootstrap() -> None:
    if not st.session_state.get("_db_ready"):
        import re
        raw_url = st.secrets.get("database", {}).get("url", "NOT SET")
        masked = re.sub(r":([^:@]+)@", ":***@", str(raw_url))
        try:
            init_db()
            seed_categories()
            st.session_state["_db_ready"] = True
        except Exception as e:
            st.error(f"**DB URL usado:** `{masked}`\n\n**Error:** {e}")
            st.stop()


def _sidebar(user: dict) -> None:
    allowed = get_allowed_pages(user["id"])
    with st.sidebar:
        language_toggle()
        st.divider()
        project_selector_sidebar(user["id"])
        if st.button(t("nav.new_project"), use_container_width=True):
            st.session_state["_edit_project_id"] = None
            st.switch_page("pages/project_form.py")
        st.divider()
        if "projects"   in allowed: st.page_link("pages/project_list.py", label=t("nav.projects"))
        if "dashboard"  in allowed: st.page_link("pages/dashboard.py",    label=t("nav.dashboard"))
        if "budget"     in allowed: st.page_link("pages/budget.py",       label=t("nav.budget"))
        if "expenses"   in allowed: st.page_link("pages/expenses.py",     label=t("nav.expenses"))
        if "import"     in allowed: st.page_link("pages/import_page.py",  label=t("nav.import"))
        if "progress"   in allowed: st.page_link("pages/progress.py",     label=t("nav.progress"))
        if "rooms"      in allowed: st.page_link("pages/rooms.py",        label=t("nav.rooms"))
        if "account"    in allowed: st.page_link("pages/account.py",      label=t("nav.account"))
        if "admin"      in allowed: st.page_link("pages/admin.py",        label="⚙ Administración")
        st.divider()
        if st.button(t("nav.logout"), use_container_width=True):
            token = st.query_params.get("s")
            if token:
                invalidate_persistent_session(token)
                st.query_params.pop("s", None)
            logout()


def _login_page() -> None:
    st.title(t("auth.page_title"))
    step = st.session_state.get("_auth_step", "email")

    if step == "email":
        with st.form("login_form"):
            email = st.text_input(t("auth.email_label"), placeholder=t("auth.email_placeholder"))
            submitted = st.form_submit_button(t("auth.send_otp_button"))
        if submitted:
            if not email or "@" not in email:
                st.error(t("error.invalid_email"))
            else:
                try:
                    send_otp(email)
                    st.session_state["_pending_email"] = email
                    st.session_state["_auth_step"] = "otp"
                    st.rerun()
                except RateLimitError:
                    st.error(t("auth.otp_rate_limited"))
                except Exception:
                    st.error(t("error.server"))

    elif step == "otp":
        email = st.session_state.get("_pending_email", "")
        st.info(t("auth.otp_sent", email=email))
        with st.form("otp_form"):
            code = st.text_input(t("auth.otp_label"), placeholder=t("auth.otp_placeholder"), max_chars=6)
            submitted = st.form_submit_button(t("auth.verify_button"))
        if submitted:
            result = verify_otp(email, code)
            if result == "ok":
                st.session_state.pop("_auth_step", None)
                st.session_state.pop("_pending_email", None)
                token = create_persistent_session(st.session_state["user_id"])
                st.query_params["s"] = token
                st.rerun()
            elif result == "expired":
                st.error(t("auth.otp_expired"))
            else:
                st.error(t("auth.otp_invalid", n=1))
        if st.button(t("auth.resend_link")):
            try:
                send_otp(email)
                st.info(t("auth.otp_sent", email=email))
            except RateLimitError:
                st.error(t("auth.otp_rate_limited"))
            except Exception:
                st.error(t("error.server"))


def main() -> None:
    _bootstrap()
    _restore_session()
    user = get_current_user()
    if not user:
        _login_page()
        return

    allowed = get_allowed_pages(user["id"])
    page_map = {
        "projects":  st.Page("pages/project_list.py", title=t("nav.projects")),
        "dashboard": st.Page("pages/dashboard.py",    title=t("nav.dashboard"), default=True),
        "budget":    st.Page("pages/budget.py",       title=t("nav.budget")),
        "expenses":  st.Page("pages/expenses.py",     title=t("nav.expenses")),
        "import":    st.Page("pages/import_page.py",  title=t("nav.import")),
        "progress":  st.Page("pages/progress.py",     title=t("nav.progress")),
        "rooms":     st.Page("pages/rooms.py",        title=t("nav.rooms")),
        "account":   st.Page("pages/account.py",      title=t("nav.account")),
        "admin":     st.Page("pages/admin.py",        title="Administración"),
    }
    pages = [p for k, p in page_map.items() if k in allowed]
    pages.append(st.Page("pages/project_form.py", title=t("project.create_title")))
    pg = st.navigation(pages, position="hidden")
    _sidebar(user)
    pg.run()


main()
