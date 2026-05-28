"""App entry point: st.navigation router + persistent sidebar."""
from __future__ import annotations

import streamlit as st

from auth import RateLimitError, get_current_user, logout, send_otp, verify_otp
from db import init_db, seed_categories
from i18n import language_toggle, t
from projects import project_selector_sidebar

st.set_page_config(page_title="Control de Presupuesto", layout="wide", initial_sidebar_state="expanded")


def _bootstrap() -> None:
    if not st.session_state.get("_db_ready"):
        init_db()
        seed_categories()
        st.session_state["_db_ready"] = True


def _sidebar(user: dict) -> None:
    with st.sidebar:
        language_toggle()
        st.divider()
        project_selector_sidebar(user["id"])
        if st.button(t("nav.new_project"), use_container_width=True):
            st.session_state["_edit_project_id"] = None
            st.switch_page("pages/project_form.py")
        st.divider()
        st.page_link("pages/project_list.py", label=t("nav.projects"))
        st.page_link("pages/dashboard.py", label=t("nav.dashboard"))
        st.page_link("pages/budget.py", label=t("nav.budget"))
        st.page_link("pages/expenses.py", label=t("nav.expenses"))
        st.page_link("pages/import_page.py", label=t("nav.import"))
        st.page_link("pages/progress.py", label=t("nav.progress"))
        st.page_link("pages/rooms.py", label=t("nav.rooms"))
        st.page_link("pages/account.py", label=t("nav.account"))
        st.divider()
        st.caption(user["email"])
        if st.button(t("nav.logout"), use_container_width=True):
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
    user = get_current_user()
    if not user:
        _login_page()
        return

    _sidebar(user)

    pages = [
        st.Page("pages/project_list.py", title=t("nav.projects")),
        st.Page("pages/dashboard.py", title=t("nav.dashboard"), default=True),
        st.Page("pages/budget.py", title=t("nav.budget")),
        st.Page("pages/expenses.py", title=t("nav.expenses")),
        st.Page("pages/import_page.py", title=t("nav.import")),
        st.Page("pages/progress.py", title=t("nav.progress")),
        st.Page("pages/rooms.py", title=t("nav.rooms")),
        st.Page("pages/account.py", title=t("nav.account")),
        st.Page("pages/project_form.py", title=t("project.create_title")),
    ]
    pg = st.navigation(pages, position="hidden")
    pg.run()


if __name__ == "__main__":
    main()
