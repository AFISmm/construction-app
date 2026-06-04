"""Admin panel — manage users, roles, and permissions."""
import json as _json

import streamlit as st

from auth import require_auth, set_password
from db import ExtendedProfile, User, UserPermission, get_session
from i18n import t
from permissions import (
    ALL_ROLES, EXTERNAL_ROLES, ROLE_LABELS_EN, ROLE_LABELS_ES,
    VIEWER_DEFAULT_PAGES, get_all_users_with_permissions, get_pending_users,
    is_admin, is_super_admin, save_permission,
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

# ── Usuarios registrados ──────────────────────────────────────────────────────
st.subheader("Registered users" if _lang == "en" else "Usuarios registrados")

if not visible_users:
    st.info("No users assigned to manage." if _lang == "en" else "No tienes usuarios asignados para gestionar.")
    st.stop()

for u in visible_users:
    is_self = u["id"] == user["id"]
    role_lbl = ROLE_LABELS.get(u["role"], u["role"])
    icon = "⭐" if u["role"] in ("admin", "super_admin") else "👤"
    header = f"{icon} {u['email']} [{role_lbl}]" + ((" (you)" if _lang == "en" else " (tú)") if is_self else "")

    with st.expander(header, expanded=False):
        if is_self:
            st.caption("You cannot modify your own permissions." if _lang == "en" else "No puedes modificar tus propios permisos.")
            continue

        if not _is_super:
            st.caption(f"Role: **{role_lbl}** | Only the administrator can edit profiles." if _lang == "en"
                       else f"Rol: **{role_lbl}** | Solo el administrador puede editar perfiles.")
            continue

        # Extended profile info if available
        with get_session() as _ps:
            _ext_prof = _ps.query(ExtendedProfile).filter_by(user_id=u["id"]).first()
        if _ext_prof:
            with st.expander("📋 " + ("Extended profile" if _lang == "en" else "Perfil extendido"), expanded=False):
                st.write(f"**{'Company' if _lang == 'en' else 'Empresa'}:** {_ext_prof.company_name}")
                st.write(f"**{'Name' if _lang == 'en' else 'Nombre'}:** {_ext_prof.first_name} {_ext_prof.middle_name or ''} {_ext_prof.last_name}")
                st.write(f"**{'Phone' if _lang == 'en' else 'Teléfono'}:** {_ext_prof.phone or '—'}")
                st.write(f"**{'Category' if _lang == 'en' else 'Categoría'}:** {_ext_prof.category}")

        with st.form(key=f"perm_{u['id']}"):
            role = st.selectbox(
                "Role" if _lang == "en" else "Rol",
                ALL_ROLES,
                index=ALL_ROLES.index(u["role"]) if u["role"] in ALL_ROLES else 0,
                format_func=lambda r: ROLE_LABELS.get(r, r),
            )

            st.markdown("**" + ("Visible pages" if _lang == "en" else "Páginas visibles") + ":**")
            current_pages = u["allowed_pages"] if u["allowed_pages"] is not None else list(PAGE_LABELS.keys())
            selected_pages = []
            cols = st.columns(2)
            for i, (key, lbl) in enumerate(PAGE_LABELS.items()):
                if cols[i % 2].checkbox(lbl, value=key in current_pages, key=f"p_{u['id']}_{key}"):
                    selected_pages.append(key)

            st.markdown("**" + ("Visible projects" if _lang == "en" else "Proyectos visibles") + ":**")
            selected_project_ids = []
            if project_options:
                for pname, pid in project_options.items():
                    checked_p = (u["allowed_project_ids"] is None or
                                 (u["allowed_project_ids"] is not None and pid in u["allowed_project_ids"]))
                    if st.checkbox(pname, value=checked_p, key=f"proj_{u['id']}_{pid}"):
                        selected_project_ids.append(pid)
                if len(selected_project_ids) == len(project_options):
                    selected_project_ids = None
            else:
                st.caption("No hay proyectos." if _lang == "es" else "No projects.")

            if st.form_submit_button("💾 Guardar permisos", use_container_width=True):
                pages_to_save = None if role in ("admin", "super_admin") else (selected_pages or list(PAGE_LABELS.keys()))
                save_permission(u["id"], role, pages_to_save, selected_project_ids)
                st.success("Permissions updated." if _lang == "en" else "Permisos actualizados.")
                st.rerun()

        st.markdown("**Reset password**" if _lang == "en" else "**Restablecer contraseña**")
        with st.form(f"pwd_{u['id']}"):
            new_pwd = st.text_input("New password" if _lang == "en" else "Nueva contraseña", type="password", key=f"pw_{u['id']}")
            if st.form_submit_button("Save password" if _lang == "en" else "Guardar contraseña", use_container_width=True):
                from auth import validate_password_strength as _vps
                _errs = _vps(new_pwd)
                if _errs:
                    for _e in _errs:
                        st.error(_e)
                else:
                    set_password(u["id"], new_pwd, force_change=True)
                    st.success("Password updated. User will be prompted to change it on next login."
                               if _lang == "en" else
                               "Contraseña actualizada. El usuario deberá cambiarla al próximo ingreso.")

        if _is_super:
            st.markdown("**Delete user**" if _lang == "en" else "**Eliminar usuario**")
            from db import Project
            with get_session() as _s:
                user_projects = _s.query(Project).filter_by(user_id=u["id"]).count()
            confirm_key = f"_confirm_del_{u['id']}"
            if not st.session_state.get(confirm_key, False):
                if st.button("Delete user" if _lang == "en" else "Eliminar usuario", key=f"del_{u['id']}"):
                    st.session_state[confirm_key] = True
                    st.rerun()
            else:
                msg = ("Confirm deleting **" + u["email"] + "**? This cannot be undone." if _lang == "en"
                       else "¿Confirmas eliminar **" + u["email"] + "**? No se puede deshacer.")
                if user_projects > 0:
                    st.error(f"⚠ Este usuario tiene **{user_projects} proyecto(s)**. Eliminar borrará también esos datos.")
                st.warning(msg)
                col_yes, col_no = st.columns(2)
                if col_yes.button("Yes, delete" if _lang == "en" else "Sí, eliminar", key=f"yes_{u['id']}", type="primary"):
                    with get_session() as s:
                        u_obj = s.get(User, u["id"])
                        if u_obj:
                            s.delete(u_obj)
                    st.session_state.pop(confirm_key, None)
                    st.success(f"Usuario {u['email']} eliminado.")
                    st.rerun()
                if col_no.button("Cancel" if _lang == "en" else "Cancelar", key=f"no_{u['id']}"):
                    st.session_state.pop(confirm_key, None)
                    st.rerun()
