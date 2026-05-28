"""Room Detail page — budget and expenses per room."""
import streamlit as st
from app.auth import require_auth
from app.budget import get_budget_lines
from app.db import Room, get_session
from app.expenses import get_expenses, get_line_spent
from app.i18n import t

user = require_auth()
project_id = st.session_state.get("current_project_id")
if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

st.title(t("room.title"))

with get_session() as session:
    rooms = session.query(Room).filter_by(project_id=project_id).all()
    room_data = [{"id": r.id, "name": r.name, "desc": r.description} for r in rooms]

with st.expander(t("room.add_room")):
    with st.form("add_room"):
        name = st.text_input(t("room.name_label") + " *")
        desc = st.text_input(t("room.description_label"))
        if st.form_submit_button(t("common.save")):
            if not name.strip():
                st.error(t("error.required"))
            else:
                with get_session() as s:
                    s.add(Room(project_id=project_id, name=name.strip(), description=desc.strip() or None))
                st.success(t("common.success"))
                st.rerun()

if not room_data:
    st.info(t("room.no_rooms"))
    st.stop()

tab_names = [r["name"] for r in room_data]
tabs = st.tabs(tab_names)

for tab, room in zip(tabs, room_data):
    with tab:
        lines = get_budget_lines(project_id, room_id=room["id"])
        total_bud = sum(float(l.budgeted_amount) for l in lines)
        total_spent = sum(get_line_spent(l.id) for l in lines)
        c1, c2 = st.columns(2)
        c1.metric(t("room.total_budgeted"), f"{total_bud:,.0f}")
        c2.metric(t("room.total_spent"), f"{total_spent:,.0f}")

        st.subheader(t("room.budget_section"))
        if lines:
            for line in lines:
                spent = get_line_spent(line.id)
                st.write(f"**{line.category_code}** — {line.description or ''} | {float(line.budgeted_amount):,.0f} / {spent:,.0f}")
        else:
            st.caption(t("budget.no_lines"))

        st.subheader(t("room.expenses_section"))
        line_ids = [l.id for l in lines]
        all_expenses = []
        for lid in line_ids:
            all_expenses.extend(get_expenses(project_id, lid))
        if all_expenses:
            for exp in sorted(all_expenses, key=lambda e: e.expense_date, reverse=True):
                st.write(f"{exp.expense_date} | {exp.vendor or '—'} | {float(exp.amount):,.0f}")
        else:
            st.caption(t("expense.no_expenses"))
