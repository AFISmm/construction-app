"""Project Dashboard page."""
import altair as alt
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

type_label = t(f"project.type_badge_{summary.project_type}")
st.title(summary.name)
st.markdown(f'<span style="color:#22c55e;font-size:0.78rem;font-weight:500;">{type_label}</span>',
            unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric(t("project.total_budget"), f"{summary.currency} {summary.total_budgeted:,.0f}")
col2.metric(t("project.total_spent"), f"{summary.currency} {summary.total_spent:,.0f}")
col3.metric(t("project.balance"), f"{summary.currency} {summary.balance:,.0f}")
col4.metric(t("project.pct_executed"), f"{summary.pct_executed}%")

st.subheader(t("report.chart_title"))
df = chart_data(project_id)
if not df.empty and "Tipo" in df.columns:
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Categoria:N", title=t("report.category_col"), axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Valor:Q", title=summary.currency if summary else ""),
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
