"""Admin panel — manage users, roles, and permissions."""
import json as _json

import streamlit as st

from auth import require_auth, set_password
from db import ExtendedProfile, User, UserPermission, get_session
from i18n import t
from permissions import (
    ALL_ROLES, APPROVABLE_MODULES, EXTERNAL_ROLES, ROLE_LABELS_EN, ROLE_LABELS_ES,
    VIEWER_DEFAULT_PAGES, get_all_approval_modules, get_all_users_with_permissions,
    get_pending_users, is_admin, is_super_admin, save_approval_modules, save_permission,
)
from projects import get_user_projects

user = require_auth()

if not is_admin(user["id"]):
    st.error("Access restricted" if t("nav.dashboard") == "Dashboard" else "Acceso restringido")
    st.stop()

_is_super = is_super_admin(user["id"])
_lang = "en" if t("nav.dashboard") == "Dashboard" else "es"
ROLE_LABELS = ROLE_LABELS_EN if _lang == "en" else ROLE_LABELS_ES

PAGE_LABELS = {
    "dashboard":    t("nav.dashboard"),
    "expenses":     t("nav.expenses"),
    "presupuesto":  t("nav.presupuesto"),
    "trazabilidad": t("nav.trazabilidad"),
    "timeline":     t("nav.timeline"),
    "proveedores":  t("nav.proveedores"),
    "account":      t("nav.account"),
}

all_projects = get_user_projects(user["id"])
project_options = {p.name: p.id for p in all_projects}
all_users = get_all_users_with_permissions()

role_order = {
    "admin": 0, "super_admin": 0,
    "coordinador_construccion": 1, "coordinador_pagos": 1,
    "gestor_permisos": 1, "usuario_general": 1,
    "proveedor": 2, "contratista": 2,
    "pending_extended": 3, "pending": 4, "rejected": 5,
}

if _is_super:
    visible_users = sorted(all_users, key=lambda u: role_order.get(u["role"], 9))
else:
    try:
        with get_session() as _s:
            perm_rec = _s.query(UserPermission).filter_by(user_id=user["id"]).first()
            managed_ids = _json.loads(perm_rec.managed_user_ids) if perm_rec and perm_rec.managed_user_ids else None
        visible_users = sorted(
            all_users if managed_ids is None else [u for u in all_users if u["id"] in managed_ids],
            key=lambda u: role_order.get(u["role"], 9)
        )
    except Exception:
        visible_users = []

st.title(t("nav.admin"))
st.divider()

# ── Aprobadores por módulo ────────────────────────────────────────────────────
if _is_super:
    _approver_title = "Aprobadores por módulo" if _lang == "es" else "Module Approvers"
    st.subheader(f"✅ {_approver_title}")
    st.caption(
        "Selecciona qué usuarios pueden aprobar cambios en cada módulo."
        if _lang == "es" else
        "Select which users can approve changes in each module."
    )

    # Non-admin users only
    _approvable_users = [u for u in all_users if u["role"] not in ("admin", "super_admin",
                         "pending", "pending_extended", "rejected")]

    if not _approvable_users:
        st.info("No hay usuarios con roles activos para asignar como aprobadores."
                if _lang == "es" else "No active users available to assign as approvers.")
    else:
        _current_approvals = get_all_approval_modules()  # {user_id: [modules]}
        _mod_keys = list(APPROVABLE_MODULES.keys())
        _mod_labels = [APPROVABLE_MODULES[k][0 if _lang == "es" else 1] for k in _mod_keys]

        # ── Table header ──────────────────────────────────────────────────────
        _hcols = st.columns([3] + [1.2] * len(_mod_keys))
        _hcols[0].markdown(f"**{'Usuario' if _lang == 'es' else 'User'}**")
        for _i, _lbl in enumerate(_mod_labels):
            _hcols[_i + 1].markdown(f"**{_lbl}**")
        st.divider()

        # ── User rows with checkboxes ─────────────────────────────────────────
        _new_approvals: dict[int, list[str]] = {}
        for _au in _approvable_users:
            _user_current = _current_approvals.get(_au["id"], [])
            _rcols = st.columns([3] + [1.2] * len(_mod_keys))
            _rcols[0].write(_au["email"])
            _selected_mods = []
            for _i, _mkey in enumerate(_mod_keys):
                _checked = _mkey in _user_current
                if _rcols[_i + 1].checkbox(
                    _mkey, value=_checked,
                    key=f"appr_{_au['id']}_{_mkey}",
                    label_visibility="collapsed"
                ):
                    _selected_mods.append(_mkey)
            _new_approvals[_au["id"]] = _selected_mods

        st.write("")
        if st.button("💾 " + ("Guardar aprobadores" if _lang == "es" else "Save approvers"),
                     key="_save_approvers"):
            save_approval_modules(_new_approvals)
            st.success("Aprobadores actualizados." if _lang == "es" else "Approvers updated.")
            st.rerun()

    st.divider()

# ── Solicitudes pendientes de aprobación ──────────────────────────────────────
if _is_super:
    pending_users = get_pending_users()
    if pending_users:
        st.subheader(f"🔔 {'Pending approvals' if _lang == 'en' else 'Solicitudes pendientes'} ({len(pending_users)})")
        for pu in pending_users:
            with st.expander(f"📨 {pu['email']}", expanded=True):
                with st.form(f"approve_{pu['id']}"):
                    st.markdown("**" + ("Assign role (required)" if _lang == "en" else "Asignar rol (obligatorio)") + ":**")

                    selectable_roles = [r for r in ALL_ROLES if r != "admin"] + ["admin"]
                    sel_role = st.selectbox(
                        "Rol" if _lang == "es" else "Role",
                        selectable_roles,
                        format_func=lambda r: ROLE_LABELS.get(r, r),
                        key=f"role_sel_{pu['id']}"
                    )

                    is_external = sel_role in EXTERNAL_ROLES

                    if not is_external:
                        st.markdown("**" + ("Visible pages" if _lang == "en" else "Páginas visibles") + ":**")
                        sel_pages = []
                        cols = st.columns(2)
                        for i, (key, lbl) in enumerate(PAGE_LABELS.items()):
                            if cols[i % 2].checkbox(lbl, value=True, key=f"ap_{pu['id']}_{key}"):
                                sel_pages.append(key)
                    else:
                        st.info(
                            "Vendor/Contractor: will be redirected to complete extended registration form."
                            if _lang == "en" else
                            "Proveedor/Contratista: será redirigido a completar el formulario de registro extendido."
                        )

                    col_ok, col_no = st.columns(2)
                    if col_ok.form_submit_button("✅ Approve" if _lang == "en" else "✅ Aprobar", use_container_width=True):
                        if is_external:
                            save_permission(pu["id"], "pending_extended", [], None)
                        else:
                            pages = sel_pages or list(PAGE_LABELS.keys())
                            save_permission(pu["id"], sel_role, pages, None)
                        st.success(f"{pu['email']} " + ("approved." if _lang == "en" else "aprobado."))
                        st.rerun()
                    if col_no.form_submit_button("❌ Reject" if _lang == "en" else "❌ Rechazar", use_container_width=True):
                        save_permission(pu["id"], "rejected", [], None)
                        st.warning(f"{pu['email']} " + ("rejected." if _lang == "en" else "rechazado."))
                        st.rerun()
        st.divider()

    # ── Perfiles extendidos pendientes de revisión ────────────────────────────
    with get_session() as _s:
        pending_ext_perms = _s.query(UserPermission).filter_by(role="pending_extended").all()
        pending_ext_profiles = []
        for pep in pending_ext_perms:
            u_obj = _s.get(User, pep.user_id)
            prof = _s.query(ExtendedProfile).filter_by(user_id=pep.user_id).first()
            if u_obj and prof:
                pending_ext_profiles.append({"user": u_obj, "profile": prof, "perm": pep})

    if pending_ext_profiles:
        st.subheader(f"📋 {'Extended registrations pending review' if _lang == 'en' else 'Registros extendidos pendientes'} ({len(pending_ext_profiles)})")
        for item in pending_ext_profiles:
            u_obj = item["user"]
            prof = item["profile"]
            with st.expander(f"📄 {u_obj.email}", expanded=True):
                c1, c2 = st.columns(2)
                c1.markdown(f"**{'Company' if _lang == 'en' else 'Empresa'}:** {prof.company_name}")
                c1.markdown(f"**{'Name' if _lang == 'en' else 'Nombre'}:** {prof.first_name} {prof.middle_name or ''} {prof.last_name}".strip())
                c2.markdown(f"**{'Phone' if _lang == 'en' else 'Teléfono'}:** {prof.phone or '—'}")
                c2.markdown(f"**{'Email' if _lang == 'en' else 'Correo'}:** {prof.contact_email}")
                st.markdown(f"**{'Category' if _lang == 'en' else 'Categoría'}:** {prof.category}")

                with st.form(f"ext_approve_{u_obj.id}"):
                    st.markdown("**" + ("Enable modules" if _lang == "en" else "Habilitar módulos") + ":**")
                    sel_pages_ext = []
                    cols_ext = st.columns(2)
                    for i, (key, lbl) in enumerate(PAGE_LABELS.items()):
                        if cols_ext[i % 2].checkbox(lbl, value=False, key=f"ext_{u_obj.id}_{key}"):
                            sel_pages_ext.append(key)

                    ext_role_options = EXTERNAL_ROLES
                    ext_role = st.selectbox(
                        "Rol" if _lang == "es" else "Role",
                        ext_role_options,
                        format_func=lambda r: ROLE_LABELS.get(r, r),
                        key=f"ext_role_{u_obj.id}"
                    )

                    if st.form_submit_button("✅ Habilitar acceso" if _lang == "es" else "✅ Enable access", use_container_width=True):
                        pages_final = sel_pages_ext or list(PAGE_LABELS.keys())
                        save_permission(u_obj.id, ext_role, pages_final, None)
                        with get_session() as _ps2:
                            _prof2 = _ps2.query(ExtendedProfile).filter_by(user_id=u_obj.id).first()
                            if _prof2:
                                from datetime import datetime as _dt
                                _prof2.reviewed_at = _dt.utcnow()
                        st.success(f"{u_obj.email} " + ("access enabled." if _lang == "en" else "acceso habilitado."))
                        st.rerun()
        st.divider()

# ── Crear usuario (solo super admin) ─────────────────────────────────────────
if _is_super:
    if st.button("➕ Create user" if _lang == "en" else "➕ Crear usuario"):
        st.session_state["_show_create_user"] = not st.session_state.get("_show_create_user", False)

    if st.session_state.get("_show_create_user", False):
        with st.form("add_user_form"):
            new_email = st.text_input("Email" if _lang == "en" else "Correo electrónico")
            new_role  = st.selectbox(
                "Role" if _lang == "en" else "Rol",
                ALL_ROLES,
                format_func=lambda r: ROLE_LABELS.get(r, r),
            )
            new_pwd  = st.text_input("Contraseña inicial", type="password")
            new_pwd2 = st.text_input("Confirmar contraseña", type="password")
            col_save, col_cancel = st.columns(2)
            save   = col_save.form_submit_button("Crear", use_container_width=True)
            cancel = col_cancel.form_submit_button("Cancel" if _lang == "en" else "Cancelar", use_container_width=True)
            if cancel:
                st.session_state["_show_create_user"] = False
                st.rerun()
            if save:
                if not new_email or "@" not in new_email:
                    st.error("Invalid email." if _lang == "en" else "Correo inválido.")
                elif len(new_pwd) < 6:
                    st.error("Mínimo 6 caracteres.")
                elif new_pwd != new_pwd2:
                    st.error("Las contraseñas no coinciden.")
                else:
                    uid_new = None
                    with get_session() as s:
                        existing = s.query(User).filter_by(email=new_email.strip().lower()).first()
                        if existing:
                            st.error("This email is already registered." if _lang == "en" else "Ese correo ya está registrado.")
                        else:
                            u_new = User(email=new_email.strip().lower())
                            s.add(u_new)
                            s.flush()
                            uid_new = u_new.id
                    if uid_new:
                        set_password(uid_new, new_pwd, force_change=True)
                        if new_role not in ("admin", "super_admin"):
                            save_permission(uid_new, new_role, list(PAGE_LABELS.keys()), None)
                        st.session_state["_show_create_user"] = False
                        st.success(f"Usuario {new_email} creado. Deberá cambiar su contraseña al ingresar.")
                        st.rerun()
    st.divider()

# ── Dialogs for user actions ──────────────────────────────────────────────────

@st.dialog("✅ Aprobar usuario")
def _aprobar_dialog(target_user: dict) -> None:
    """Show pending items for a user and allow individual approval/rejection."""
    from datetime import datetime as _dt
    from db import Budget, Expense, get_session as _gs

    st.markdown(f"**Usuario:** {target_user['email']} — Rol: **{ROLE_LABELS.get(target_user['role'], target_user['role'])}**")
    st.divider()

    proj_id = st.session_state.get("current_project_id")

    # --- Account approval (if pending) ---
    if target_user["role"] == "pending":
        st.subheader("Solicitud de acceso pendiente")
        selectable_roles = [r for r in ALL_ROLES if r != "admin"] + ["admin"]
        sel_role = st.selectbox(
            "Asignar rol",
            selectable_roles,
            format_func=lambda r: ROLE_LABELS.get(r, r),
            key=f"_apr_role_{target_user['id']}",
        )
        is_external = sel_role in EXTERNAL_ROLES
        if not is_external:
            st.markdown("**Páginas visibles:**")
            sel_pages: list[str] = []
            cols = st.columns(2)
            for i, (pk, pl) in enumerate(PAGE_LABELS.items()):
                if cols[i % 2].checkbox(pl, value=True, key=f"_apr_pg_{target_user['id']}_{pk}"):
                    sel_pages.append(pk)
        else:
            st.info("Proveedor/Contratista: será redirigido a completar el formulario extendido.")

        ca, cr = st.columns(2)
        if ca.button("✅ Aprobar acceso", use_container_width=True, type="primary", key=f"_apr_ok_{target_user['id']}"):
            if is_external:
                save_permission(target_user["id"], "pending_extended", [], None)
            else:
                pages_final = sel_pages or list(PAGE_LABELS.keys())
                save_permission(target_user["id"], sel_role, pages_final, None)
            st.success(f"{target_user['email']} aprobado.")
            st.rerun()
        if cr.button("❌ Rechazar", use_container_width=True, key=f"_apr_no_{target_user['id']}"):
            save_permission(target_user["id"], "rejected", [], None)
            st.warning(f"{target_user['email']} rechazado.")
            st.rerun()
        st.divider()

    # --- Pending financial items ---
    st.subheader("Ítems pendientes de aprobación")
    found_items = False

    if proj_id:
        with get_session() as _s:
            # Presupuestos en revisión creados por este usuario
            budgets_review = _s.query(Budget).filter_by(
                project_id=proj_id, status="review", created_by=target_user["id"]
            ).all()

            if budgets_review:
                found_items = True
                st.markdown("**Presupuestos en revisión:**")
                for b in budgets_review:
                    cols = st.columns([3, 1, 1])
                    cols[0].write(f"📋 {b.name} v{b.version_major}.{b.version_minor}")
                    if cols[1].button("✅", key=f"_bappr_{b.id}", help="Aprobar"):
                        with get_session() as _s2:
                            bv = _s2.get(Budget, b.id)
                            if bv:
                                bv.status = "approved"
                                bv.updated_by = user["id"]
                        st.success("Presupuesto aprobado.")
                        st.rerun()
                    if cols[2].button("❌", key=f"_brej_{b.id}", help="Rechazar"):
                        with get_session() as _s2:
                            bv = _s2.get(Budget, b.id)
                            if bv:
                                bv.status = "rejected"
                                bv.updated_by = user["id"]
                        st.warning("Presupuesto rechazado.")
                        st.rerun()

            # Gastos/pagos pendientes de aprobación de este usuario
            try:
                from sqlalchemy import text as _text
                with get_session() as _gs2:
                    pending_expenses = _gs2.execute(
                        _text("""
                            SELECT id, description, amount, expense_date, vendor
                            FROM expenses
                            WHERE project_id = :pid
                              AND created_by = :uid
                              AND approval_status = 'pending'
                        """),
                        {"pid": proj_id, "uid": target_user["id"]},
                    ).fetchall()
            except Exception:
                pending_expenses = []

            if pending_expenses:
                found_items = True
                st.markdown("**Gastos/Pagos pendientes:**")
                for exp in pending_expenses:
                    cols = st.columns([4, 1, 1])
                    cols[0].write(f"💰 {exp[4] or '—'} | {exp[1] or '—'} | ${exp[2]:,.0f} ({exp[3]})")
                    if cols[1].button("✅", key=f"_eappr_{exp[0]}", help="Aprobar"):
                        from sqlalchemy import text as _text2
                        with get_session() as _gs3:
                            _gs3.execute(
                                _text2("""
                                    UPDATE expenses
                                    SET approval_status='approved', approver_id=:aid, approved_at=:ts
                                    WHERE id=:eid
                                """),
                                {"aid": user["id"], "ts": _dt.utcnow(), "eid": exp[0]},
                            )
                        st.success("Gasto aprobado.")
                        st.rerun()
                    if cols[2].button("❌", key=f"_erej_{exp[0]}", help="Rechazar"):
                        from sqlalchemy import text as _text3
                        with get_session() as _gs4:
                            _gs4.execute(
                                _text3("""
                                    UPDATE expenses
                                    SET approval_status='rejected', approver_id=:aid, approved_at=:ts
                                    WHERE id=:eid
                                """),
                                {"aid": user["id"], "ts": _dt.utcnow(), "eid": exp[0]},
                            )
                        st.warning("Gasto rechazado.")
                        st.rerun()

    if not found_items and target_user["role"] != "pending":
        st.info("No hay ítems pendientes de aprobación para este usuario en el proyecto activo.")


@st.dialog("✏️ Editar — Subir archivos")
def _editar_dialog(target_user: dict) -> None:
    """Allow admin to upload files into the target user's accessible modules."""
    from file_manager import MODULES, save_file as _sf

    proj_id = st.session_state.get("current_project_id")
    if not proj_id:
        st.warning("Selecciona un proyecto activo primero.")
        return

    st.markdown(f"**Subir archivos para:** {target_user['email']}")
    st.markdown(f"**Proyecto activo ID:** {proj_id}")
    st.divider()

    # Determine accessible modules for this user
    user_pages = target_user.get("allowed_pages") or list(PAGE_LABELS.keys())
    page_to_module = {
        "presupuesto": "presupuesto",
        "expenses": "gastos",
        "proveedores": "proveedores",
        "trazabilidad": "trazabilidad",
    }
    accessible_modules = {
        mod: MODULES[mod]
        for pg, mod in page_to_module.items()
        if pg in user_pages and mod in MODULES
    }
    accessible_modules["general"] = MODULES["general"]

    if not accessible_modules:
        st.info("Este usuario no tiene módulos accesibles.")
        return

    sel_module_label = st.selectbox(
        "Módulo destino",
        list(accessible_modules.values()),
        key=f"_edit_mod_{target_user['id']}",
    )
    sel_module = next(k for k, v in accessible_modules.items() if v == sel_module_label)

    uploaded = st.file_uploader(
        "Seleccionar archivos (acepta cualquier formato)",
        accept_multiple_files=True,
        key=f"_edit_files_{target_user['id']}",
    )

    if uploaded:
        if st.button("📤 Subir archivos", type="primary", use_container_width=True, key=f"_edit_upload_{target_user['id']}"):
            count = 0
            for f in uploaded:
                _sf(proj_id, target_user["id"], f.name, f.getvalue(),
                    f.type or "application/octet-stream", sel_module)
                count += 1
            st.success(f"✅ {count} archivo(s) subido(s) al módulo **{sel_module_label}**.")
            st.rerun()

    # Show existing files in selected module
    from file_manager import get_project_files
    existing = get_project_files(proj_id, sel_module)
    if existing:
        st.markdown(f"**Archivos existentes en {sel_module_label}:**")
        for pf in existing:
            size_kb = round(pf.file_size / 1024, 1)
            st.markdown(f"- 📄 `{pf.filename}` ({size_kb} KB) — {pf.uploaded_at.strftime('%Y-%m-%d %H:%M') if pf.uploaded_at else '—'}")


@st.dialog("👁️ Ver usuario")
def _ver_dialog(target_user: dict) -> None:
    """Read-only view of a user's profile, modules, files, and recent activity."""
    from db import BudgetAuditLog, Budget, Expense, Project, get_session as _gs

    st.markdown(f"### {target_user['email']}")
    st.markdown(f"**Rol:** {ROLE_LABELS.get(target_user['role'], target_user['role'])}")

    # Status badge
    status_colors = {
        "pending": "🟡 Pendiente",
        "rejected": "🔴 Rechazado",
        "pending_extended": "🟠 Registro pendiente",
    }
    status_display = status_colors.get(
        target_user["role"],
        "🟢 Activo" if target_user["role"] not in ("pending", "rejected", "pending_extended") else target_user["role"]
    )
    st.markdown(f"**Estado:** {status_display}")
    st.divider()

    # Accessible modules
    user_pages = target_user.get("allowed_pages")
    if user_pages is None:
        st.markdown("**Módulos:** Acceso completo")
    else:
        visible = [PAGE_LABELS[k] for k in user_pages if k in PAGE_LABELS]
        st.markdown("**Módulos con acceso:** " + (", ".join(visible) if visible else "Ninguno"))

    # Accessible projects
    proj_ids = target_user.get("allowed_project_ids")
    if proj_ids is None:
        st.markdown("**Proyectos:** Todos")
    else:
        with _gs() as _s:
            proj_names = [
                p.name for p in _s.query(Project).filter(Project.id.in_(proj_ids)).all()
            ]
        st.markdown("**Proyectos:** " + (", ".join(proj_names) if proj_names else "Ninguno"))

    st.divider()

    # Files uploaded by this user
    proj_id = st.session_state.get("current_project_id")
    if proj_id:
        from file_manager import MODULES
        from db import ProjectFile, get_session as _gs2
        with _gs2() as _s:
            user_files = _s.query(ProjectFile).filter_by(
                project_id=proj_id, uploaded_by=target_user["id"]
            ).order_by(ProjectFile.uploaded_at.desc()).all()
            _s.expunge_all()

        if user_files:
            st.markdown("**Archivos subidos (proyecto activo):**")
            for pf in user_files[:15]:
                mod_label = MODULES.get(pf.module, pf.module)
                size_kb = round(pf.file_size / 1024, 1)
                ts = pf.uploaded_at.strftime("%Y-%m-%d %H:%M") if pf.uploaded_at else "—"
                st.markdown(f"- 📄 `{pf.filename}` | {mod_label} | {size_kb} KB | {ts}")
        else:
            st.caption("No hay archivos subidos por este usuario en el proyecto activo.")

    # Recent activity (audit log)
    st.divider()
    st.markdown("**Actividad reciente:**")
    proj_id = st.session_state.get("current_project_id")
    if proj_id:
        with get_session() as _s:
            logs = (
                _s.query(BudgetAuditLog)
                .join(Budget)
                .filter(Budget.project_id == proj_id, BudgetAuditLog.user_id == target_user["id"])
                .order_by(BudgetAuditLog.timestamp.desc())
                .limit(10)
                .all()
            )
            for log in logs:
                ts = log.timestamp.strftime("%Y-%m-%d %H:%M") if log.timestamp else "—"
                st.markdown(f"- `{ts}` — {log.action}: {log.field_changed or ''} {log.notes or ''}")
            if not logs:
                st.caption("Sin actividad registrada en el proyecto activo.")
    else:
        st.caption("Selecciona un proyecto activo para ver la actividad.")


# ── Usuarios registrados ──────────────────────────────────────────────────────
st.subheader("Registered users" if _lang == "en" else "Usuarios registrados")

if not visible_users:
    st.info("No users assigned to manage." if _lang == "en" else "No tienes usuarios asignados para gestionar.")
    st.stop()

# Header row
hcols = st.columns([4, 2, 1, 1, 1])
hcols[0].markdown("**Usuario**")
hcols[1].markdown("**Rol**")
hcols[2].markdown("**✅ APROBAR**")
hcols[3].markdown("**✏️ EDITAR**")
hcols[4].markdown("**👁️ VER**")
st.divider()

for u in visible_users:
    is_self = u["id"] == user["id"]
    role_lbl = ROLE_LABELS.get(u["role"], u["role"])
    icon = "⭐" if u["role"] in ("admin", "super_admin") else "👤"

    row = st.columns([4, 2, 1, 1, 1])
    row[0].markdown(f"{icon} **{u['email']}**" + (f" _(tú)_" if is_self else ""))
    row[1].markdown(role_lbl)

    # APROBAR: show for pending users OR users with pending financial items
    aprobar_visible = u["role"] == "pending" or (not is_self and u["role"] not in ("admin", "super_admin"))
    if aprobar_visible and not is_self:
        if row[2].button("✅", key=f"_aprobar_{u['id']}", help="Aprobar", use_container_width=True):
            _aprobar_dialog(u)
    else:
        row[2].markdown("—")

    # EDITAR: all non-self users
    if not is_self:
        if row[3].button("✏️", key=f"_editar_{u['id']}", help="Editar / Subir archivos", use_container_width=True):
            _editar_dialog(u)
    else:
        row[3].markdown("—")

    # VER: all users (including self)
    if row[4].button("👁️", key=f"_ver_{u['id']}", help="Ver", use_container_width=True):
        _ver_dialog(u)
