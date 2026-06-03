"""Admin panel — manage users, roles, and permissions."""
import json as _json

import streamlit as st

from auth import require_auth, set_password
from db import User, UserPermission, get_session
from i18n import t
from permissions import (
    VIEWER_DEFAULT_PAGES, get_all_users_with_permissions, get_pending_users,
    is_admin, is_super_admin, save_permission,
)
from projects import get_user_projects

user = require_auth()

# Both super admins and admins with explicit panel access can enter
if not is_admin(user["id"]):
    st.error("Access restricted" if t("nav.dashboard") == "Dashboard" else "Acceso restringido")
    st.stop()

_is_super = is_super_admin(user["id"])
_lang = "en" if t("nav.dashboard") == "Dashboard" else "es"

PAGE_LABELS = {
    "dashboard":         t("nav.dashboard"),
    "expenses":          t("nav.expenses"),
    "presupuesto":       t("nav.presupuesto"),
    "trazabilidad":      t("nav.trazabilidad"),
    "trazabilidad_edit": t("trazabilidad.can_edit"),
    "timeline":          t("nav.timeline"),
    "proveedores":       t("nav.proveedores"),
    "account":           t("nav.account"),
    "admin":             t("nav.admin"),
}

all_projects = get_user_projects(user["id"])
project_options = {p.name: p.id for p in all_projects}
all_users = get_all_users_with_permissions()

# Filter visible users for non-super admins
if _is_super:
    # Sort: admins first, then viewers, then others
    role_order = {"admin": 0, "super_admin": 0, "viewer": 1, "pending": 2, "rejected": 3}
    visible_users = sorted(all_users, key=lambda u: role_order.get(u["role"], 9))
else:
    try:
        with get_session() as _s:
            perm_rec = _s.query(UserPermission).filter_by(user_id=user["id"]).first()
            managed_ids = _json.loads(perm_rec.managed_user_ids) if perm_rec and perm_rec.managed_user_ids else None
        role_order = {"admin": 0, "super_admin": 0, "viewer": 1, "pending": 2, "rejected": 3}
        visible_users = sorted(
            all_users if managed_ids is None else [u for u in all_users if u["id"] in managed_ids],
            key=lambda u: role_order.get(u["role"], 9)
        )
    except Exception:
        visible_users = []

st.title(t("nav.admin"))
st.divider()

# ── Solicitudes de aprobación ─────────────────────────────────────────────────
if _is_super:
    pending_users = get_pending_users()
    if pending_users:
        st.subheader(f"🔔 {'Pending approvals' if _lang == 'en' else 'Solicitudes pendientes'} ({len(pending_users)})")
        for pu in pending_users:
            with st.expander(f"📨 {pu['email']}", expanded=True):
                with st.form(f"approve_{pu['id']}"):
                    st.markdown("**" + ("Visible pages on approval" if _lang == "en" else "Páginas visibles al aprobar") + ":**")
                    sel_pages = []
                    cols = st.columns(2)
                    for i, (key, lbl) in enumerate(PAGE_LABELS.items()):
                        if cols[i % 2].checkbox(lbl, value=True, key=f"ap_{pu['id']}_{key}"):
                            sel_pages.append(key)
                    col_ok, col_no = st.columns(2)
                    if col_ok.form_submit_button("✅ Approve" if _lang == "en" else "✅ Aprobar", use_container_width=True):
                        save_permission(pu["id"], "viewer",
                                        sel_pages or VIEWER_DEFAULT_PAGES, None)
                        st.success(f"{pu['email']} " + ("approved." if _lang == "en" else "aprobado."))
                        st.rerun()
                    if col_no.form_submit_button("❌ Reject" if _lang == "en" else "❌ Rechazar", use_container_width=True):
                        save_permission(pu["id"], "rejected", [], None)
                        st.warning(f"{pu['email']} " + ("rejected." if _lang == "en" else "rechazado."))
                        st.rerun()
        st.divider()

# ── Crear usuario (solo super admin) ─────────────────────────────────────────
if _is_super:
    if st.button("➕ Create user" if _lang == "en" else "➕ Crear usuario"):
        st.session_state["_show_create_user"] = not st.session_state.get("_show_create_user", False)

    if st.session_state.get("_show_create_user", False):
        with st.form("add_user_form"):
            new_email = st.text_input("Email" if _lang == "en" else "Correo electrónico")
            new_role  = st.selectbox("Role" if _lang == "en" else "Rol", ["viewer", "admin"])
            new_pwd   = st.text_input("Contraseña inicial", type="password")
            new_pwd2  = st.text_input("Confirmar contraseña", type="password")
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
                        set_password(uid_new, new_pwd)
                        if new_role == "viewer":
                            save_permission(uid_new, "viewer",
                                            [k for k in PAGE_LABELS if k != "admin"], None)
                        st.session_state["_show_create_user"] = False
                        st.success(f"Usuario {new_email} creado.")
                        st.rerun()

    st.divider()

# ── Usuarios visibles ─────────────────────────────────────────────────────────
st.subheader("Registered users" if _lang == "en" else "Usuarios registrados")

if not visible_users:
    st.info("No users assigned to manage." if _lang == "en" else "No tienes usuarios asignados para gestionar.")
    st.stop()

for u in visible_users:
    is_self = u["id"] == user["id"]
    icon = "⭐" if u["role"] in ("admin", "super_admin") else "👤"
    header = f"{icon} {u['email']}" + ((" (you)" if _lang == "en" else " (tú)") if is_self else "")

    with st.expander(header, expanded=False):
        if is_self:
            st.caption("You cannot modify your own permissions." if _lang == "en" else "No puedes modificar tus propios permisos.")
            continue

        # Solo el super admin puede editar — los demás solo ven
        if not _is_super:
            st.caption(f"Role: **{u['role']}** | Only the administrator can edit profiles." if _lang == "en"
                       else f"Rol: **{u['role']}** | Solo el administrador puede editar perfiles.")
            continue

        # ── Permissions form ──────────────────────────────────────────────
        with st.form(key=f"perm_{u['id']}"):
            role = st.selectbox(
                "Role" if _lang == "en" else "Rol",
                ["admin", "viewer"],
                index=0 if u["role"] in ("admin", "super_admin") else 1,
            )

            st.markdown("**Páginas visibles** *(Viewer)*:")
            current_pages = u["allowed_pages"] if u["allowed_pages"] is not None else list(PAGE_LABELS.keys())
            selected_pages = []
            cols = st.columns(2)
            for i, (key, lbl) in enumerate(PAGE_LABELS.items()):
                if cols[i % 2].checkbox(lbl, value=key in current_pages, key=f"p_{u['id']}_{key}"):
                    selected_pages.append(key)

            st.markdown("**" + ("Visible projects" if _lang == "en" else "Proyectos visibles") + "** *(Viewer)*:")
            selected_project_ids = []
            for pname, pid in project_options.items():
                checked_p = (u["allowed_project_ids"] is None or
                             (u["allowed_project_ids"] is not None and pid in u["allowed_project_ids"]))
                if st.checkbox(pname, value=checked_p, key=f"proj_{u['id']}_{pid}"):
                    selected_project_ids.append(pid)
            # All checked = no restriction (None), otherwise use the list
            if len(selected_project_ids) == len(project_options):
                selected_project_ids = None

            # Managed users
            st.markdown("**" + ("Visible emails" if _lang == "en" else "Correos visibles") + "**")
            other_users = [x for x in all_users
                           if x["id"] != u["id"] and not is_super_admin(x["id"])]
            try:
                with get_session() as _s:
                    perm_rec = _s.query(UserPermission).filter_by(user_id=u["id"]).first()
                    current_managed = _json.loads(perm_rec.managed_user_ids) \
                        if perm_rec and perm_rec.managed_user_ids else None
            except Exception:
                current_managed = None

            selected_managed = []
            if other_users:
                for ou in other_users:
                    checked_m = current_managed is None or (current_managed is not None and ou["id"] in current_managed)
                    if st.checkbox(ou["email"], value=checked_m, key=f"mu_{u['id']}_{ou['id']}"):
                        selected_managed.append(ou["id"])
                if len(selected_managed) == len(other_users):
                    selected_managed = None  # all checked = no restriction
            else:
                st.caption("No other users registered." if _lang == "en" else "No hay otros usuarios registrados.")

            if st.form_submit_button("💾 Guardar permisos", use_container_width=True):
                pages_to_save = None if role == "admin" else (selected_pages or [k for k in PAGE_LABELS if k != "admin"])
                save_permission(u["id"], role, pages_to_save, selected_project_ids, selected_managed)
                st.success("Permissions updated." if _lang == "en" else "Permisos actualizados.")
                st.rerun()

        # ── Reset password ────────────────────────────────────────────────
        st.markdown("**Reset password**" if _lang == "en" else "**Restablecer contrasena**")
        with st.form(f"pwd_{u['id']}"):
            new_pwd = st.text_input("New password" if _lang == "en" else "Nueva contraseña", type="password", key=f"pw_{u['id']}")
            if st.form_submit_button("Save password" if _lang == "en" else "Guardar contraseña", use_container_width=True):
                if len(new_pwd) < 6:
                    st.error("Mínimo 6 caracteres.")
                else:
                    set_password(u["id"], new_pwd)
                    st.success("Password updated." if _lang == "en" else "Contraseña actualizada.")

        # ── Delete user (solo super admin) ────────────────────────────────
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
                    st.error(f"⚠ This user has **{user_projects} project(s)** associated. Deleting the user will also delete those projects and all their data."
                             if _lang == "en" else
                             f"⚠ Este usuario tiene **{user_projects} proyecto(s)** asociado(s). Eliminar el usuario borrará también esos proyectos y todos sus datos.")
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
