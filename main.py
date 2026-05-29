"""App entry point: st.navigation router + persistent sidebar."""
from __future__ import annotations

import streamlit as st

from auth import (
    RateLimitError, create_persistent_session, get_current_user,
    invalidate_persistent_session, login_with_password, logout,
    send_otp, set_password, user_has_password, validate_persistent_session,
    verify_otp,
)
from db import init_db, seed_categories
from i18n import language_toggle, set_language, t
from permissions import PAGE_FILES, VIEWER_DEFAULT_PAGES, get_allowed_pages, get_visible_projects, is_admin, is_viewer, save_permission
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
        /* Compact sidebar top */
        [data-testid="stSidebarContent"] { padding-top: 0.5rem !important; }
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
        /* ES/EN buttons — small, consistent everywhere */
        button[data-testid="baseButton-secondary"][kind="secondary"]:has(> p:contains("ES")),
        button[data-testid="baseButton-primary"][kind="primary"]:has(> p:contains("ES")),
        button[data-testid="baseButton-secondary"][kind="secondary"]:has(> p:contains("EN")),
        button[data-testid="baseButton-primary"][kind="primary"]:has(> p:contains("EN")) {
            padding: 2px 8px !important;
            font-size: 0.7rem !important;
            min-height: 0 !important;
            height: 1.6rem !important;
            line-height: 1 !important;
            background-color: #1a1a2e !important;
            color: #8ec5d6 !important;
            border: 1px solid #4fc3f7 !important;
        }
    </style>"""


def _lang_buttons() -> None:
    """Render compact ES / EN buttons at top-right of content area."""
    st.markdown(_HIDE_CHROME, unsafe_allow_html=True)
    current = st.session_state.get("lang", "es")
    _, c1, c2 = st.columns([9, 0.5, 0.5])
    if c1.button("ES", key="_lang_es",
                 type="primary" if current == "es" else "secondary",
                 use_container_width=True):
        set_language("es")
        st.rerun()
    if c2.button("EN", key="_lang_en",
                 type="primary" if current == "en" else "secondary",
                 use_container_width=True):
        set_language("en")
        st.rerun()


def _sidebar(user: dict) -> None:
    allowed = get_allowed_pages(user["id"])
    with st.sidebar:
        # Project selector (read-only display + dropdown to switch)
        project_selector_sidebar(user["id"])
        if not st.session_state.get("is_viewer", False):
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
    # Color palette from diGenius.ai logo
    # Black background | Orange: #e05a20 | Blue accent: #4fc3f7 | White: #fff
    st.markdown("""
        <style>
            [data-testid="stSidebar"]        { display:none!important; }
            [data-testid="collapsedControl"] { display:none!important; }
            header[data-testid="stHeader"]   { display:none!important; }
            #MainMenu                        { display:none!important; }
            .stDeployButton                  { display:none!important; }
            [data-testid="stToolbar"]        { display:none!important; }
            [data-testid="stDecoration"]     { display:none!important; }

            /* Black background on every Streamlit layer */
            html, body, .stApp,
            [data-testid="stAppViewContainer"],
            [data-testid="stMain"],
            [data-testid="stMainBlockContainer"],
            .main, .block-container,
            section[data-testid="stMain"] > div {
                background-color: #000000 !important;
                background: #000000 !important;
            }

            /* Reduce top padding so content sits higher */
            [data-testid="stMainBlockContainer"] {
                padding-top: 0.5rem !important;
            }

            /* White text */
            .stApp, .stApp * { color: #ffffff; }

            /* Input fields */
            input[type="text"], input[type="password"] {
                background-color: #111111 !important;
                color: #ffffff !important;
                border: 1px solid #4fc3f7 !important;
                border-radius: 6px !important;
            }
            label { color: #c8dce8 !important; }

            /* Primary button — orange */
            .stButton > button[kind="primary"],
            .stFormSubmitButton > button {
                background-color: #e05a20 !important;
                color: #ffffff !important;
                border: none !important;
                border-radius: 6px !important;
                font-weight: 600 !important;
            }
            .stButton > button[kind="primary"]:hover,
            .stFormSubmitButton > button:hover {
                background-color: #c84d1a !important;
            }

            /* Tabs */
            .stTabs [data-baseweb="tab-list"] { background-color: #162030 !important; border-radius:6px; }
            .stTabs [data-baseweb="tab"] { color: #8ec5d6 !important; }
            .stTabs [aria-selected="true"] { color: #4fc3f7 !important; border-bottom: 2px solid #4fc3f7 !important; }

            /* Lang buttons */
            .stButton > button { border-radius:4px !important; font-size:0.8rem !important; }
        </style>
    """, unsafe_allow_html=True)

    _lang_buttons()

    # Logo — small, centered, no white border
    from pathlib import Path as _Path
    import base64 as _b64
    logo_path = _Path(__file__).parent / "Logo.jpeg"
    if logo_path.exists():
        logo_b64 = _b64.b64encode(logo_path.read_bytes()).decode()
        st.markdown(f"""
            <div style="display:flex;flex-direction:column;align-items:center;
                        gap:0.3rem;margin-top:0.2rem;margin-bottom:0.5rem;">
                <img src="data:image/jpeg;base64,{logo_b64}"
                     style="width:320px;object-fit:contain;
                            -webkit-mask-image: radial-gradient(ellipse 90% 80% at 50% 50%, black 55%, transparent 100%);
                            mask-image: radial-gradient(ellipse 90% 80% at 50% 50%, black 55%, transparent 100%);
                            filter:brightness(1.1);">
                <p style="color:#ffffff;font-size:1.1rem;font-weight:600;
                          letter-spacing:0.08em;margin:0;text-align:center;
                          text-shadow: 0 0 8px rgba(224,90,32,0.5);">
                    {t("auth.page_title").upper()}
                </p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <p style="text-align:center;color:#ffffff;font-size:1.1rem;
                      font-weight:600;letter-spacing:0.08em;margin:0.5rem 0;">
                {t("auth.page_title").upper()}
            </p>
        """, unsafe_allow_html=True)
    _, form_col, _ = st.columns([1, 2, 1])

    step = st.session_state.get("_auth_step", "login")

    with form_col:
        if step == "set_password":
            # First-time password setup
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
            # Tab selector: Iniciar sesión | Registrarse
            tab_login, tab_register = st.tabs([t("auth.login_button"), t("auth.register_title")])

            with tab_login:
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

            with tab_register:
                with st.form("register_form"):
                    reg_email = st.text_input(t("auth.email_label"), placeholder=t("auth.email_placeholder"),
                                              key="reg_email")
                    reg_pwd1  = st.text_input(t("auth.password_label"), type="password", key="reg_pwd1")
                    reg_pwd2  = st.text_input(t("auth.confirm_password_label"), type="password", key="reg_pwd2")
                    reg_submitted = st.form_submit_button(t("auth.register_button"), use_container_width=True)
                if reg_submitted:
                    if not reg_email or "@" not in reg_email:
                        st.error(t("error.invalid_email"))
                    elif len(reg_pwd1) < 6:
                        st.error(t("auth.password_too_short"))
                    elif reg_pwd1 != reg_pwd2:
                        st.error(t("auth.password_mismatch"))
                    else:
                        from db import User, get_session as _gs
                        uid_new = None
                        email_taken = False
                        with _gs() as _s:
                            existing = _s.query(User).filter_by(email=reg_email.strip().lower()).first()
                            if existing:
                                email_taken = True
                            else:
                                u = User(email=reg_email.strip().lower())
                                _s.add(u)
                                _s.flush()
                                uid_new = u.id
                        # set_password AFTER session commits the user
                        if email_taken:
                            st.error(t("auth.email_already_registered"))
                        elif uid_new:
                            set_password(uid_new, reg_pwd1)
                            # New users are viewers by default
                            save_permission(uid_new, "viewer", VIEWER_DEFAULT_PAGES, None)
                            st.session_state["user_id"] = uid_new
                            st.session_state["user_email"] = reg_email.strip().lower()
                            st.session_state["is_viewer"] = True
                            token = create_persistent_session(uid_new)
                            st.query_params["s"] = token
                            st.rerun()


def main() -> None:
    _bootstrap()
    # Handle language param from URL (don't delete — just apply if changed)
    lang_param = st.query_params.get("lang")
    if lang_param in ("es", "en") and lang_param != st.session_state.get("lang"):
        set_language(lang_param)
        st.rerun()
    _restore_session()
    user = get_current_user()
    if not user:
        _login_page()
        return
    # Cache viewer status in session state
    if "is_viewer" not in st.session_state:
        st.session_state["is_viewer"] = is_viewer(user["id"])

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
    _lang_buttons()
    _sidebar(user)
    pg.run()


main()
