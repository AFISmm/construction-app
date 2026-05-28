"""File Import page — delegates to Isabela's import module."""
import streamlit as st
from auth import require_auth
from i18n import t

require_auth()
project_id = st.session_state.get("current_project_id")
if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

st.title(t("import.title"))

try:
    from import_.review import run_import_page
    run_import_page(project_id)
except ImportError:
    st.info("Import pipeline not yet available. Run instruction 009 to install Isabela's module.")
