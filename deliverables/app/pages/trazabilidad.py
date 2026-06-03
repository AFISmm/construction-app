"""Trazabilidad — Budget versioning, audit trail, and comparison."""
from datetime import datetime

import pandas as pd
import streamlit as st
from i18n import fmt_money, t as _t

from auth import require_auth
from budget import get_budget_lines
from budget_versioning import (
    STATUS_LABELS_EN, STATUS_LABELS_ES, change_status, compare_versions,
    create_budget, create_version, get_audit_log, get_budget, get_budgets,
    get_user_email, get_versions, restore_version,
)
from permissions import can_edit_trazabilidad
from i18n import t

user = require_auth()
project_id = st.session_state.get("current_project_id")
if not project_id:
    st.info(t("project.no_projects"))
    st.stop()

lang = st.session_state.get("lang", "en")
STATUS_LABELS = STATUS_LABELS_ES if lang == "es" else STATUS_LABELS_EN
_can_edit = can_edit_trazabilidad(user["id"])

STATUS_COLORS = {
    "draft":    "#aaaaaa",
    "review":   "#f59e0b",
    "approved": "#22c55e",
    "rejected": "#ef4444",
}


def _cat_label(code: str) -> str:
    """Return translated category name, fallback to stored description or code."""
    key = f"cat.{code}"
    translated = _t(key)
    return translated if translated != key else code


def _enrich_snapshot(rows: list[dict]) -> list[dict]:
    """Replace description with translated category name for bilingual display."""
    enriched = []
    for r in rows:
        r2 = dict(r)
        r2["description"] = _cat_label(r["category_code"])
        enriched.append(r2)
    return enriched


def _badge(status: str) -> str:
    color = STATUS_COLORS.get(status, "#aaa")
    label = STATUS_LABELS.get(status, status)
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:10px;font-size:0.75rem;">{label}</span>'


st.title("📋 " + ("Trazabilidad" if lang == "es" else "Traceability"))

# ── Select or create budget ───────────────────────────────────────────────────
budgets = get_budgets(project_id)

col_sel, col_new = st.columns([4, 1])
budget_options = {f"V{b.version_major}.{b.version_minor} — {b.name}": b.id for b in budgets}

selected_budget_id = None
if budget_options:
    sel_label = col_sel.selectbox(
        "Presupuesto" if lang == "es" else "Budget",
        list(budget_options.keys()),
        key="_traz_budget_sel",
    )
    selected_budget_id = budget_options[sel_label]

if col_new.button("➕ Nuevo" if lang == "es" else "➕ New", use_container_width=True):
    st.session_state["_traz_create"] = True

if st.session_state.get("_traz_create", False):
    with st.form("create_budget_form"):
        bname = st.text_input("Nombre del presupuesto" if lang == "es" else "Budget name",
                              value="Presupuesto Principal" if lang == "es" else "Main Budget")
        if st.form_submit_button("Crear" if lang == "es" else "Create", use_container_width=True):
            b = create_budget(project_id, bname, user["id"])
            st.session_state["_traz_create"] = False
            st.success(f"{'Presupuesto creado' if lang == 'es' else 'Budget created'}: {bname} V1.0")
            st.rerun()
        if st.form_submit_button("Cancelar" if lang == "es" else "Cancel"):
            st.session_state["_traz_create"] = False
            st.rerun()
    st.stop()

if not selected_budget_id:
    st.info("No hay presupuestos. Crea uno con ➕ Nuevo." if lang == "es"
            else "No budgets yet. Create one with ➕ New.")
    st.stop()

budget = get_budget(selected_budget_id)

# ── Header — current state ────────────────────────────────────────────────────
h1, h2, h3, h4 = st.columns(4)
h1.metric("Versión vigente" if lang == "es" else "Current version",
          f"V{budget.version_major}.{budget.version_minor}")
h2.markdown(
    f"**{'Estado' if lang == 'es' else 'Status'}**<br>{_badge(budget.status)}",
    unsafe_allow_html=True,
)
h3.metric("Última modificación" if lang == "es" else "Last modified",
          str(budget.updated_at)[:16] if budget.updated_at else "—")
h4.metric("Modificado por" if lang == "es" else "Modified by",
          get_user_email(budget.updated_by).split("@")[0])

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
if lang == "es":
    tab_labels = ["📄 Vigente", "🕐 Versiones", "🔍 Comparar", "📜 Auditoría"]
else:
    tab_labels = ["📄 Current", "🕐 Versions", "🔍 Compare", "📜 Audit log"]

tab_vigente, tab_versions, tab_compare, tab_audit = st.tabs(tab_labels)


# ── TAB 1: Vigente ────────────────────────────────────────────────────────────
with tab_vigente:
    # Status actions (editors only)
    if not _can_edit:
        st.info("View-only mode. Contact the administrator to request edit access."
                if lang == "en" else
                "Modo solo lectura. Contacta al administrador para solicitar acceso de edicion.")
    act_label = "Cambiar estado" if lang == "es" else "Change status"
    with st.expander(act_label, expanded=False):
        new_status = st.selectbox(
            "Estado" if lang == "es" else "Status",
            [s for s in ["draft", "review", "approved", "rejected"] if s != budget.status],
            format_func=lambda s: STATUS_LABELS.get(s, s),
            key="_traz_new_status",
        )
        notes_st = st.text_input("Notas" if lang == "es" else "Notes", key="_traz_status_notes")
        if _can_edit and st.button("Guardar estado" if lang == "es" else "Save status", key="_traz_save_status"):
            change_status(selected_budget_id, new_status, user["id"], notes_st or None)
            st.success("Estado actualizado." if lang == "es" else "Status updated.")
            st.rerun()

    # Load latest version snapshot and show editable lines
    versions = get_versions(selected_budget_id)
    if not versions:
        st.info("Sin versiones." if lang == "es" else "No versions.")
        st.stop()

    latest_v = versions[0]
    import json as _json
    lines_data = _enrich_snapshot(_json.loads(latest_v.snapshot_json))

    st.subheader(f"V{latest_v.version_label} — {STATUS_LABELS.get(latest_v.status, latest_v.status)}")

    # Editable table — apply any pending edits from session state to get live values
    col_labels = {
        "category_code":   "Code" if lang == "en" else "Código",
        "description":     "Description" if lang == "en" else "Descripción",
        "budgeted_amount": "Amount" if lang == "en" else "Monto",
    }
    df_base = pd.DataFrame(lines_data)[["category_code", "description", "budgeted_amount"]].copy()

    # Apply edits from previous interaction so monto_fmt reflects live changes
    prev_state = st.session_state.get("_traz_editor")
    if prev_state and "edited_rows" in prev_state:
        for idx_str, changes in prev_state["edited_rows"].items():
            idx = int(idx_str)
            for col, val in changes.items():
                if col in df_base.columns and idx < len(df_base):
                    df_base.at[idx, col] = val

    df_base["monto_fmt"] = df_base["budgeted_amount"].map(fmt_money)

    fmt_label = f"{'Monto' if lang == 'es' else 'Amount'} (US$)"
    edit_label = f"{'Monto' if lang == 'es' else 'Amount'} ({'editar' if lang == 'es' else 'edit'})"

    edited = st.data_editor(
        df_base,
        column_config={
            "category_code":   st.column_config.TextColumn(col_labels["category_code"]),
            "description":     st.column_config.TextColumn(col_labels["description"], disabled=True),
            "monto_fmt":       st.column_config.TextColumn(fmt_label, disabled=True),
            "budgeted_amount": st.column_config.NumberColumn(edit_label, format="%.2f", min_value=0),
        },
        column_order=["category_code", "description", "monto_fmt", "budgeted_amount"],
        use_container_width=True,
        hide_index=True,
        key="_traz_editor",
    )

    total = edited["budgeted_amount"].sum()
    st.caption(f"**Total: {fmt_money(total)}**")

    # Save as new version (editors only)
    if _can_edit:
        sv_label = "Guardar nueva version" if lang == "es" else "Save as new version"
        with st.expander(sv_label):
            with st.form("new_version_form"):
                change_desc = st.text_input(
                    "Descripcion del cambio" if lang == "es" else "Change description")
                change_type = st.radio(
                    "Tipo de cambio" if lang == "es" else "Change type",
                    ["minor", "major"],
                    format_func=lambda x: ("Cambio menor (V+0.1)" if x == "minor" else "Cambio de alcance (V+1.0)")
                                if lang == "es" else
                                ("Minor change (V+0.1)" if x == "minor" else "Scope change (V+1.0)"),
                    horizontal=True,
                )
                if st.form_submit_button("Crear version" if lang == "es" else "Create version",
                                         use_container_width=True):
                    if not change_desc:
                        st.error("Describe el cambio." if lang == "es" else "Please describe the change.")
                    else:
                        new_rows = edited.to_dict("records")
                        create_version(selected_budget_id, change_type, change_desc, new_rows, user["id"])
                        st.success("Nueva version creada." if lang == "es" else "New version created.")
                        st.rerun()

    # ── Version guide / Instructivo ───────────────────────────────────────────
    guide_label = "Version guide" if lang == "en" else "Guia de versiones"
    with st.expander(f"ℹ️ {guide_label}"):
        if lang == "en":
            st.markdown("""
**How versioning works:**

| Change type | Effect | Example |
|---|---|---|
| **Minor change (V+0.1)** | Small adjustment to an amount or description | V1.0 → V1.1 |
| **Scope change (V+1.0)** | New categories added or major restructure | V1.1 → V2.0 |
| **Restore** | Copies an old snapshot as a new major version | V2.0 → V3.0 |

**Status meanings:**

| Status | Meaning |
|---|---|
| **Draft** | Working version — can be edited freely |
| **In review** | Sent for approval — changes paused |
| **Approved** | Officially accepted — locked baseline |
| **Rejected** | Not accepted — return to draft and revise |

**Reading a version label:**
- `V1.0 — Draft` → First version, still being edited
- `V2.3 — Approved` → Second major scope, third minor adjustment, approved
- `V3.0 — Draft` → Restored from a previous version
            """)
        else:
            st.markdown("""
**Como funciona el versionado:**

| Tipo de cambio | Efecto | Ejemplo |
|---|---|---|
| **Cambio menor (V+0.1)** | Ajuste pequeño de monto o descripcion | V1.0 → V1.1 |
| **Cambio de alcance (V+1.0)** | Nuevas categorias o reestructuracion mayor | V1.1 → V2.0 |
| **Restauracion** | Copia un snapshot anterior como nueva version mayor | V2.0 → V3.0 |

**Significado de los estados:**

| Estado | Significado |
|---|---|
| **Borrador** | Version en trabajo — se puede editar libremente |
| **En revision** | Enviado para aprobacion — cambios en pausa |
| **Aprobado** | Aceptado oficialmente — linea base bloqueada |
| **Rechazado** | No aceptado — volver a borrador y revisar |

**Como leer una etiqueta de version:**
- `V1.0 — Borrador` → Primera version, todavia en edicion
- `V2.3 — Aprobado` → Segundo alcance mayor, tercer ajuste menor, aprobado
- `V3.0 — Borrador` → Restaurado desde una version anterior
            """)


# ── TAB 2: Versiones ──────────────────────────────────────────────────────────
with tab_versions:
    versions = get_versions(selected_budget_id)
    if not versions:
        st.info("Sin versiones." if lang == "es" else "No versions.")
    else:
        for v in versions:
            is_current = (v.version_major == budget.version_major and
                          v.version_minor == budget.version_minor)
            label = f"{'✅ ' if is_current else ''}V{v.version_label}"
            with st.expander(label, expanded=is_current):
                c1, c2, c3 = st.columns(3)
                c1.markdown(_badge(v.status), unsafe_allow_html=True)
                c2.caption(str(v.created_at)[:16])
                c3.caption(get_user_email(v.created_by))
                if v.change_description:
                    st.caption(f"📝 {v.change_description}")

                v_lines = _enrich_snapshot(_json.loads(v.snapshot_json))
                v_df = pd.DataFrame(v_lines)[["category_code", "description", "budgeted_amount"]]
                v_df["budgeted_amount"] = v_df["budgeted_amount"].map(fmt_money)
                v_df.columns = (
                    ["Código", "Descripción", "Monto"] if lang == "es"
                    else ["Code", "Description", "Amount"]
                )
                st.dataframe(v_df, use_container_width=True, hide_index=True)

                if not is_current and _can_edit:
                    restore_label = "Restaurar esta version" if lang == "es" else "Restore this version"
                    with st.form(f"restore_{v.id}"):
                        rdesc = st.text_input(
                            "Motivo de restauración" if lang == "es" else "Reason for restoring")
                        if st.form_submit_button(restore_label, use_container_width=True):
                            if not rdesc:
                                st.error("Escribe el motivo." if lang == "es" else "Enter a reason.")
                            else:
                                restore_version(selected_budget_id, v.id, rdesc, user["id"])
                                st.success("Versión restaurada." if lang == "es" else "Version restored.")
                                st.rerun()


# ── TAB 3: Comparar ───────────────────────────────────────────────────────────
with tab_compare:
    versions = get_versions(selected_budget_id)
    if len(versions) < 2:
        st.info("Se necesitan al menos 2 versiones para comparar." if lang == "es"
                else "At least 2 versions needed to compare.")
    else:
        v_options = {f"V{v.version_label}": v.id for v in versions}
        cv1, cv2 = st.columns(2)
        sel_a = cv1.selectbox("Versión A" if lang == "es" else "Version A",
                              list(v_options.keys()), index=1, key="_cmp_a")
        sel_b = cv2.selectbox("Versión B" if lang == "es" else "Version B",
                              list(v_options.keys()), index=0, key="_cmp_b")

        if st.button("Comparar" if lang == "es" else "Compare", key="_cmp_btn"):
            if sel_a == sel_b:
                st.warning("Selecciona versiones diferentes." if lang == "es" else "Select different versions.")
            else:
                diff = compare_versions(v_options[sel_a], v_options[sel_b])
                changed = [d for d in diff if d["changed"] or d["added"] or d["removed"]]
                same    = [d for d in diff if not d["changed"] and not d["added"] and not d["removed"]]

                lbl_changes = f"**{len(changed)}** {'cambios' if lang == 'es' else 'changes'} · **{len(same)}** {'sin cambios' if lang == 'es' else 'unchanged'}"
                st.markdown(lbl_changes)

                col_code = "Código" if lang == "es" else "Code"
                col_desc = "Descripción" if lang == "es" else "Description"
                col_stat = "Estado" if lang == "es" else "Status"

                rows = []
                for d in diff:
                    if d["added"]:
                        tag = "🟢 Agregado" if lang == "es" else "🟢 Added"
                    elif d["removed"]:
                        tag = "🔴 Eliminado" if lang == "es" else "🔴 Removed"
                    elif d["changed"]:
                        tag = "🟡 Cambiado" if lang == "es" else "🟡 Changed"
                    else:
                        tag = "— Igual" if lang == "es" else "— Same"
                    rows.append({
                        col_code: d["code"],
                        col_desc: _cat_label(d["code"]),
                        sel_a: fmt_money(d["val_a"]) if d["val_a"] is not None else "—",
                        sel_b: fmt_money(d["val_b"]) if d["val_b"] is not None else "—",
                        col_stat: tag,
                    })

                df_diff = pd.DataFrame(rows)
                st.dataframe(df_diff, use_container_width=True, hide_index=True)


# ── TAB 4: Auditoría ──────────────────────────────────────────────────────────
with tab_audit:
    audit = get_audit_log(selected_budget_id)
    if not audit:
        st.info("Sin registros de auditoría." if lang == "es" else "No audit records.")
    else:
        ACTION_LABELS = {
            "create":          ("Creación"         if lang == "es" else "Creation"),
            "version_created": ("Nueva versión"    if lang == "es" else "New version"),
            "status_change":   ("Cambio de estado" if lang == "es" else "Status change"),
            "restored":        ("Restauración"     if lang == "es" else "Restore"),
            "edit_line":       ("Edición de línea" if lang == "es" else "Line edit"),
        }
        h_date   = "Fecha"    if lang == "es" else "Date"
        h_user   = "Usuario"  if lang == "es" else "User"
        h_action = "Acción"   if lang == "es" else "Action"
        h_field  = "Campo"    if lang == "es" else "Field"
        h_old    = "Anterior" if lang == "es" else "Before"
        h_new    = "Nuevo"    if lang == "es" else "After"
        h_notes  = "Notas"    if lang == "es" else "Notes"
        rows = []
        for entry in audit:
            rows.append({
                h_date:   str(entry.timestamp)[:16],
                h_user:   get_user_email(entry.user_id),
                h_action: ACTION_LABELS.get(entry.action, entry.action),
                h_field:  entry.field_changed or "—",
                h_old:    entry.old_value or "—",
                h_new:    entry.new_value or "—",
                h_notes:  entry.notes or "—",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("🔒 " + ("Registro inmutable — ningún registro puede eliminarse."
                   if lang == "es" else "Immutable log — records cannot be deleted."))
