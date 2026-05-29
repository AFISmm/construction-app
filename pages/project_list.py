"""Project List page — overview of all user projects."""
import streamlit as st

from auth import require_auth
from i18n import t
from projects import get_project_summary, get_user_projects

user = require_auth()

st.title(t("project.list_title"))

projects = get_user_projects(user["id"])
if not projects:
    st.info(t("project.no_projects"))
    if st.button(t("nav.new_project")):
        st.session_state["_edit_project_id"] = None
        st.switch_page("pages/project_form.py")
    st.stop()

current_project_id = st.session_state.get("current_project_id")

for p in projects:
    summary = get_project_summary(p.id)
    is_active = p.id == current_project_id
    badge = " ✓" if is_active else ""
    type_label = t(f"project.type_badge_{p.project_type}")

    with st.container(border=True):
        col_name, col_budget, col_pct, col_actions = st.columns([3, 2, 1.5, 2])

        col_name.markdown(f"**{p.name}**{badge}")
        col_name.caption(type_label)

        if summary:
            col_budget.metric(t("project.total_budget"), f"{summary.total_budgeted:,.0f}")
            col_pct.metric(t("project.pct_executed"), f"{summary.pct_executed:.1f}%")
        else:
            col_budget.caption("—")
            col_pct.caption("—")

        with col_actions:
            if not is_active:
                if st.button(t("common.select"), key=f"sel_{p.id}", use_container_width=True):
                    st.session_state["current_project_id"] = p.id
                    st.rerun()
            if st.button(t("common.edit"), key=f"edit_{p.id}", use_container_width=True):
                st.session_state["_edit_project_id"] = p.id
                st.switch_page("pages/project_form.py")
