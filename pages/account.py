"""User Management / Account page."""
import streamlit as st
from app.auth import logout, require_auth
from app.i18n import t

user = require_auth()

st.title(t("nav.account"))
st.write(f"**{t('auth.email_label')}:** {user['email']}")

if st.button(t("nav.logout"), type="primary"):
    logout()
