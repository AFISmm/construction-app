"""Expenses page — spreadsheet-style view of all budget lines and expenses."""
from datetime import date

import streamlit as st

from auth import require_auth
from budget import get_all_categories, get_budget_lines
from expenses import create_expense, delete_expense, get_expenses, get_line_spent
from i18n import fmt_money, t

from i18n import _cache as _i18n_cache
_lang = st.session_state.get("lang", "en")
# Ensure cache is fresh for current language
if _lang not in _i18n_cache:
    _i18n_cache.clear()
_lbl_budget   = t("report.budgeted_col")
_lbl_actual   = t("report.actual_col")
_lbl_balance  = t("project.balance")
_lbl_subtotal = "Subtotal"

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

# Build category name map — use translated names
categories = get_all_categories()

def _translated_cat(code: str) -> str:
    key = f"cat.{code}"
    translated = t(key)
    return translated if translated != key else next(
        (c.name for c in categories if c.code == code), code)

cat_names = {c.code: _translated_cat(c.code) for c in categories}

# Group lines by top-level category
groups: dict[str, list] = {}
for line in lines:
    top = line.category_code.split(".")[0]
    groups.setdefault(top, []).append(line)

# ── Table header ──────────────────────────────────────────────────────────────
h1, h2, h3, h4, h5, h6, h7 = st.columns([3, 1.5, 1.2, 1.2, 1.2, 1.2, 0.8])
h1.markdown(f"**{t('expense.description_label')}**")
h2.markdown(f"**{t('expense.vendor_label')}**")
h3.markdown(f"**{_lbl_budget}**")
h4.markdown(f"**{_lbl_actual}**")
h5.markdown(f"**{_lbl_balance}**")
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
        c1.write(_translated_cat(line.category_code))
        c2.write("—")
        c3.write(fmt_money(budgeted))
        color = ":red" if spent > budgeted else ""
        c4.write(f"{color}[{fmt_money(spent)}]" if color else fmt_money(spent))
        c5.write(f":red[{fmt_money(balance)}]" if balance < 0 else fmt_money(balance))
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
            # Use translated category name for the description label
            e1.caption(f"  ↳ {_translated_cat(line.category_code)}")
            e2.caption(exp.vendor or "—")
            e3.caption("—")
            e4.caption(fmt_money(exp.amount))
            e5.caption("—")
            e6.caption(str(exp.expense_date))
            if not _read_only and e7.button("x", key=f"del_{exp.id}", help=t("common.delete")):
                delete_expense(exp.id, project_id)
                st.rerun()

    # Subtotal row
    sub_balance = sub_budget - sub_spent
    st.markdown(
        f"<div style='background:#f0f2f6;padding:4px 8px;border-radius:4px;font-size:0.85em;'>"
        f"<b>{_lbl_subtotal} {top_code}:</b> &nbsp; {_lbl_budget}: <b>{fmt_money(sub_budget)}</b> &nbsp;|&nbsp; "
        f"{_lbl_actual}: <b>{fmt_money(sub_spent)}</b> &nbsp;|&nbsp; "
        f"{_lbl_balance}: <b style='color:{'red' if sub_balance < 0 else 'green'};'>{fmt_money(sub_balance)}</b>"
        f"</div>", unsafe_allow_html=True
    )
    st.write("")

    grand_budget += sub_budget
    grand_spent += sub_spent

# ── Grand total ───────────────────────────────────────────────────────────────
st.divider()
grand_balance = grand_budget - grand_spent
t1, t2, t3 = st.columns(3)
t1.metric(t("project.total_budget"),  fmt_money(grand_budget))
t2.metric(t("project.total_spent"),   fmt_money(grand_spent))
t3.metric(t("project.balance"),       fmt_money(grand_balance),
          delta=fmt_money(grand_balance),
          delta_color="normal" if grand_balance >= 0 else "inverse")

# ── File attachment — import expenses from CSV/Excel ──────────────────────────
if not _read_only:
    st.divider()
    attach_label = "📎 Import expenses from file" if _lang == "en" else "📎 Importar gastos desde archivo"
    with st.expander(attach_label):
        st.caption(
            "Upload a CSV or Excel file with columns: Description, Vendor, Amount, Date, CategoryCode"
            if _lang == "en" else
            "Sube un CSV o Excel con columnas: Descripcion, Proveedor, Monto, Fecha, CodigoCategoria"
        )
        uploaded = st.file_uploader(
            "File / Archivo", type=["csv", "xlsx", "xls"], key="_exp_upload"
        )
        if uploaded:
            import io, pandas as pd
            try:
                if uploaded.name.endswith(".csv"):
                    df_up = pd.read_csv(io.BytesIO(uploaded.read()))
                else:
                    df_up = pd.read_excel(io.BytesIO(uploaded.read()))

                # Normalize column names
                df_up.columns = [c.strip().lower().replace(" ", "_") for c in df_up.columns]
                col_map = {
                    "description":    ["description", "descripcion", "descripción", "item", "concepto"],
                    "vendor":         ["vendor", "proveedor", "supplier"],
                    "amount":         ["amount", "monto", "valor", "precio"],
                    "date":           ["date", "fecha"],
                    "category_code":  ["category_code", "categorycode", "codigo", "código", "code", "cat"],
                }
                found = {}
                for key, options in col_map.items():
                    for opt in options:
                        if opt in df_up.columns:
                            found[key] = opt
                            break

                st.write(f"{'Detected columns' if _lang == 'en' else 'Columnas detectadas'}: {list(df_up.columns)}")

                if "amount" not in found:
                    st.error("Amount column not found." if _lang == "en" else "No se encontró columna de monto.")
                else:
                    # Preview
                    st.dataframe(df_up.head(5), use_container_width=True)

                    # Build budget line lookup
                    bl_map = {bl.category_code: bl.id for bl in lines}

                    if st.button("Import expenses" if _lang == "en" else "Importar gastos", key="_exp_import_btn"):
                        imported = 0
                        errors = []
                        for _, row in df_up.iterrows():
                            try:
                                amt = float(str(row[found["amount"]]).replace(",", "").replace("$", ""))
                                if amt <= 0:
                                    continue
                                desc    = str(row.get(found.get("description", ""), "")).strip() or "—"
                                vendor  = str(row.get(found.get("vendor", ""), "")).strip() or ""
                                cat_code = str(row.get(found.get("category_code", ""), "")).strip()
                                raw_date = row.get(found.get("date", ""), None)
                                try:
                                    exp_date = pd.to_datetime(raw_date).date() if raw_date else date.today()
                                except Exception:
                                    exp_date = date.today()

                                # Find matching budget line
                                line_id = bl_map.get(cat_code)
                                if not line_id:
                                    # Try parent code
                                    parent = cat_code.split(".")[0] if "." in cat_code else None
                                    if parent:
                                        line_id = bl_map.get(parent)
                                if not line_id:
                                    errors.append(f"No budget line for code: {cat_code}")
                                    continue

                                create_expense(project_id, line_id, amt, exp_date, vendor, desc)
                                imported += 1
                            except Exception as ex:
                                errors.append(str(ex))

                        if imported:
                            st.success(f"{'Imported' if _lang == 'en' else 'Importados'}: {imported} {'expenses' if _lang == 'en' else 'gastos'}")
                            st.rerun()
                        if errors:
                            with st.expander(f"{'Warnings' if _lang == 'en' else 'Advertencias'} ({len(errors)})"):
                                for e in errors[:10]:
                                    st.caption(e)
            except Exception as ex:
                st.error(f"Error reading file: {ex}")
