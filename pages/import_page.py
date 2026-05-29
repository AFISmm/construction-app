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

# ── Import mode selector ──────────────────────────────────────────────────────
current_mode = st.session_state.get("_import_mode", None)

if current_mode is None:
    st.markdown(t("import.choose_mode"))
    col_new, col_merge = st.columns(2)
    if col_new.button(t("import.mode_new"), use_container_width=True, type="primary"):
        st.session_state["_import_mode"] = "new"
        st.rerun()
    if col_merge.button(t("import.mode_merge"), use_container_width=True):
        st.session_state["_import_mode"] = "merge"
        st.rerun()
    st.stop()

# Show active mode + allow changing
mode_label = t("import.mode_new") if current_mode == "new" else t("import.mode_merge")
col_info, col_change = st.columns([4, 1])
col_info.info(f"**Modo:** {mode_label}")
if col_change.button(t("common.cancel")):
    st.session_state.pop("_import_mode", None)
    st.session_state.pop("_import_step", None)
    st.session_state.pop("_import_job_id", None)
    st.rerun()

from importer.review import run_import_page
run_import_page(project_id)
