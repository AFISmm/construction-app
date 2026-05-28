"""Expense Entry page."""
from datetime import date

import streamlit as st
from app.auth import require_auth
from app.expenses import create_expense, delete_expense, get_budget_lines_for_project, get_expenses, get_line_spent
from app.i18n import t

user = require_auth()
project_id = st.session_state.get("current_project_id")
if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

st.title(t("expense.title"))

lines = get_budget_lines_for_project(project_id)
if not lines:
    st.info(t("budget.no_lines"))
    st.stop()

line_options = {f"{l.category_code} — {l.description or ''}": l.id for l in lines}
selected_label = st.selectbox(t("expense.budget_line_label"), list(line_options.keys()))
selected_line_id = line_options[selected_label]
selected_line = next(l for l in lines if l.id == selected_line_id)

col_bud, col_spent = st.columns(2)
col_bud.metric(t("budget.amount_label"), f"{float(selected_line.budgeted_amount):,.0f}")
col_spent.metric(t("project.total_spent"), f"{get_line_spent(selected_line_id):,.0f}")

with st.expander(t("expense.add_expense")):
    with st.form("add_expense"):
        vendor = st.text_input(t("expense.vendor_label"))
        desc = st.text_input(t("expense.description_label"))
        amount = st.number_input(t("expense.amount_label") + " *", min_value=0.01, step=1000.0)
        exp_date = st.date_input(t("expense.date_label"), value=date.today())
        notes = st.text_area(t("expense.notes_label"))
        if st.form_submit_button(t("common.save")):
            create_expense(project_id, selected_line_id, amount, exp_date, vendor, desc, notes)
            st.success(t("expense.saved"))
            st.rerun()

expenses = get_expenses(project_id, selected_line_id)
if not expenses:
    st.info(t("expense.no_expenses"))
else:
    for exp in expenses:
        c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 1, 0.5])
        c1.write(exp.vendor or "—")
        c2.write(exp.description or "—")
        c3.write(f"{float(exp.amount):,.0f}")
        c4.write(str(exp.expense_date))
        if c5.button("x", key=f"del_exp_{exp.id}"):
            delete_expense(exp.id, project_id)
            st.rerun()
