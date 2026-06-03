"""Project Dashboard page."""
import altair as alt
import streamlit as st
from auth import require_auth
from i18n import fmt_money, t
from projects import get_project_summary
from reports import chart_data, get_budget_increase_pct

user = require_auth()
project_id = st.session_state.get("current_project_id")

if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

summary = get_project_summary(project_id)
if not summary:
    st.error(t("error.not_found"))
    st.stop()

type_label = t(f"project.type_badge_{summary.project_type}")
st.title(summary.name)
st.markdown(f'<span style="color:#22c55e;font-size:0.78rem;font-weight:500;">{type_label}</span>',
            unsafe_allow_html=True)

increase_pct, increase_label = get_budget_increase_pct(project_id)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(t("project.total_budget"), fmt_money(summary.total_budgeted))
col2.metric(t("project.total_spent"), fmt_money(summary.total_spent))
col3.metric(t("project.balance"), fmt_money(summary.balance))
col4.metric(t("project.pct_executed"), f"{summary.pct_executed}%")
if increase_pct is not None:
    _lang = st.session_state.get("lang", "en")
    lbl = "Aumento presupuestal" if _lang == "es" else "Budget increase"
    col5.metric(lbl, f"{increase_pct:+.1f}%", delta=increase_label, delta_color="inverse")
else:
    _lang = st.session_state.get("lang", "en")
    lbl = "Aumento presupuestal" if _lang == "es" else "Budget increase"
    col5.metric(lbl, "—")

st.subheader(t("report.chart_title"))
df = chart_data(project_id)
if not df.empty and "Tipo" in df.columns:
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Categoria:N", title=t("report.category_col"), axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Valor:Q", title="US$"),
            color=alt.Color(
                "Tipo:N",
                scale=alt.Scale(range=["#4fc3f7", "#e05a20"]),
                legend=alt.Legend(title=""),
            ),
            xOffset="Tipo:N",
            tooltip=["Categoria:N", "Tipo:N", alt.Tooltip("Valor:Q", format=",.0f")],
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.caption(t("common.no_data"))
