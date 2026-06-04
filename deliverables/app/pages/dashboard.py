"""Project Dashboard — metrics + editable variance table."""
import altair as alt
import streamlit as st
from auth import require_auth, send_budget_approval_email
from budget import get_budget_lines, get_category_totals, update_budget_line
from budget_versioning import (change_status, create_budget, create_version,
                               get_budgets, get_versions, STATUS_LABELS_ES, STATUS_LABELS_EN)
from i18n import fmt_money, t
from permissions import get_budget_approver_email
from projects import get_project_summary
from reports import chart_data, get_budget_increase_pct

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

# ── Metricas ──────────────────────────────────────────────────────────────────
increase_pct, increase_label = get_budget_increase_pct(project_id)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric(t("project.total_budget"), fmt_money(summary.total_budgeted))
col2.metric(t("project.total_spent"), fmt_money(summary.total_spent))
col3.metric(t("project.balance"), fmt_money(summary.balance))
col4.metric(t("project.pct_executed"), f"{summary.pct_executed}%")
if increase_pct is not None:
    lbl = "Aumento presupuestal" if _lang == "es" else "Budget increase"
    col5.metric(lbl, f"{increase_pct:+.1f}%", delta=increase_label, delta_color="inverse")
else:
    lbl = "Aumento presupuestal" if _lang == "es" else "Budget increase"
    col5.metric(lbl, "—")

st.divider()

# ── Tabla de variacion editable ───────────────────────────────────────────────
_read_only = st.session_state.get("is_viewer", False)

var_title = "Variacion de Presupuesto" if _lang == "es" else "Budget Variance"
st.subheader(var_title)

from budget import get_all_categories
from expenses import get_line_spent

categories = get_all_categories()


def _cat_name(code: str) -> str:
    key = f"cat.{code}"
    translated = t(key)
    return translated if translated != key else next((c.name for c in categories if c.code == code), code)


lines = get_budget_lines(project_id)

if not lines:
    st.info(t("common.no_data"))
else:
    # Group by top-level category
    groups: dict[str, list] = {}
    for line in lines:
        top = line.category_code.split(".")[0]
        groups.setdefault(top, []).append(line)

    # Header
    _lbl_cat      = t("report.category_col")
    _lbl_budget   = t("report.budgeted_col")
    _lbl_actual   = t("report.actual_col")
    _lbl_variance = t("report.variance_col")
    _lbl_pct      = t("report.pct_col")

    hc1, hc2, hc3, hc4, hc5 = st.columns([3, 1.5, 1.5, 1.5, 1])
    hc1.markdown(f"**{_lbl_cat}**")
    hc2.markdown(f"**{_lbl_budget}**")
    hc3.markdown(f"**{_lbl_actual}**")
    hc4.markdown(f"**{_lbl_variance}**")
    hc5.markdown(f"**{_lbl_pct}**")
    st.divider()

    pending_saves: list[tuple] = []  # (line_id, new_budgeted)

    for top_code in sorted(groups.keys()):
        group_lines = groups[top_code]
        cat_label = _cat_name(top_code)
        # Category header row (bold, no indentation)
        st.markdown(f"**{top_code} — {cat_label}**")

        for line in group_lines:
            spent = get_line_spent(line.id)
            budgeted = float(line.budgeted_amount)
            balance = budgeted - spent
            pct = round((spent / budgeted * 100), 1) if budgeted > 0 else 0.0

            c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1.5, 1])
            # Subcategory with indentation
            c1.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;{_cat_name(line.category_code)}")

            if not _read_only:
                new_budgeted = c2.number_input(
                    "", value=budgeted, min_value=0.0, step=1000.0,
                    key=f"_dash_bud_{line.id}", label_visibility="collapsed"
                )
                if new_budgeted != budgeted:
                    pending_saves.append((line.id, new_budgeted))
            else:
                c2.write(fmt_money(budgeted))

            color = ":red" if spent > budgeted else ""
            c3.write(f"{color}[{fmt_money(spent)}]" if color else fmt_money(spent))
            c4.write(f":red[{fmt_money(balance)}]" if balance < 0 else fmt_money(balance))
            c5.write(f"{pct:.1f}%")

        st.write("")

    # ── Estado del presupuesto ────────────────────────────────────────────────
    _SL = STATUS_LABELS_ES if _lang == "es" else STATUS_LABELS_EN
    _budgets = get_budgets(project_id)
    _cur_budget = _budgets[0] if _budgets else None
    if _cur_budget:
        _ver_lbl = f"V{_cur_budget.version_major}.{_cur_budget.version_minor}"
        _status_lbl = _SL.get(_cur_budget.status, _cur_budget.status)
        _color = {"draft": "#8ec5d6", "review": "#f59e0b", "approved": "#22c55e", "rejected": "#ef4444"}.get(_cur_budget.status, "#8ec5d6")
        st.markdown(
            f'<span style="background:{_color};color:#fff;padding:3px 10px;border-radius:10px;font-size:0.8rem;">'
            f'📋 {_ver_lbl} · {_status_lbl}</span>',
            unsafe_allow_html=True,
        )
        st.write("")

    # ── Botones de acción ─────────────────────────────────────────────────────
    if not _read_only:
        _bc1, _bc2 = st.columns(2)

        # Guardar borrador
        _draft_lbl = "💾 Guardar borrador" if _lang == "es" else "💾 Save draft"
        if _bc1.button(_draft_lbl, use_container_width=True):
            for line_id, new_amt in pending_saves:
                update_budget_line(line_id, project_id, new_amt)
            # Create or update budget as draft
            _budgets2 = get_budgets(project_id)
            if not _budgets2:
                _new_b = create_budget(project_id, summary.name, user["id"])
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

        # Enviar para aprobación
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
                # Save budget line changes
                for line_id, new_amt in pending_saves:
                    update_budget_line(line_id, project_id, new_amt)
                # Create version and set to review
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
                # Send notification
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

# ── Grafico ────────────────────────────────────────────────────────────────────
st.subheader(t("report.chart_title"))
df = chart_data(project_id)
if not df.empty and "Tipo" in df.columns:
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Categoria:N", title=t("report.category_col"), axis=alt.Axis(labelAngle=0)),
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
