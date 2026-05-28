"""Project Dashboard page."""
import streamlit as st
from auth import require_auth
from i18n import t
from projects import get_project_summary
from reports import chart_data

user = require_auth()
project_id = st.session_state.get("current_project_id")

if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

summary = get_project_summary(project_id)
if not summary:
    st.error(t("error.not_found"))
    st.stop()

st.title(f"{summary.name}  `{t(f'project.type_badge_{summary.project_type}')}`")

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("project.total_budget"), f"{summary.currency} {summary.total_budgeted:,.0f}")
col2.metric(t("project.total_spent"), f"{summary.currency} {summary.total_spent:,.0f}")
col3.metric(t("project.balance"), f"{summary.currency} {summary.balance:,.0f}")
col4.metric(t("project.pct_executed"), f"{summary.pct_executed}%")

st.subheader(t("report.chart_title"))
df = chart_data(project_id)
if not df.empty:
    st.bar_chart(df)
else:
    st.caption(t("common.no_data"))
