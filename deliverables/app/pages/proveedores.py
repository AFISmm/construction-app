"""Proveedores — placeholder page."""
import streamlit as st
from auth import require_auth
from i18n import t

user = require_auth()
_lang = st.session_state.get("lang", "en")
st.title("Proveedores" if _lang == "es" else "Vendors")
st.info("Modulo en construccion." if _lang == "es" else "Module under construction.")
