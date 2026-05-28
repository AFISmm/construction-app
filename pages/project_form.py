"""Project Create / Edit page."""
import streamlit as st
from app.auth import require_auth
from app.i18n import t
from app.projects import create_project, get_project, update_project

user = require_auth()
edit_id = st.session_state.get("_edit_project_id")
project = get_project(edit_id, user["id"]) if edit_id else None

st.title(t("project.edit_title") if project else t("project.create_title"))

with st.form("project_form"):
    name = st.text_input(t("project.name_label") + " *",
                         value=project.name if project else "",
                         placeholder=t("project.name_placeholder"))
    type_options = [t("project.type_residential"), t("project.type_commercial")]
    type_values = ["residential", "commercial"]
    current_type_idx = type_values.index(project.project_type) if project else 0
    selected_type_label = st.radio(t("project.type_label") + " *", type_options, index=current_type_idx, horizontal=True)
    selected_type = type_values[type_options.index(selected_type_label)]
    description = st.text_area(t("project.description_label"), value=project.description or "" if project else "")
    currency = st.selectbox(t("common.currency"), ["COP", "USD", "EUR"],
                            index=["COP", "USD", "EUR"].index(project.currency) if project else 0)

    col_save, col_cancel = st.columns(2)
    submitted = col_save.form_submit_button(t("common.save"))
    cancelled = col_cancel.form_submit_button(t("common.cancel"))

if submitted:
    if not name.strip():
        st.error(t("error.required"))
    elif project:
        update_project(edit_id, user["id"], name, selected_type, description, currency)
        st.success(t("common.success"))
        st.switch_page("pages/dashboard.py")
    else:
        new_project = create_project(user["id"], name, selected_type, description, currency)
        st.session_state["current_project_id"] = new_project.id
        st.switch_page("pages/dashboard.py")

if cancelled:
    st.switch_page("pages/dashboard.py")
