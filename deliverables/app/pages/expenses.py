"""Pagos / Payments — 4 columns: Description, Vendor, Payment, Date."""
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


def _cat_name(code: str) -> str:
    key = f"cat.{code}"
    translated = t(key)
    return translated if translated != key else next(
        (c.name for c in categories if c.code == code), code)


groups: dict[str, list] = {}
for line in lines:
    top = line.category_code.split(".")[0]
    groups.setdefault(top, []).append(line)

# ── Column labels ──────────────────────────────────────────────────────────────
_lbl_desc   = t("expense.description_label")
_lbl_vendor = t("expense.vendor_label")
_lbl_pay    = "Pago" if _lang == "es" else "Payment"
_lbl_date   = t("expense.date_label")

# ── Table header ───────────────────────────────────────────────────────────────
h1, h2, h3, h4, h5 = st.columns([2.5, 1.8, 1.2, 1.2, 0.6])
h1.markdown(f"**{_lbl_desc}**")
h2.markdown(f"**{_lbl_vendor}**")
h3.markdown(f"**{_lbl_pay}**")
h4.markdown(f"**{_lbl_date}**")
h5.markdown("**+**")
st.divider()

grand_spent = 0.0

for top_code in sorted(groups.keys()):
    group_lines = groups[top_code]
    cat_label = _cat_name(top_code)

    # Sum all payments for this top-level category
    cat_total_spent = sum(get_line_spent(line.id) for line in group_lines)
    grand_spent += cat_total_spent

    # Category header row — shows total payments in the Payment column
    r1, r2, r3, r4, r5 = st.columns([2.5, 1.8, 1.2, 1.2, 0.6])
    r1.markdown(f"**{top_code} — {cat_label}**")
    r2.markdown("—")
    r3.markdown(f"**{fmt_money(cat_total_spent)}**")
    r4.markdown("—")
    r5.markdown("")

    for line in group_lines:
        line_spent = get_line_spent(line.id)

        # Budget line row — shows payments total for this line
        c1, c2, c3, c4, c5 = st.columns([2.5, 1.8, 1.2, 1.2, 0.6])
        c1.write(f"&nbsp;&nbsp;&nbsp;&nbsp;{_cat_name(line.category_code)}")
        c2.write("—")
        c3.write(fmt_money(line_spent))
        c4.write("—")

        add_key = f"_add_{line.id}"
        if not _read_only and c5.button("＋", key=f"btn_{line.id}", help=t("expense.add_expense")):
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

        # Existing expense rows
        exps = get_expenses(project_id, line.id)
        for exp in exps:
            e1, e2, e3, e4, e5 = st.columns([2.5, 1.8, 1.2, 1.2, 0.6])
            e1.caption(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↳ {exp.description or _cat_name(line.category_code)}")
            e2.caption(exp.vendor or "—")
            e3.caption(fmt_money(exp.amount))
            e4.caption(str(exp.expense_date))
            if not _read_only and e5.button("✕", key=f"del_{exp.id}", help=t("common.delete")):
                delete_expense(exp.id, project_id)
                st.rerun()

    st.write("")

# ── Grand total ────────────────────────────────────────────────────────────────
st.divider()
st.metric(t("project.total_spent"), fmt_money(grand_spent))

# ── Export / Import bar ────────────────────────────────────────────────────────
if not _read_only:
    st.divider()
    import io as _io
    import pandas as _pd

    all_exps = []
    for line in lines:
        for exp in get_expenses(project_id, line.id):
            all_exps.append({
                "Categoria" if _lang == "es" else "Category":
                    _cat_name(line.category_code),
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
            file_name="pagos.csv", mime="text/csv", use_container_width=True,
        )
        _buf_xl = _io.BytesIO()
        with _pd.ExcelWriter(_buf_xl, engine="openpyxl") as _wr:
            df_exp.to_excel(_wr, index=False, sheet_name="Pagos")
        bc2.download_button(
            "📥 Excel", _buf_xl.getvalue(),
            file_name="pagos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        try:
            from reports import export_pdf as _epdf
            from projects import get_project_summary as _gps
            _summ = _gps(project_id)
            _pdf = _epdf(project_id, _summ.name if _summ else "Pagos",
                         _summ.currency if _summ else "")
            bc3.download_button(
                "📥 PDF", _pdf, file_name="pagos.pdf",
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

# ── Import panel ───────────────────────────────────────────────────────────────
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

                    if st.button("Import payments" if _lang == "en" else "Importar pagos",
                                 key="_exp_import_btn"):
                        imported = 0
                        errors = []
                        for _, row in df_up.iterrows():
                            try:
                                amt = float(str(row[found["amount"]]).replace(",", "").replace("$", ""))
                                if amt <= 0:
                                    continue
                                desc     = str(row.get(found.get("description", ""), "")).strip() or "—"
                                vendor   = str(row.get(found.get("vendor", ""), "")).strip() or ""
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
                                       f"{'payments' if _lang == 'en' else 'pagos'}")
                            st.rerun()
                        if errors:
                            with st.expander(f"{'Warnings' if _lang == 'en' else 'Advertencias'} "
                                             f"({len(errors)})"):
                                for e in errors[:10]:
                                    st.caption(e)
            except Exception as ex:
                st.error(f"Error reading file: {ex}")
