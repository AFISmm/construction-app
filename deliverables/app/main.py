"""App entry point: st.navigation router + persistent sidebar."""
from __future__ import annotations

import streamlit as st

from auth import (
    RateLimitError, clear_must_change, create_persistent_session, get_current_user,
    invalidate_persistent_session, login_with_password, logout, must_change_password,
    send_otp, set_password, user_has_password, validate_password_strength,
    validate_persistent_session, verify_otp,
)
from db import init_db, seed_categories
from i18n import language_toggle, set_language, t
from permissions import (PAGE_FILES, VIEWER_DEFAULT_PAGES, get_allowed_pages,
                         get_pending_count, get_visible_projects,
                         is_admin, is_pending, is_pending_extended, is_viewer, save_permission)
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


_HIDE_CHROME = """<style>
    header[data-testid="stHeader"]   { display:none!important; }
    #MainMenu                        { display:none!important; }
    .stDeployButton                  { display:none!important; }
    [data-testid="stToolbar"]        { display:none!important; }
    [data-testid="stDecoration"]     { display:none!important; }
    [data-testid="stStatusWidget"]   { display:none!important; }
    footer                           { display:none!important; }
    [data-testid="stSidebarContent"] { padding-top:0.3rem!important; }
    section[data-testid="stSidebar"] > div { padding-top:0!important; }
    [data-testid="stSidebarContent"] hr { margin:0.3rem 0!important; }
    /* Project selector: dropdown only, no keyboard typing */
    [data-testid="stSidebarContent"] [data-baseweb="select"] input {
        pointer-events:none!important; caret-color:transparent!important; }
    [data-testid="stSidebarContent"] [data-baseweb="select"] [role="combobox"] {
        cursor:pointer!important; }
    /* Smooth fade-in on every render to hide flash transitions */
    .stApp { animation: _pg_fadein 0.25s ease-in !important; }
    @keyframes _pg_fadein { from { opacity:0; } to { opacity:1; } }
</style>"""


def _lang_buttons() -> None:
    """Render ES / EN buttons fixed top-right."""
    current = st.session_state.get("lang", "en")
    st.markdown(_HIDE_CHROME, unsafe_allow_html=True)
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
        st.divider()
        # Navigation — fixed order for all users
        if "dashboard"    in allowed: st.page_link("pages/dashboard.py",    label=t("nav.dashboard"))
        if "expenses"     in allowed: st.page_link("pages/expenses.py",     label=t("nav.expenses"))
        if "presupuesto"  in allowed: st.page_link("pages/presupuesto.py",  label=t("nav.presupuesto"))
        if "trazabilidad" in allowed: st.page_link("pages/trazabilidad.py", label=t("nav.trazabilidad"))
        if "timeline"     in allowed: st.page_link("pages/timeline.py",     label=t("nav.timeline"))
        if "proveedores"  in allowed: st.page_link("pages/proveedores.py",  label=t("nav.proveedores"))
        if "account"      in allowed: st.page_link("pages/account.py",      label=t("nav.account"))
        if "admin" in allowed:
            pending = get_pending_count()
            admin_label = f"🔔 {t('nav.admin')} ({pending})" if pending > 0 else t("nav.admin")
            st.page_link("pages/admin.py", label=admin_label)
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

            /* Tabs — smaller, no red indicator line */
            .stTabs [data-baseweb="tab-list"] {
                background-color: #111111 !important;
                border-radius: 6px !important;
                gap: 0 !important;
                border-bottom: 1px solid #2a2a2a !important;
            }
            .stTabs [data-baseweb="tab"] {
                color: #8ec5d6 !important;
                font-size: 0.8rem !important;
                padding: 6px 14px !important;
                background: transparent !important;
            }
            .stTabs [aria-selected="true"] {
                color: #4fc3f7 !important;
                background-color: #1a2a3a !important;
                border-bottom: 2px solid #4fc3f7 !important;
            }
            /* Hide the animated red/orange sliding indicator */
            .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
            .stTabs [data-baseweb="tab-border"]    { display: none !important; }

            /* Lang buttons */
            .stButton > button { border-radius: 4px !important; font-size: 0.75rem !important; }
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
                        gap:0.3rem;margin-top:0.2rem;margin-bottom:0.5rem;
                        background:#000000;">
                <img src="data:image/jpeg;base64,{logo_b64}"
                     style="width:380px;object-fit:contain;
                            mix-blend-mode:screen;
                            filter:brightness(1.3) contrast(2.5) saturate(1.1);">
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
    _, form_col, _ = st.columns([2, 2, 2])

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
                    _pwd_errors = validate_password_strength(reg_pwd1)
                    if not reg_email or "@" not in reg_email:
                        st.error(t("error.invalid_email"))
                    elif _pwd_errors:
                        for _e in _pwd_errors:
                            st.error(_e)
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
                            save_permission(uid_new, "pending", [], None)
                            _lang = st.session_state.get("lang", "en")
                            st.success("✅ Registration successful. Your account is pending administrator approval."
                                       if _lang == "en" else
                                       "✅ Registro exitoso. Tu cuenta está pendiente de aprobación del administrador.")
                            st.info("You will receive access once the administrator approves your request."
                                    if _lang == "en" else
                                    "Recibirás acceso una vez que el administrador apruebe tu solicitud.")


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
    # Forzar cambio de contraseña en primer login
    if must_change_password(user["id"]):
        st.markdown(_HIDE_CHROME, unsafe_allow_html=True)
        _lang = st.session_state.get("lang", "en")
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.subheader("🔐 Crea tu contraseña" if _lang == "es" else "🔐 Create your password")
            st.info("El administrador creó tu cuenta. Debes establecer una nueva contraseña para continuar."
                    if _lang == "es" else
                    "The administrator created your account. You must set a new password to continue.")
            with st.form("force_pwd_form"):
                np1 = st.text_input("Nueva contraseña" if _lang == "es" else "New password", type="password")
                np2 = st.text_input("Confirmar contraseña" if _lang == "es" else "Confirm password", type="password")
                if st.form_submit_button("Guardar y continuar" if _lang == "es" else "Save and continue",
                                         use_container_width=True, type="primary"):
                    errs = validate_password_strength(np1)
                    if np1 != np2:
                        errs.append("Las contraseñas no coinciden." if _lang == "es" else "Passwords do not match.")
                    if errs:
                        for e in errs:
                            st.error(e)
                    else:
                        set_password(user["id"], np1, force_change=False)
                        clear_must_change(user["id"])
                        st.success("✅ Contraseña guardada." if _lang == "es" else "✅ Password saved.")
                        st.rerun()
            st.caption("Requisitos: 8+ caracteres, mayúscula, minúscula, número y carácter especial."
                       if _lang == "es" else
                       "Requirements: 8+ characters, uppercase, lowercase, number and special character.")
            if st.button(t("nav.logout"), key="_force_logout"):
                logout()
        st.stop()

    # Usuarios con registro extendido pendiente de completar
    if is_pending_extended(user["id"]):
        # Include extended_registration in allowed pages so it can render
        _ext_pages = [st.Page("pages/extended_registration.py", title="Registration", default=True)]
        _ext_nav = st.navigation(_ext_pages, position="hidden")
        _lang_buttons()
        _ext_nav.run()
        return

    # Block pending users
    if is_pending(user["id"]):
        st.markdown(_HIDE_CHROME, unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        _lang = st.session_state.get("lang", "en")
        _, col, _ = st.columns([1, 2, 1])
        with col:
            st.warning("⏳ Your account is pending approval." if _lang == "en"
                       else "⏳ Tu cuenta está pendiente de aprobación.")
            st.markdown("The administrator will review your request and grant access soon." if _lang == "en"
                        else "El administrador revisará tu solicitud y te dará acceso pronto.")
            if st.button(t("nav.logout")):
                logout()
        st.stop()

    # Cache viewer status in session state
    if "is_viewer" not in st.session_state:
        st.session_state["is_viewer"] = is_viewer(user["id"])

    allowed = get_allowed_pages(user["id"])
    page_map = {
        "dashboard":     st.Page("pages/dashboard.py",     title=t("nav.dashboard"),     default=True),
        "expenses":      st.Page("pages/expenses.py",      title=t("nav.expenses")),
        "presupuesto":   st.Page("pages/presupuesto.py",   title=t("nav.presupuesto")),
        "trazabilidad":  st.Page("pages/trazabilidad.py",  title=t("nav.trazabilidad")),
        "timeline":      st.Page("pages/timeline.py",      title=t("nav.timeline")),
        "proveedores":   st.Page("pages/proveedores.py",   title=t("nav.proveedores")),
        "account":       st.Page("pages/account.py",       title=t("nav.account")),
        "admin":         st.Page("pages/admin.py",         title=t("nav.admin")),
    }
    pages = [p for k, p in page_map.items() if k in allowed]
    pg = st.navigation(pages, position="hidden")
    _lang_buttons()
    _sidebar(user)
    pg.run()


main()
