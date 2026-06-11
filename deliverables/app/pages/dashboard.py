"""Tablero / Dashboard — summary metrics + 4-column read-only budget table."""
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

# ── Summary metrics ────────────────────────────────────────────────────────────
increase_pct, increase_money, increase_label = get_budget_increase(project_id)

col1, col2, col3 = st.columns(3)
col1.metric(t("project.total_budget"), fmt_money(summary.total_budgeted))
col2.metric(t("project.total_spent"),  fmt_money(summary.total_spent))
col3.metric(t("project.balance"),      fmt_money(summary.balance))

st.write("")

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

# ── 4-column read-only table ───────────────────────────────────────────────────
_lbl_cat = t("report.category_col")
_lbl_est = "Presupuesto Estimado"  if _lang == "es" else "Estimated Budget"
_lbl_adj = "Presupuesto Ajustado"  if _lang == "es" else "Adjusted Budget"
_lbl_pay = "Pagos al Día"          if _lang == "es" else "Payments to Date"
_lbl_bal = "Balance del Presupuesto" if _lang == "es" else "Budget Balance"

categories = get_all_categories()


def _cat_name(code: str) -> str:
    key = f"cat.{code}"
    translated = t(key)
    return translated if translated != key else next(
        (c.name for c in categories if c.code == code), code)


lines = get_budget_lines(project_id)

if not lines:
    st.info(t("common.no_data"))
else:
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

    grand_est = grand_adj = grand_pay = 0.0

    for top_code in sorted(groups.keys()):
        group_lines = groups[top_code]
        st.markdown(f"**{top_code} — {_cat_name(top_code)}**")

        for line in group_lines:
            estimated  = float(line.budgeted_amount)
            co_stored  = float(getattr(line, "change_order_amount", 0) or 0)
            adjusted   = co_stored if co_stored > 0 else estimated
            payments   = get_line_spent(line.id)
            balance    = adjusted - payments

            grand_est += estimated
            grand_adj += adjusted
            grand_pay += payments

            c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
            c1.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{_cat_name(line.category_code)}")
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
