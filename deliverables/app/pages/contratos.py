"""Contratos / Contracts — contract management page."""
import streamlit as st
from auth import require_auth
from i18n import t

require_auth()
_lang = st.session_state.get("lang", "en")

title = "Contratos" if _lang == "es" else "Contracts"
st.title(title)

st.info(
    "Módulo de contratos en desarrollo. Aquí podrá registrar y hacer seguimiento a los contratos del proyecto."
    if _lang == "es" else
    "Contracts module coming soon. Here you will be able to register and track project contracts."
)
