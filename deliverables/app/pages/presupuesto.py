"""Budget variance table — detailed budget vs actual by category."""
import streamlit as st
from auth import require_auth
from i18n import t
from projects import get_project_summary
from reports import build_variance_df, export_pdf, export_xlsx

user = require_auth()
project_id = st.session_state.get("current_project_id")
if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

_lang = st.session_state.get("lang", "en")
summary = get_project_summary(project_id)

title = "Budget" if _lang == "en" else "Presupuesto"
st.title(title)

if summary:
    from i18n import fmt_money
    c1, c2, c3 = st.columns(3)
    c1.metric(t("project.total_budget"), fmt_money(summary.total_budgeted))
    c2.metric(t("project.total_spent"),  fmt_money(summary.total_spent))
    c3.metric(t("project.balance"),      fmt_money(summary.balance))
    st.divider()

currency = summary.currency if summary else ""
project_name = summary.name if summary else "Budget"
df = build_variance_df(project_id, currency)

if df.empty:
    st.info(t("common.no_data"))
else:
    st.subheader(t("report.variance"))
    display_df = df.drop(columns=["_over_budget"])

    def _style_row(row):
        styles = [""] * len(row)
        if df.loc[row.name, "_over_budget"]:
            styles = ["background-color: #ffe0e0"] * len(row)
        return styles

    st.dataframe(display_df.style.apply(_style_row, axis=1), use_container_width=True)

    col_pdf, col_xlsx = st.columns(2)

    pdf_label = t("report.export_pdf")
    xlsx_label = t("report.export_xlsx")

    try:
        pdf_bytes = export_pdf(project_id, project_name, currency)
        col_pdf.download_button(
            f"📄 {pdf_label}", pdf_bytes,
            file_name="presupuesto.pdf", mime="application/pdf",
        )
    except Exception as e:
        col_pdf.warning(f"PDF no disponible: {e}" if _lang == "es" else f"PDF unavailable: {e}")

    col_xlsx.download_button(
        f"📊 {xlsx_label}", export_xlsx(project_id),
        file_name="presupuesto.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
