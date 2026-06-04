"""User Management / Account page."""
import streamlit as st
from auth import (clear_must_change, logout, require_auth, set_password,
                  validate_password_strength, verify_current_password)
from i18n import t

user = require_auth()
_lang = st.session_state.get("lang", "en")

st.title(t("nav.account"))
st.write(f"**{t('auth.email_label')}:** {user['email']}")
st.divider()

# ── Cambiar contraseña ────────────────────────────────────────────────────────
pwd_title = "Cambiar contraseña" if _lang == "es" else "Change password"
st.subheader(pwd_title)

with st.form("change_pwd_form"):
    current_pwd = st.text_input(
        "Contraseña actual" if _lang == "es" else "Current password",
        type="password",
    )
    new_pwd = st.text_input(
        "Nueva contraseña" if _lang == "es" else "New password",
        type="password",
    )
    confirm_pwd = st.text_input(
        "Confirmar nueva contraseña" if _lang == "es" else "Confirm new password",
        type="password",
    )
    save_btn = st.form_submit_button(
        "💾 Guardar contraseña" if _lang == "es" else "💾 Save password",
        use_container_width=True,
        type="primary",
    )

if save_btn:
    errors = []
    if not verify_current_password(user["id"], current_pwd):
        errors.append("Contraseña actual incorrecta." if _lang == "es" else "Current password is incorrect.")
    if new_pwd != confirm_pwd:
        errors.append("Las contraseñas no coinciden." if _lang == "es" else "Passwords do not match.")
    strength_errors = validate_password_strength(new_pwd)
    errors.extend(strength_errors)

    if errors:
        for err in errors:
            st.error(err)
    else:
        set_password(user["id"], new_pwd, force_change=False)
        clear_must_change(user["id"])
        st.success("✅ Contraseña actualizada." if _lang == "es" else "✅ Password updated.")

st.divider()

# ── Requisitos de contraseña ──────────────────────────────────────────────────
req_title = "Requisitos de contraseña" if _lang == "es" else "Password requirements"
with st.expander(f"ℹ️ {req_title}"):
    if _lang == "es":
        st.markdown("""
- Mínimo **8 caracteres**
- Al menos una **letra mayúscula** (A-Z)
- Al menos una **letra minúscula** (a-z)
- Al menos un **número** (0-9)
- Al menos un **carácter especial** (!@#$%^&*...)
        """)
    else:
        st.markdown("""
- Minimum **8 characters**
- At least one **uppercase letter** (A-Z)
- At least one **lowercase letter** (a-z)
- At least one **number** (0-9)
- At least one **special character** (!@#$%^&*...)
        """)

st.divider()
if st.button(t("nav.logout"), type="primary"):
    logout()
