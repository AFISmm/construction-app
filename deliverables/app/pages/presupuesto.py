"""Presupuesto / Budget — editable 4-column table + chart + approval flow."""
import altair as alt
import streamlit as st
from auth import require_auth, send_budget_approval_email
from budget import get_all_categories, get_budget_lines, update_budget_line
from budget_versioning import (change_status, create_budget, create_version,
                               get_budgets, STATUS_LABELS_ES, STATUS_LABELS_EN)
from expenses import get_line_spent
from i18n import fmt_money, t
from permissions import get_budget_approver_email
from projects import get_project_summary
from reports import build_variance_df, chart_data, export_csv, export_pdf, export_xlsx

user = require_auth()
project_id = st.session_state.get("current_project_id")
_lang = st.session_state.get("lang", "en")

if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

summary = get_project_summary(project_id)
title = "Presupuesto" if _lang == "es" else "Budget"
st.title(title)

if summary:
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric(t("project.total_budget"), fmt_money(summary.total_budgeted))
    mc2.metric(t("project.total_spent"),  fmt_money(summary.total_spent))
    mc3.metric(t("project.balance"),      fmt_money(summary.balance))
    st.divider()

# ── Column labels ─────────────────────────────────────────────────────────────
_lbl_cat = t("report.category_col")
_lbl_est = "Presupuesto Estimado"    if _lang == "es" else "Estimated Budget"
_lbl_adj = "Presupuesto Ajustado"    if _lang == "es" else "Adjusted Budget"
_lbl_pay = "Pagos al Día"            if _lang == "es" else "Payments to Date"
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

    pending_saves: list[tuple] = []   # (line_id, new_estimated, new_adjusted)
    grand_est = grand_adj = grand_pay = 0.0

    for top_code in sorted(groups.keys()):
        group_lines = groups[top_code]
        st.markdown(f"**{top_code} — {_cat_name(top_code)}**")

        for line in group_lines:
            estimated = float(line.budgeted_amount)
            co_stored = float(getattr(line, "change_order_amount", 0) or 0)
            adj_default = co_stored if co_stored > 0 else estimated
            payments  = get_line_spent(line.id)

            c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1.5])
            c1.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{_cat_name(line.category_code)}")

            new_est = c2.number_input(
                _lbl_est, value=estimated, min_value=0.0, step=1000.0,
                key=f"_est_{line.id}", label_visibility="collapsed"
            )
            new_adj = c3.number_input(
                _lbl_adj, value=adj_default, min_value=0.0, step=1000.0,
                key=f"_adj_{line.id}", label_visibility="collapsed"
            )

            if new_est != estimated or new_adj != adj_default:
                pending_saves.append((line.id, new_est, new_adj))

            balance = new_adj - payments
            grand_est += new_est
            grand_adj += new_adj
            grand_pay += payments

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

    st.write("")

    # ── Budget status badge ───────────────────────────────────────────────────
    _SL = STATUS_LABELS_ES if _lang == "es" else STATUS_LABELS_EN
    _budgets = get_budgets(project_id)
    _cur_budget = _budgets[0] if _budgets else None
    if _cur_budget:
        _ver_lbl = f"V{_cur_budget.version_major}.{_cur_budget.version_minor}"
        _status_lbl = _SL.get(_cur_budget.status, _cur_budget.status)
        _color = {
            "draft":    "#8ec5d6",
            "review":   "#f59e0b",
            "approved": "#22c55e",
            "rejected": "#ef4444",
        }.get(_cur_budget.status, "#8ec5d6")
        st.markdown(
            f'<span style="background:{_color};color:#fff;padding:3px 10px;'
            f'border-radius:10px;font-size:0.8rem;">'
            f'📋 {_ver_lbl} · {_status_lbl}</span>',
            unsafe_allow_html=True,
        )
        st.write("")

    # ── Action buttons ────────────────────────────────────────────────────────
    if not st.session_state.get("is_viewer", False):
        _bc1, _bc2 = st.columns(2)

        _draft_lbl = "💾 Guardar borrador" if _lang == "es" else "💾 Save draft"
        if _bc1.button(_draft_lbl, use_container_width=True):
            for _lid, _new_est, _new_adj in pending_saves:
                update_budget_line(_lid, project_id, _new_est,
                                   change_order_amount=_new_adj)
            _budgets2 = get_budgets(project_id)
            if not _budgets2:
                create_budget(project_id, summary.name, user["id"])
            else:
                _b = _budgets2[0]
                _lines_now = get_budget_lines(project_id)
                _rows = [{"category_code": l.category_code, "description": l.description or "",
                          "budgeted_amount": float(l.budgeted_amount), "room_id": l.room_id}
                         for l in _lines_now]
                create_version(_b.id, "minor",
                               "Borrador guardado" if _lang == "es" else "Draft saved",
                               _rows, user["id"])
            st.success("✅ Guardado como borrador." if _lang == "es" else "✅ Saved as draft.")
            st.rerun()

        _approval_lbl = "📤 Enviar para aprobación" if _lang == "es" else "📤 Send for approval"
        _approver_email = get_budget_approver_email()
        if _bc2.button(_approval_lbl, use_container_width=True, type="primary"):
            if not _approver_email:
                st.warning(
                    "No hay un aprobador configurado. Contacta al administrador."
                    if _lang == "es" else
                    "No budget approver configured. Contact the administrator."
                )
            else:
                for _lid, _new_est, _new_adj in pending_saves:
                    update_budget_line(_lid, project_id, _new_est,
                                       change_order_amount=_new_adj)
                _budgets3 = get_budgets(project_id)
                _lines_now2 = get_budget_lines(project_id)
                _rows2 = [{"category_code": l.category_code, "description": l.description or "",
                            "budgeted_amount": float(l.budgeted_amount), "room_id": l.room_id}
                           for l in _lines_now2]
                if not _budgets3:
                    _b3 = create_budget(project_id, summary.name, user["id"])
                    _b3_id = _b3.id
                else:
                    _b3_id = _budgets3[0].id
                    create_version(_b3_id, "minor",
                                   "Enviado para aprobacion" if _lang == "es" else "Sent for approval",
                                   _rows2, user["id"])
                change_status(_b3_id, "review", user["id"],
                              "Enviado para aprobacion" if _lang == "es" else "Sent for approval")
                _bv_list = get_budgets(project_id)
                _ver_str = (f"V{_bv_list[0].version_major}.{_bv_list[0].version_minor}"
                            if _bv_list else "V1.0")
                _sent = send_budget_approval_email(
                    _approver_email, summary.name, user["email"], _ver_str
                )
                _notif = (f"✅ Presupuesto {_ver_str} enviado para aprobación a **{_approver_email}**."
                          if _lang == "es" else
                          f"✅ Budget {_ver_str} sent for approval to **{_approver_email}**.")
                if not _sent:
                    _notif += (" (Notificación por email pendiente de configurar SMTP.)"
                               if _lang == "es" else " (Email notification pending SMTP configuration.)")
                st.success(_notif)
                st.rerun()

st.divider()

# ── Chart ──────────────────────────────────────────────────────────────────────
st.subheader(t("report.chart_title"))
df_chart = chart_data(project_id)
if not df_chart.empty and "Tipo" in df_chart.columns:
    chart = (
        alt.Chart(df_chart)
        .mark_bar()
        .encode(
            x=alt.X("Categoria:N", title=t("report.category_col"),
                    axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Valor:Q", title="US$"),
            color=alt.Color(
                "Tipo:N",
                scale=alt.Scale(range=["#4fc3f7", "#e05a20"]),
                legend=alt.Legend(title=""),
            ),
            xOffset="Tipo:N",
            tooltip=["Categoria:N", "Tipo:N", alt.Tooltip("Valor:Q", format=",.0f")],
        )
        .properties(height=300)
    )
    st.altair_chart(chart, use_container_width=True)
else:
    st.caption(t("common.no_data"))

st.divider()

# ── Export buttons ─────────────────────────────────────────────────────────────
if summary:
    currency     = summary.currency
    project_name = summary.name
    df_var = build_variance_df(project_id, currency)

    if not df_var.empty:
        bc1, bc2, bc3 = st.columns(3)
        bc1.download_button(
            "📥 CSV", export_csv(project_id),
            file_name="presupuesto.csv", mime="text/csv",
            use_container_width=True,
        )
        bc2.download_button(
            "📥 Excel", export_xlsx(project_id),
            file_name="presupuesto.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        try:
            pdf_bytes = export_pdf(project_id, project_name, currency)
            bc3.download_button(
                "📥 PDF", pdf_bytes,
                file_name="presupuesto.pdf", mime="application/pdf",
                use_container_width=True,
            )
        except Exception:
            bc3.warning("PDF no disponible" if _lang == "es" else "PDF unavailable")
