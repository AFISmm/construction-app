"""Progress View — execution gauge and charts."""
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

_lang = st.session_state.get("lang", "en")
summary = get_project_summary(project_id)
st.title(t("report.title"))

if summary:
    pct = summary.pct_executed / 100
    pct_safe = max(0.0, min(float(pct), 1.0))
    st.subheader(t("report.gauge_title"))
    st.progress(pct_safe)
    st.caption(f"{summary.pct_executed}% — {fmt_money(summary.total_spent)} / {fmt_money(summary.total_budgeted)}")

    increase_pct, increase_label = get_budget_increase_pct(project_id)
    if increase_pct is not None:
        lbl = "Aumento presupuestal" if _lang == "es" else "Budget increase"
        st.metric(lbl, f"{increase_pct:+.1f}%", delta=increase_label, delta_color="inverse")

st.subheader(t("report.chart_title"))
df_chart = chart_data(project_id)
if not df_chart.empty and "Tipo" in df_chart.columns:
    chart = (
        alt.Chart(df_chart)
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
