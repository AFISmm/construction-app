"""Tablero / Dashboard — summary metrics + budget table (valued lines only)."""
import streamlit as st
from auth import require_auth
from budget import get_all_categories, get_budget_lines
from expenses import get_line_spent
from i18n import fmt_money, t
from projects import get_project_summary
from reports import get_budget_increase

user = require_auth()
project_id = st.session_state.get("current_project_id")
_lang = st.session_state.get("lang", "en")

if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

summary = get_project_summary(project_id)
if not summary:
    st.error(t("error.not_found"))
    st.stop()

type_label = t(f"project.type_badge_{summary.project_type}")
st.title(summary.name)
st.markdown(
    f'<span style="color:#22c55e;font-size:0.78rem;font-weight:500;">{type_label}</span>',
    unsafe_allow_html=True,
)

st.divider()

# ── Column labels ──────────────────────────────────────────────────────────────
_lbl_cat = t("report.category_col")
_lbl_est = "Presupuesto Estimado"    if _lang == "es" else "Estimated Budget"
_lbl_adj = "Presupuesto Ajustado"    if _lang == "es" else "Adjusted Budget"
_lbl_pay = "Pagos al Día"            if _lang == "es" else "Payments to Date"
_lbl_bal = "Balance del Presupuesto" if _lang == "es" else "Budget Balance"

categories = get_all_categories()
all_lines  = get_budget_lines(project_id)

# Only show lines that have a non-zero estimated budget
lines = [l for l in all_lines if float(l.budgeted_amount or 0) > 0]


def _cat_name(code: str) -> str:
    key = f"cat.{code}"
    translated = t(key)
    return translated if translated != key else next(
        (c.name for c in categories if c.code == code), code)


def _line_label(line) -> str:
    """Return the most descriptive label for a budget line."""
    if line.description:
        # description format: "C.GC.1.1 - Permits & Fees" — show just the name part
        parts = line.description.split(" - ", 1)
        return parts[1].strip() if len(parts) == 2 else line.description
    return _cat_name(line.category_code)


# ── Pre-calculate totals ────────────────────────────────────────────────────────
_line_data: dict[int, tuple[float, float, float]] = {}
grand_est = grand_adj = grand_pay = 0.0
for line in lines:
    estimated = float(line.budgeted_amount)
    co_stored = float(getattr(line, "change_order_amount", 0) or 0)
    adjusted  = co_stored if co_stored > 0 else estimated
    payments  = get_line_spent(line.id)
    _line_data[line.id] = (estimated, adjusted, payments)
    grand_est += estimated
    grand_adj += adjusted
    grand_pay += payments

# ── Summary metrics ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric(_lbl_est, fmt_money(grand_est))
col2.metric(_lbl_adj, fmt_money(grand_adj))
col3.metric(_lbl_pay, fmt_money(grand_pay))

st.write("")

increase_pct, increase_money, increase_label = get_budget_increase(project_id)
lbl_increase = "Aumento presupuestal" if _lang == "es" else "Budget increase"
col4, col5 = st.columns(2)
if increase_money is not None:
    col4.metric(f"{lbl_increase} ($)", fmt_money(increase_money))
    col5.metric(f"{lbl_increase} (%)", f"{increase_pct:+.1f}%",
                delta=increase_label, delta_color="inverse")
else:
    col4.metric(f"{lbl_increase} ($)", "—")
    col5.metric(f"{lbl_increase} (%)", "—")

st.divider()

# ── Budget table (valued lines only) ────────────────────────────────────────────
if not lines:
    st.info(
        "No hay partidas con presupuesto asignado. Agrega valores en el módulo de Presupuesto."
        if _lang == "es" else
        "No budget lines with values yet. Add amounts in the Budget module."
    )
else:
    # Group by top-level category (first segment of category_code)
    groups: dict[str, list] = {}
    for line in lines:
        top = line.category_code.split(".")[0]
        groups.setdefault(top, []).append(line)

    # Header row
    h1, h2, h3, h4, h5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    h1.markdown(f"**{_lbl_cat}**")
    h2.markdown(f"**{_lbl_est}**")
    h3.markdown(f"**{_lbl_adj}**")
    h4.markdown(f"**{_lbl_pay}**")
    h5.markdown(f"**{_lbl_bal}**")
    st.divider()

    for top_code in sorted(groups.keys()):
        group_lines = groups[top_code]
        # Group header — top-level section name
        st.markdown(f"**{top_code} — {_cat_name(top_code)}**")

        for line in sorted(group_lines, key=lambda l: l.category_code):
            estimated, adjusted, payments = _line_data[line.id]
            balance = adjusted - payments

            c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
            c1.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{_line_label(line)}")
            c2.write(fmt_money(estimated))
            c3.write(fmt_money(adjusted))
            c4.write(fmt_money(payments))
            c5.write(f":red[{fmt_money(balance)}]" if balance < 0 else fmt_money(balance))

        st.write("")

    # Grand total row
    grand_bal = grand_adj - grand_pay
    st.divider()
    g1, g2, g3, g4, g5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
    g1.markdown("**Total**")
    g2.markdown(f"**{fmt_money(grand_est)}**")
    g3.markdown(f"**{fmt_money(grand_adj)}**")
    g4.markdown(f"**{fmt_money(grand_pay)}**")
    bal_color = "red" if grand_bal < 0 else "green"
    g5.markdown(
        f'**<span style="color:{bal_color};">{fmt_money(grand_bal)}</span>**',
        unsafe_allow_html=True,
    )
