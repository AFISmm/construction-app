"""Gastos / Expenses — same columns as budget table plus vendor."""
from datetime import date

import streamlit as st

from auth import require_auth
from budget import get_all_categories, get_budget_lines
from expenses import create_expense, delete_expense, get_expenses, get_line_spent
from i18n import fmt_money, t

_lang = st.session_state.get("lang", "en")

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

categories = get_all_categories()


def _translated_cat(code: str) -> str:
    key = f"cat.{code}"
    translated = t(key)
    return translated if translated != key else next(
        (c.name for c in categories if c.code == code), code)


cat_names = {c.code: _translated_cat(c.code) for c in categories}

groups: dict[str, list] = {}
for line in lines:
    top = line.category_code.split(".")[0]
    groups.setdefault(top, []).append(line)

# ── Column labels ─────────────────────────────────────────────────────────────
_lbl_desc       = t("expense.description_label")
_lbl_vendor     = t("expense.vendor_label")
_lbl_budget     = "Presupuesto" if _lang == "es" else "Budget"
_lbl_co         = "Change Order"
_lbl_contracted = "Valor contratado" if _lang == "es" else "Contracted value"
_lbl_total      = "Total presupuesto" if _lang == "es" else "Total budget"
_lbl_balance    = "Balance Due"

# ── Table header ──────────────────────────────────────────────────────────────
h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([2.5, 1.5, 1.2, 1.2, 1.2, 1.2, 1.2, 0.8])
h1.markdown(f"**{_lbl_desc}**")
h2.markdown(f"**{_lbl_vendor}**")
h3.markdown(f"**{_lbl_budget}**")
h4.markdown(f"**{_lbl_co}**")
h5.markdown(f"**{_lbl_contracted}**")
h6.markdown(f"**{_lbl_total}**")
h7.markdown(f"**{_lbl_balance}**")
h8.markdown("**+**")
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
        change_order = float(getattr(line, "change_order_amount", 0) or 0)
        contracted = float(getattr(line, "contracted_amount", 0) or 0)
        total_budget = budgeted + change_order
        balance_due = total_budget - spent

        sub_budget += budgeted
        sub_spent += spent

        # Budget line row
        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2.5, 1.5, 1.2, 1.2, 1.2, 1.2, 1.2, 0.8])
        c1.write(_translated_cat(line.category_code))
        c2.write("—")
        c3.write(fmt_money(budgeted))
        c4.write(fmt_money(change_order))
        c5.write(fmt_money(contracted))
        c6.write(fmt_money(total_budget))
        c7.write(f":red[{fmt_money(balance_due)}]" if balance_due < 0 else fmt_money(balance_due))

        add_key = f"_add_{line.id}"
        if not _read_only and c8.button("＋", key=f"btn_{line.id}", help=t("expense.add_expense")):
            st.session_state[add_key] = not st.session_state.get(add_key, False)

        # Inline add expense form
        if st.session_state.get(add_key, False):
            with st.form(f"form_{line.id}"):
                fc1, fc2, fc3, fc4 = st.columns([2, 2, 1.5, 1.5])
                vendor   = fc1.text_input(t("expense.vendor_label"), key=f"v_{line.id}")
                desc     = fc2.text_input(t("expense.description_label"), key=f"d_{line.id}")
                amount   = fc3.number_input(t("expense.amount_label"), min_value=0.01, step=100.0,
                                            key=f"a_{line.id}")
                exp_date = fc4.date_input(t("expense.date_label"), value=date.today(),
                                          key=f"dt_{line.id}")
                col_s, col_c = st.columns(2)
                if col_s.form_submit_button(t("common.save"), use_container_width=True):
                    create_expense(project_id, line.id, amount, exp_date, vendor, desc)
                    st.session_state[add_key] = False
                    st.success(t("expense.saved"))
                    st.rerun()
                if col_c.form_submit_button(t("common.cancel"), use_container_width=True):
                    st.session_state[add_key] = False
                    st.rerun()

        # Existing expense sub-rows
        exps = get_expenses(project_id, line.id)
        for exp in exps:
            e1, e2, e3, e4, e5, e6, e7, e8 = st.columns([2.5, 1.5, 1.2, 1.2, 1.2, 1.2, 1.2, 0.8])
            e1.caption(f"  ↳ {exp.description or _translated_cat(line.category_code)}")
            e2.caption(exp.vendor or "—")
            e3.caption("—")
            e4.caption("—")
            e5.caption(fmt_money(exp.amount))
            e6.caption("—")
            e7.caption(str(exp.expense_date))
            if not _read_only and e8.button("x", key=f"del_{exp.id}", help=t("common.delete")):
                delete_expense(exp.id, project_id)
                st.rerun()

    # Subtotal
    sub_total   = sum(float(l.budgeted_amount) + float(getattr(l, "change_order_amount", 0) or 0)
                      for l in group_lines)
    sub_balance = sub_total - sub_spent
    st.markdown(
        f"<div style='background:#f0f2f6;padding:4px 8px;border-radius:4px;font-size:0.85em;'>"
        f"<b>Subtotal {top_code}:</b> &nbsp; {_lbl_budget}: <b>{fmt_money(sub_budget)}</b>"
        f" &nbsp;|&nbsp; Total: <b>{fmt_money(sub_total)}</b>"
        f" &nbsp;|&nbsp; Balance Due: "
        f"<b style='color:{'red' if sub_balance < 0 else 'green'};'>{fmt_money(sub_balance)}</b>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    grand_budget += sub_budget
    grand_spent += sub_spent

# ── Grand total ───────────────────────────────────────────────────────────────
st.divider()
grand_total = sum(
    float(l.budgeted_amount) + float(getattr(l, "change_order_amount", 0) or 0)
    for l in lines
)
grand_balance = grand_total - grand_spent
t1, t2, t3 = st.columns(3)
t1.metric(t("project.total_budget"),  fmt_money(grand_budget))
t2.metric(t("project.total_spent"),   fmt_money(grand_spent))
t3.metric("Balance Due",              fmt_money(grand_balance),
          delta=fmt_money(grand_balance),
          delta_color="normal" if grand_balance >= 0 else "inverse")

# ── Export / Import bar ───────────────────────────────────────────────────────
if not _read_only:
    st.divider()
    import io as _io
    import pandas as _pd

    all_exps = []
    for line in lines:
        for exp in get_expenses(project_id, line.id):
            all_exps.append({
                "Categoria" if _lang == "es" else "Category":
                    _translated_cat(line.category_code),
                "Proveedor" if _lang == "es" else "Vendor":
                    exp.vendor or "—",
                "Descripcion" if _lang == "es" else "Description":
                    exp.description or "—",
                "Monto" if _lang == "es" else "Amount":
                    float(exp.amount),
                "Fecha" if _lang == "es" else "Date":
                    str(exp.expense_date),
            })
    df_exp = _pd.DataFrame(all_exps) if all_exps else _pd.DataFrame()

    bc1, bc2, bc3, _sp, bc4 = st.columns([1, 1, 1, 2, 1.2])

    if not df_exp.empty:
        bc1.download_button(
            "📥 CSV", df_exp.to_csv(index=False).encode("utf-8-sig"),
            file_name="gastos.csv", mime="text/csv", use_container_width=True,
        )
        _buf_xl = _io.BytesIO()
        with _pd.ExcelWriter(_buf_xl, engine="openpyxl") as _wr:
            df_exp.to_excel(_wr, index=False, sheet_name="Gastos")
        bc2.download_button(
            "📥 Excel", _buf_xl.getvalue(),
            file_name="gastos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        try:
            from reports import export_pdf as _epdf
            from projects import get_project_summary as _gps
            _summ = _gps(project_id)
            _pdf = _epdf(project_id, _summ.name if _summ else "Gastos",
                         _summ.currency if _summ else "")
            bc3.download_button(
                "📥 PDF", _pdf, file_name="gastos.pdf",
                mime="application/pdf", use_container_width=True,
            )
        except Exception:
            bc3.caption("—")
    else:
        bc1.caption(t("expense.no_expenses"))

    _import_key = "_show_import_expenses"
    if bc4.button("📤 " + ("Importar" if _lang == "es" else "Import"),
                  key="_imp_btn", use_container_width=True):
        st.session_state[_import_key] = not st.session_state.get(_import_key, False)

# ── Import panel ──────────────────────────────────────────────────────────────
if not _read_only and st.session_state.get("_show_import_expenses", False):
    st.divider()
    with st.container():
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

                df_up.columns = [c.strip().lower().replace(" ", "_") for c in df_up.columns]
                col_map = {
                    "description":   ["description", "descripcion", "descripción", "item", "concepto"],
                    "vendor":        ["vendor", "proveedor", "supplier"],
                    "amount":        ["amount", "monto", "valor", "precio"],
                    "date":          ["date", "fecha"],
                    "category_code": ["category_code", "categorycode", "codigo", "código", "code", "cat"],
                }
                found = {}
                for key, options in col_map.items():
                    for opt in options:
                        if opt in df_up.columns:
                            found[key] = opt
                            break

                st.write(f"{'Detected columns' if _lang == 'en' else 'Columnas detectadas'}: "
                         f"{list(df_up.columns)}")

                if "amount" not in found:
                    st.error("Amount column not found." if _lang == "en"
                             else "No se encontró columna de monto.")
                else:
                    st.dataframe(df_up.head(5), use_container_width=True)
                    bl_map = {bl.category_code: bl.id for bl in lines}

                    if st.button("Import expenses" if _lang == "en" else "Importar gastos",
                                 key="_exp_import_btn"):
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
                                line_id = bl_map.get(cat_code)
                                if not line_id:
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
                            st.success(f"{'Imported' if _lang == 'en' else 'Importados'}: {imported} "
                                       f"{'expenses' if _lang == 'en' else 'gastos'}")
                            st.rerun()
                        if errors:
                            with st.expander(f"{'Warnings' if _lang == 'en' else 'Advertencias'} "
                                             f"({len(errors)})"):
                                for e in errors[:10]:
                                    st.caption(e)
            except Exception as ex:
                st.error(f"Error reading file: {ex}")
