"""Tablero / Dashboard — summary metrics only."""
import streamlit as st
from auth import require_auth
from i18n import fmt_money, t
from projects import get_project_summary
from reports import get_budget_increase

user = require_auth()
project_id = st.session_state.get("current_project_id")
_lang = st.session_state.get("lang", "en")

if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

summary = get_project_summary(project_id)
if not summary:
    st.error(t("error.not_found"))
    st.stop()

type_label = t(f"project.type_badge_{summary.project_type}")
st.title(summary.name)
st.markdown(
    f'<span style="color:#22c55e;font-size:0.78rem;font-weight:500;">{type_label}</span>',
    unsafe_allow_html=True,
)

st.divider()

# ── Summary metrics ────────────────────────────────────────────────────────────
increase_pct, increase_money, increase_label = get_budget_increase(project_id)

col1, col2, col3 = st.columns(3)
col1.metric(t("project.total_budget"), fmt_money(summary.total_budgeted))
col2.metric(t("project.total_spent"),  fmt_money(summary.total_spent))
col3.metric(t("project.balance"),      fmt_money(summary.balance))

st.write("")

lbl_increase = "Aumento presupuestal" if _lang == "es" else "Budget increase"
col4, col5 = st.columns(2)

if increase_money is not None:
    col4.metric(f"{lbl_increase} ($)", fmt_money(increase_money))
    col5.metric(f"{lbl_increase} (%)", f"{increase_pct:+.1f}%",
                delta=increase_label, delta_color="inverse")
else:
    col4.metric(f"{lbl_increase} ($)", "—")
    col5.metric(f"{lbl_increase} (%)", "—")
