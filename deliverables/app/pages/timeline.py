"""Timeline — cronologia de actividades del proyecto."""
import streamlit as st

from auth import require_auth
from budget_versioning import STATUS_LABELS_EN, STATUS_LABELS_ES, get_user_email
from db import Budget, BudgetAuditLog, User, get_session
from i18n import t

user = require_auth()
project_id = st.session_state.get("current_project_id")
_lang = st.session_state.get("lang", "en")

if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

# ── Cargar datos ──────────────────────────────────────────────────────────────

def _load_timeline(project_id: int):
    with get_session() as s:
        budgets = s.query(Budget).filter_by(project_id=project_id).all()
        budget_map = {b.id: b.name for b in budgets}
        budget_ids = list(budget_map.keys())
        if not budget_ids:
            return [], budget_map, []
        logs = (
            s.query(BudgetAuditLog, User)
            .outerjoin(User, BudgetAuditLog.user_id == User.id)
            .filter(BudgetAuditLog.budget_id.in_(budget_ids))
            .order_by(BudgetAuditLog.timestamp.desc())
            .all()
        )
        users_raw = s.query(User).all()
        users_list = [{"id": u.id, "email": u.email} for u in users_raw]
        result = []
        for log, u in logs:
            result.append({
                "id": log.id,
                "budget_id": log.budget_id,
                "budget_name": budget_map.get(log.budget_id, "—"),
                "version_id": log.version_id,
                "action": log.action,
                "field_changed": log.field_changed,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "notes": log.notes,
                "user_id": log.user_id,
                "user_email": u.email if u else "—",
                "timestamp": log.timestamp,
            })
        return result, budget_map, users_list


ACTION_ICONS = {
    "create":          "✨",
    "version_created": "🔄",
    "status_change":   "📋",
    "restored":        "↩️",
}
ACTION_LABELS_ES = {
    "create":          "Presupuesto creado",
    "version_created": "Nueva version",
    "status_change":   "Cambio de estado",
    "restored":        "Version restaurada",
}
ACTION_LABELS_EN = {
    "create":          "Budget created",
    "version_created": "New version",
    "status_change":   "Status change",
    "restored":        "Version restored",
}
STATUS_LABELS = STATUS_LABELS_ES if _lang == "es" else STATUS_LABELS_EN


def _action_label(action: str) -> str:
    d = ACTION_LABELS_ES if _lang == "es" else ACTION_LABELS_EN
    return d.get(action, action)


def _format_event(ev: dict) -> str:
    icon = ACTION_ICONS.get(ev["action"], "📌")
    action = _action_label(ev["action"])
    budget_lbl = "Presupuesto" if _lang == "es" else "Budget"
    parts = [f"{icon} **{action}** — {budget_lbl}: *{ev['budget_name']}*"]

    if ev["action"] == "version_created":
        old_v = ev["old_value"] or "—"
        new_v = ev["new_value"] or "—"
        parts.append(f"V{old_v} → V{new_v}")
        if ev["notes"]:
            lbl = "Comentario" if _lang == "es" else "Comment"
            parts.append(f"*{lbl}: {ev['notes']}*")

    elif ev["action"] == "status_change":
        old_s = STATUS_LABELS.get(ev["old_value"], ev["old_value"] or "—")
        new_s = STATUS_LABELS.get(ev["new_value"], ev["new_value"] or "—")
        parts.append(f"{old_s} → **{new_s}**")
        if ev["notes"]:
            lbl = "Motivo" if _lang == "es" else "Reason"
            parts.append(f"*{lbl}: {ev['notes']}*")

    elif ev["action"] == "create":
        if ev["notes"]:
            parts.append(f"*{ev['notes']}*")

    elif ev["action"] == "restored":
        if ev["notes"]:
            parts.append(f"*{ev['notes']}*")

    return "  \n".join(parts)


# ── Titulo ────────────────────────────────────────────────────────────────────
title = t("nav.timeline")
st.title(title)
st.divider()

events, budget_map, users_list = _load_timeline(project_id)

if not events:
    st.info(t("timeline.no_events"))
    st.stop()

# ── Filtros ───────────────────────────────────────────────────────────────────
with st.expander(t("timeline.filters"), expanded=False):
    fc1, fc2, fc3, fc4 = st.columns(4)

    # Filtro por accion
    all_label = t("timeline.all")
    action_options = [all_label] + list({ev["action"] for ev in events})
    sel_action = fc1.selectbox(
        t("timeline.event_type"),
        action_options, key="_tl_action"
    )

    # Filtro por usuario
    user_label = "Usuario" if _lang == "es" else "User"
    user_emails = [all_label] + sorted({ev["user_email"] for ev in events if ev["user_email"] != "—"})
    sel_user = fc2.selectbox(
        user_label,
        user_emails, key="_tl_user"
    )

    # Filtro por presupuesto
    budget_label = "Presupuesto" if _lang == "es" else "Budget"
    budget_names = [all_label] + sorted(set(budget_map.values()))
    sel_budget = fc3.selectbox(
        budget_label,
        budget_names, key="_tl_budget"
    )

    # Busqueda por keyword
    keyword = fc4.text_input(t("timeline.search"), key="_tl_kw")

# ── Aplicar filtros ───────────────────────────────────────────────────────────
filtered = events

if sel_action and sel_action != all_label:
    filtered = [e for e in filtered if e["action"] == sel_action]
if sel_user and sel_user != all_label:
    filtered = [e for e in filtered if e["user_email"] == sel_user]
if sel_budget and sel_budget != all_label:
    filtered = [e for e in filtered if e["budget_name"] == sel_budget]
if keyword:
    kw = keyword.lower()
    filtered = [
        e for e in filtered
        if kw in (e["notes"] or "").lower()
        or kw in (e["old_value"] or "").lower()
        or kw in (e["new_value"] or "").lower()
        or kw in e["user_email"].lower()
        or kw in e["budget_name"].lower()
        or kw in _action_label(e["action"]).lower()
    ]

# ── Paginacion ────────────────────────────────────────────────────────────────
PAGE_SIZE = 20
total = len(filtered)
total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

if "tl_page" not in st.session_state:
    st.session_state["tl_page"] = 1
page = st.session_state["tl_page"]
page = max(1, min(page, total_pages))

page_events = filtered[(page - 1) * PAGE_SIZE : page * PAGE_SIZE]

# Contador
lbl_showing = (
    t("timeline.showing").format(n=len(page_events), total=total)
    if "{n}" in t("timeline.showing")
    else f"Mostrando {len(page_events)} de {total} eventos"
    if _lang == "es"
    else f"Showing {len(page_events)} of {total} events"
)
st.caption(lbl_showing)

# ── Renderizar timeline ───────────────────────────────────────────────────────
COLORS = {
    "create":          "#4fc3f7",
    "version_created": "#22c55e",
    "status_change":   "#e05a20",
    "restored":        "#a78bfa",
}

for ev in page_events:
    color = COLORS.get(ev["action"], "#8ec5d6")
    ts = ev["timestamp"].strftime("%d/%m/%Y %I:%M %p") if ev["timestamp"] else "—"
    user_lbl = "Usuario" if _lang == "es" else "User"

    st.markdown(
        f"""
        <div style="
            border-left: 4px solid {color};
            padding: 0.6rem 1rem;
            margin-bottom: 0.8rem;
            background: rgba(255,255,255,0.03);
            border-radius: 0 6px 6px 0;
        ">
        """,
        unsafe_allow_html=True,
    )
    st.markdown(_format_event(ev))
    st.caption(f"📅 {ts} · {user_lbl}: **{ev['user_email']}**")
    st.markdown("</div>", unsafe_allow_html=True)

# ── Navegacion de paginas ─────────────────────────────────────────────────────
if total_pages > 1:
    st.divider()
    pcol1, pcol2, pcol3 = st.columns([1, 2, 1])
    if pcol1.button(t("timeline.prev"), disabled=page <= 1, key="_tl_prev"):
        st.session_state["tl_page"] = page - 1
        st.rerun()
    page_lbl = (
        t("timeline.page").format(page=page, total=total_pages)
        if "{page}" in t("timeline.page")
        else f"Pagina {page} de {total_pages}"
        if _lang == "es"
        else f"Page {page} of {total_pages}"
    )
    pcol2.markdown(
        f"<p style='text-align:center;color:#8ec5d6;'>{page_lbl}</p>",
        unsafe_allow_html=True,
    )
    if pcol3.button(t("timeline.next"), disabled=page >= total_pages, key="_tl_next"):
        st.session_state["tl_page"] = page + 1
        st.rerun()
