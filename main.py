"""App entry point: st.navigation router + persistent sidebar."""
from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as _components

from auth import (
    RateLimitError, create_persistent_session, get_current_user,
    invalidate_persistent_session, login_with_password, logout,
    send_otp, set_password, user_has_password, validate_persistent_session,
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


_HIDE_CHROME = """
    <style>
        header[data-testid="stHeader"]   { display:none!important; }
        #MainMenu                        { display:none!important; }
        .stDeployButton                  { display:none!important; }
        [data-testid="stToolbar"]        { display:none!important; }
        [data-testid="stDecoration"]     { display:none!important; }
        [data-testid="stStatusWidget"]   { display:none!important; }
        footer                           { display:none!important; }
    </style>"""


def _flag_links() -> None:
    """Inject flag images into the parent DOM via components.html — reliable fixed positioning."""
    current_lang = st.session_state.get("lang", "es")
    token = st.query_params.get("s", "")
    s_param = f"&s={token}" if token else ""
    es_op = "1.0" if current_lang == "es" else "0.3"
    en_op = "1.0" if current_lang == "en" else "0.3"

    # Also hide Streamlit chrome via markdown
    st.markdown(_HIDE_CHROME, unsafe_allow_html=True)

    _components.html(f"""
    <script>
    (function() {{
        var parent = window.parent.document;
        var el = parent.getElementById('lang-flags');
        if (!el) {{
            el = parent.createElement('div');
            el.id = 'lang-flags';
            el.style.cssText = 'position:fixed;top:12px;right:16px;z-index:99999;display:flex;gap:8px;align-items:center;';
            parent.body.appendChild(el);
        }}
        el.innerHTML = `
            <a href="?lang=es{s_param}" target="_parent" style="text-decoration:none;opacity:{es_op};">
                <img src="https://flagcdn.com/w40/es.png" width="30"
                     style="border-radius:3px;display:block;box-shadow:0 1px 3px rgba(0,0,0,.3);">
            </a>
            <a href="?lang=en{s_param}" target="_parent" style="text-decoration:none;opacity:{en_op};">
                <img src="https://flagcdn.com/w40/us.png" width="30"
                     style="border-radius:3px;display:block;box-shadow:0 1px 3px rgba(0,0,0,.3);">
            </a>`;
    }})();
    </script>
    """, height=0, scrolling=False)


def _sidebar(user: dict) -> None:
    allowed = get_allowed_pages(user["id"])
    with st.sidebar:
        # Project selector (read-only display + dropdown to switch)
        project_selector_sidebar(user["id"])
        if st.button(t("nav.new_project"), use_container_width=True):
            st.session_state["_edit_project_id"] = None
            st.switch_page("pages/project_form.py")
        st.divider()
        # Navigation — fixed order for all users
        if "dashboard"  in allowed: st.page_link("pages/dashboard.py",    label=t("nav.dashboard"))
        if "import"     in allowed: st.page_link("pages/import_page.py",  label=t("nav.import"))
        if "projects"   in allowed: st.page_link("pages/project_list.py", label=t("nav.projects"))
        if "progress"   in allowed: st.page_link("pages/progress.py",     label=t("nav.progress"))
        if "expenses"   in allowed: st.page_link("pages/expenses.py",     label=t("nav.expenses"))
        if "rooms"      in allowed: st.page_link("pages/rooms.py",        label=t("nav.rooms"))
        if "account"    in allowed: st.page_link("pages/account.py",      label=t("nav.account"))
        # Admin only
        if "admin"      in allowed: st.page_link("pages/admin.py",        label=t("nav.admin"))
        st.divider()
        if st.button(t("nav.logout"), use_container_width=True):
            token = st.query_params.get("s")
            if token:
                invalidate_persistent_session(token)
                st.query_params.pop("s", None)
            logout()


def _login_page() -> None:
    # Hide sidebar and Streamlit chrome
    st.markdown("""
        <style>
            [data-testid="stSidebar"]       { display:none!important; }
            [data-testid="collapsedControl"]{ display:none!important; }
            header[data-testid="stHeader"]  { display:none!important; }
            #MainMenu                       { display:none!important; }
            .stDeployButton                 { display:none!important; }
            [data-testid="stToolbar"]       { display:none!important; }
            [data-testid="stDecoration"]    { display:none!important; }
        </style>
    """, unsafe_allow_html=True)

    # Handle ?lang= param set by flag links
    lang_param = st.query_params.get("lang")
    if lang_param in ("es", "en"):
        st.session_state["lang"] = lang_param
        st.query_params.pop("lang", None)
        st.rerun()

    current_lang = st.session_state.get("lang", "es")
    es_op = "1.0" if current_lang == "es" else "0.3"
    en_op = "1.0" if current_lang == "en" else "0.3"
    st.markdown(_HIDE_CHROME, unsafe_allow_html=True)
    _components.html(f"""
    <script>
    (function() {{
        var parent = window.parent.document;
        var el = parent.getElementById('lang-flags');
        if (!el) {{
            el = parent.createElement('div');
            el.id = 'lang-flags';
            el.style.cssText = 'position:fixed;top:12px;right:16px;z-index:99999;display:flex;gap:8px;align-items:center;';
            parent.body.appendChild(el);
        }}
        el.innerHTML = `
            <a href="?lang=es" target="_parent" style="text-decoration:none;opacity:{es_op};">
                <img src="https://flagcdn.com/w40/es.png" width="30"
                     style="border-radius:3px;display:block;box-shadow:0 1px 3px rgba(0,0,0,.3);">
            </a>
            <a href="?lang=en" target="_parent" style="text-decoration:none;opacity:{en_op};">
                <img src="https://flagcdn.com/w40/us.png" width="30"
                     style="border-radius:3px;display:block;box-shadow:0 1px 3px rgba(0,0,0,.3);">
            </a>`;
    }})();
    </script>
    """, height=0, scrolling=False)

    st.title(t("auth.page_title"))
    _, form_col, _ = st.columns([1, 2, 1])

    step = st.session_state.get("_auth_step", "login")

    with form_col:
        if step == "register":
            st.subheader(t("auth.register_title"))
            with st.form("register_form"):
                email = st.text_input(t("auth.email_label"), placeholder=t("auth.email_placeholder"))
                pwd1  = st.text_input(t("auth.password_label"), type="password")
                pwd2  = st.text_input(t("auth.confirm_password_label"), type="password")
                submitted = st.form_submit_button(t("auth.register_button"), use_container_width=True)
            if submitted:
                if not email or "@" not in email:
                    st.error(t("error.invalid_email"))
                elif len(pwd1) < 6:
                    st.error(t("auth.password_too_short"))
                elif pwd1 != pwd2:
                    st.error(t("auth.password_mismatch"))
                else:
                    from db import User, get_session as _gs
                    with _gs() as _s:
                        existing = _s.query(User).filter_by(email=email.strip().lower()).first()
                        if existing:
                            st.error(t("auth.email_already_registered"))
                        else:
                            u = User(email=email.strip().lower())
                            _s.add(u)
                            _s.flush()
                            uid = u.id
                            set_password(uid, pwd1)
                            st.session_state["user_id"] = uid
                            st.session_state["user_email"] = email.strip().lower()
                    if "user_id" in st.session_state:
                        token = create_persistent_session(st.session_state["user_id"])
                        st.query_params["s"] = token
                        st.session_state.pop("_auth_step", None)
                        st.rerun()
            if st.button(t("auth.back_to_login"), use_container_width=True):
                st.session_state.pop("_auth_step", None)
                st.rerun()

        elif step == "set_password":
            email = st.session_state.get("_pending_email", "")
            st.info(f"**{email}** — {t('auth.set_password_title')}")
            with st.form("set_pwd_form"):
                pwd1 = st.text_input(t("auth.set_password_label"), type="password")
                pwd2 = st.text_input(t("auth.confirm_password_label"), type="password")
                if st.form_submit_button(t("auth.set_password_button"), use_container_width=True):
                    if len(pwd1) < 6:
                        st.error(t("auth.password_too_short"))
                    elif pwd1 != pwd2:
                        st.error(t("auth.password_mismatch"))
                    else:
                        from db import User, get_session as _gs
                        with _gs() as _s:
                            u = _s.query(User).filter_by(email=email).first()
                            if not u:
                                u = User(email=email)
                                _s.add(u)
                                _s.flush()
                            uid = u.id
                        set_password(uid, pwd1)
                        st.success(t("auth.password_saved"))
                        st.session_state.pop("_auth_step", None)
                        st.session_state.pop("_pending_email", None)
                        st.rerun()

        else:
            # Login form
            with st.form("login_form"):
                email    = st.text_input(t("auth.email_label"), placeholder=t("auth.email_placeholder"))
                password = st.text_input(t("auth.password_label"), type="password",
                                         placeholder=t("auth.password_placeholder"))
                submitted = st.form_submit_button(t("auth.login_button"), use_container_width=True)
            if submitted:
                if not email or "@" not in email:
                    st.error(t("error.invalid_email"))
                elif not password:
                    st.error(t("auth.password_too_short"))
                else:
                    result = login_with_password(email, password)
                    if result == "ok":
                        token = create_persistent_session(st.session_state["user_id"])
                        st.query_params["s"] = token
                        st.rerun()
                    elif result == "no_password":
                        st.session_state["_pending_email"] = email.strip().lower()
                        st.session_state["_auth_step"] = "set_password"
                        st.rerun()
                    else:
                        st.error(t("auth.invalid_credentials"))
            if st.button(t("auth.register_link"), use_container_width=True):
                st.session_state["_auth_step"] = "register"
                st.rerun()


def main() -> None:
    _bootstrap()
    # Handle language param (set by flag links on both login and app pages)
    lang_param = st.query_params.get("lang")
    if lang_param in ("es", "en"):
        from i18n import _cache
        st.session_state["lang"] = lang_param
        _cache.clear()
        st.query_params.pop("lang", None)
        st.rerun()
    _restore_session()
    user = get_current_user()
    if not user:
        _login_page()
        return

    allowed = get_allowed_pages(user["id"])
    page_map = {
        "dashboard": st.Page("pages/dashboard.py",    title=t("nav.dashboard"), default=True),
        "import":    st.Page("pages/import_page.py",  title=t("nav.import")),
        "projects":  st.Page("pages/project_list.py", title=t("nav.projects")),
        "progress":  st.Page("pages/progress.py",     title=t("nav.progress")),
        "expenses":  st.Page("pages/expenses.py",     title=t("nav.expenses")),
        "rooms":     st.Page("pages/rooms.py",        title=t("nav.rooms")),
        "account":   st.Page("pages/account.py",      title=t("nav.account")),
        "budget":    st.Page("pages/budget.py",       title=t("nav.budget")),
        "admin":     st.Page("pages/admin.py",        title=t("nav.admin")),
    }
    pages = [p for k, p in page_map.items() if k in allowed]
    pages.append(st.Page("pages/project_form.py", title=t("project.create_title")))
    pg = st.navigation(pages, position="hidden")
    _flag_links()
    _sidebar(user)
    pg.run()


main()
