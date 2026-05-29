"""Expenses page — spreadsheet-style view of all budget lines and expenses."""
from datetime import date

import streamlit as st

from auth import require_auth
from budget import get_all_categories, get_budget_lines
from expenses import create_expense, delete_expense, get_expenses, get_line_spent
from i18n import t

user = require_auth()
project_id = st.session_state.get("current_project_id")
if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

st.title(t("expense.title"))

_read_only = st.session_state.get("is_viewer", False)

lines = get_budget_lines(project_id)
if not lines:
    st.info(t("budget.no_lines"))
    st.stop()

# Build category name map
categories = get_all_categories()
cat_names = {c.code: c.name for c in categories}

# Group lines by top-level category
groups: dict[str, list] = {}
for line in lines:
    top = line.category_code.split(".")[0]
    groups.setdefault(top, []).append(line)

# ── Table header ──────────────────────────────────────────────────────────────
h1, h2, h3, h4, h5, h6, h7 = st.columns([3, 1.5, 1.2, 1.2, 1.2, 1.2, 0.8])
h1.markdown(f"**{t('expense.description_label')}**")
h2.markdown(f"**{t('expense.vendor_label')}**")
h3.markdown(f"**{t('budget.amount_label')}**")
h4.markdown(f"**{t('project.total_spent')}**")
h5.markdown(f"**{t('project.balance')}**")
h6.markdown(f"**{t('expense.date_label')}**")
h7.markdown(f"**+**")
st.divider()

grand_budget = 0.0
grand_spent = 0.0

for top_code in sorted(groups.keys()):
    group_lines = groups[top_code]
    cat_label = cat_names.get(top_code, top_code)
    st.markdown(f"**{top_code} — {cat_label}**")

    sub_budget = 0.0
    sub_spent = 0.0

    for line in group_lines:
        spent = get_line_spent(line.id)
        budgeted = float(line.budgeted_amount)
        balance = budgeted - spent
        sub_budget += budgeted
        sub_spent += spent

        # Main row
        c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 1.5, 1.2, 1.2, 1.2, 1.2, 0.8])
        c1.write(line.description or line.category_code)
        c2.write("—")
        c3.write(f"{budgeted:,.0f}")
        color = ":red" if spent > budgeted else ""
        c4.write(f"{color}[{spent:,.0f}]" if color else f"{spent:,.0f}")
        c5.write(f":red[{balance:,.0f}]" if balance < 0 else f"{balance:,.0f}")
        c6.write("—")

        # Add expense button (hidden for viewers)
        add_key = f"_add_{line.id}"
        if not _read_only and c7.button("＋", key=f"btn_{line.id}", help=t("expense.add_expense")):
            st.session_state[add_key] = not st.session_state.get(add_key, False)

        # Inline add expense form
        if st.session_state.get(add_key, False):
            with st.form(f"form_{line.id}"):
                fc1, fc2, fc3, fc4 = st.columns([2, 2, 1.5, 1.5])
                vendor  = fc1.text_input(t("expense.vendor_label"), key=f"v_{line.id}")
                desc    = fc2.text_input(t("expense.description_label"), key=f"d_{line.id}")
                amount  = fc3.number_input(t("expense.amount_label"), min_value=0.01, step=100.0, key=f"a_{line.id}")
                exp_date = fc4.date_input(t("expense.date_label"), value=date.today(), key=f"dt_{line.id}")
                col_s, col_c = st.columns(2)
                if col_s.form_submit_button(t("common.save"), use_container_width=True):
                    create_expense(project_id, line.id, amount, exp_date, vendor, desc)
                    st.session_state[add_key] = False
                    st.success(t("expense.saved"))
                    st.rerun()
                if col_c.form_submit_button(t("common.cancel"), use_container_width=True):
                    st.session_state[add_key] = False
                    st.rerun()

        # Show existing expenses for this line
        exps = get_expenses(project_id, line.id)
        for exp in exps:
            e1, e2, e3, e4, e5, e6, e7 = st.columns([3, 1.5, 1.2, 1.2, 1.2, 1.2, 0.8])
            e1.caption(f"  ↳ {exp.description or '—'}")
            e2.caption(exp.vendor or "—")
            e3.caption("—")
            e4.caption(f"{float(exp.amount):,.0f}")
            e5.caption("—")
            e6.caption(str(exp.expense_date))
            if not _read_only and e7.button("x", key=f"del_{exp.id}", help=t("common.delete")):
                delete_expense(exp.id, project_id)
                st.rerun()

    # Subtotal row
    sub_balance = sub_budget - sub_spent
    st.markdown(
        f"<div style='background:#f0f2f6;padding:4px 8px;border-radius:4px;font-size:0.85em;'>"
        f"<b>Subtotal {top_code}:</b> &nbsp; Presupuesto: <b>{sub_budget:,.0f}</b> &nbsp;|&nbsp; "
        f"Ejecutado: <b>{sub_spent:,.0f}</b> &nbsp;|&nbsp; "
        f"Saldo: <b style='color:{'red' if sub_balance < 0 else 'green'};'>{sub_balance:,.0f}</b>"
        f"</div>", unsafe_allow_html=True
    )
    st.write("")

    grand_budget += sub_budget
    grand_spent += sub_spent

# ── Grand total ───────────────────────────────────────────────────────────────
st.divider()
grand_balance = grand_budget - grand_spent
t1, t2, t3 = st.columns(3)
t1.metric(t("project.total_budget"),  f"{grand_budget:,.0f}")
t2.metric(t("project.total_spent"),   f"{grand_spent:,.0f}")
t3.metric(t("project.balance"),       f"{grand_balance:,.0f}",
          delta=f"{grand_balance:,.0f}",
          delta_color="normal" if grand_balance >= 0 else "inverse")
