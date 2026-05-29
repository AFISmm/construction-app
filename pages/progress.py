"""Progress View — charts, variance table, and export."""
import streamlit as st
from auth import require_auth
from i18n import t
from projects import get_project_summary
from reports import build_variance_df, chart_data, export_csv, export_xlsx

user = require_auth()
project_id = st.session_state.get("current_project_id")
if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

summary = get_project_summary(project_id)
st.title(t("report.title"))

if summary:
    pct = summary.pct_executed / 100
    pct_safe = max(0.0, min(float(pct), 1.0))
    st.subheader(t("report.gauge_title"))
    st.progress(pct_safe)
    st.caption(f"{summary.pct_executed}% — {summary.currency} {summary.total_spent:,.0f} / {summary.total_budgeted:,.0f}")

st.subheader(t("report.chart_title"))
df_chart = chart_data(project_id)
if not df_chart.empty:
    st.bar_chart(df_chart)

st.subheader(t("report.variance"))
currency = summary.currency if summary else ""
df = build_variance_df(project_id, currency)
if df.empty:
    st.info(t("common.no_data"))
else:
    display_df = df.drop(columns=["_over_budget"])

    def _style_row(row):
        styles = [""] * len(row)
        if df.loc[row.name, "_over_budget"]:
            styles = ["background-color: #ffe0e0"] * len(row)
        return styles

    st.dataframe(display_df.style.apply(_style_row, axis=1), use_container_width=True)

col_csv, col_xlsx = st.columns(2)
col_csv.download_button(t("report.export_csv"), export_csv(project_id),
                        file_name="progreso.csv", mime="text/csv")
col_xlsx.download_button(t("report.export_xlsx"), export_xlsx(project_id),
                         file_name="progreso.xlsx",
                         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# --- Room-level breakdown ---
st.divider()
st.subheader(t("room.title"))

from db import Room, get_session
from budget import get_budget_lines
from expenses import get_line_spent
import pandas as pd

with get_session() as session:
    rooms = session.query(Room).filter_by(project_id=project_id).all()
    room_data = [{"id": r.id, "name": r.name} for r in rooms]

if not room_data:
    st.caption(t("room.no_rooms"))
else:
    room_rows = []
    for room in room_data:
        lines = get_budget_lines(project_id, room_id=room["id"])
        budgeted = sum(float(l.budgeted_amount) for l in lines)
        spent = sum(get_line_spent(l.id) for l in lines)
        variance = budgeted - spent
        over = spent > budgeted and budgeted > 0
        room_rows.append({
            t("room.name_label"): room["name"],
            t("report.budgeted_col"): budgeted,
            t("report.actual_col"): spent,
            t("report.variance_col"): variance,
            "_over": over,
        })
    room_df = pd.DataFrame(room_rows)
    display_room_df = room_df.drop(columns=["_over"])

    def _style_room(row):
        return ["background-color: #ffe0e0"] * len(row) if room_df.loc[row.name, "_over"] else [""] * len(row)

    st.dataframe(display_room_df.style.apply(_style_room, axis=1), use_container_width=True)
    if any(r["_over"] for r in room_rows):
        st.warning(t("budget.over_budget_warning"))
