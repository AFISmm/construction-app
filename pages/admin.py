"""Admin panel — manage users, roles, and permissions."""
import json as _json

import streamlit as st

from auth import require_auth, set_password
from db import User, UserPermission, get_session
from i18n import t
from permissions import get_all_users_with_permissions, is_super_admin, save_permission
from projects import get_user_projects

user = require_auth()

if not is_super_admin(user["id"]):
    st.error("Acceso restringido / Access restricted")
    st.stop()

PAGE_LABELS = {
    "dashboard": "Inicio",
    "import":    "Importar",
    "projects":  "Proyectos",
    "progress":  "Progreso",
    "expenses":  "Gastos",
    "rooms":     "Habitaciones",
    "account":   "Mi cuenta",
}

all_projects = get_user_projects(user["id"])
project_options = {p.name: p.id for p in all_projects}
all_users = get_all_users_with_permissions()

st.title(t("nav.admin"))
st.divider()

# ── Crear usuario (collapsible) ───────────────────────────────────────────────
if st.button("➕ Crear usuario", use_container_width=False):
    st.session_state["_show_create_user"] = not st.session_state.get("_show_create_user", False)

if st.session_state.get("_show_create_user", False):
    with st.form("add_user_form"):
        new_email = st.text_input("Correo electrónico")
        new_role  = st.selectbox("Rol", ["viewer", "admin"],
                                 help="Admin: acceso total. Viewer: acceso restringido.")
        new_pwd   = st.text_input("Contraseña inicial", type="password")
        new_pwd2  = st.text_input("Confirmar contraseña", type="password")
        col_save, col_cancel = st.columns(2)
        save = col_save.form_submit_button("Crear", use_container_width=True)
        cancel = col_cancel.form_submit_button("Cancelar", use_container_width=True)
        if cancel:
            st.session_state["_show_create_user"] = False
            st.rerun()
        if save:
            if not new_email or "@" not in new_email:
                st.error("Correo inválido.")
            elif len(new_pwd) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres.")
            elif new_pwd != new_pwd2:
                st.error("Las contraseñas no coinciden.")
            else:
                uid_new = None
                with get_session() as s:
                    existing = s.query(User).filter_by(email=new_email.strip().lower()).first()
                    if existing:
                        st.error("Ese correo ya está registrado.")
                    else:
                        u_new = User(email=new_email.strip().lower())
                        s.add(u_new)
                        s.flush()
                        uid_new = u_new.id
                if uid_new:
                    set_password(uid_new, new_pwd)
                    if new_role == "viewer":
                        save_permission(uid_new, "viewer", list(PAGE_LABELS.keys()), None)
                    st.session_state["_show_create_user"] = False
                    st.success(f"Usuario {new_email} creado.")
                    st.rerun()

st.divider()

# ── Usuarios registrados ──────────────────────────────────────────────────────
st.subheader("👥 Usuarios registrados")

for u in all_users:
    is_self = u["id"] == user["id"]
    icon = "⭐" if u["role"] in ("admin", "super_admin") else "👤"
    header = f"{icon} {u['email']}" + (" (tú)" if is_self else "")

    with st.expander(header, expanded=False):
        if is_self:
            st.caption("No puedes modificar tus propios permisos.")
            continue

        # ── Permissions form ──────────────────────────────────────────────
        with st.form(key=f"perm_{u['id']}"):
            role = st.selectbox(
                "Rol",
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

            st.markdown("**Proyectos visibles** *(Viewer)*:")
            all_proj = st.checkbox("Todos", value=u["allowed_project_ids"] is None, key=f"ap_{u['id']}")
            selected_project_ids = None
            if not all_proj:
                selected_project_ids = []
                for pname, pid in project_options.items():
                    checked_p = u["allowed_project_ids"] is not None and pid in u["allowed_project_ids"]
                    if st.checkbox(pname, value=checked_p, key=f"proj_{u['id']}_{pid}"):
                        selected_project_ids.append(pid)

            st.markdown("**Usuarios visibles en Configurar perfiles** *(si es admin)*:")
            other_users = [x for x in all_users if x["id"] != u["id"] and not is_super_admin(x["id"])]
            try:
                with get_session() as _s:
                    perm_rec = _s.query(UserPermission).filter_by(user_id=u["id"]).first()
                    current_managed = _json.loads(perm_rec.managed_user_ids) if perm_rec and perm_rec.managed_user_ids else None
            except Exception:
                current_managed = None

            all_managed = st.checkbox("Todos los usuarios", value=current_managed is None, key=f"am_{u['id']}")
            selected_managed = None
            if not all_managed:
                selected_managed = []
                for ou in other_users:
                    checked_m = current_managed is not None and ou["id"] in current_managed
                    if st.checkbox(ou["email"], value=checked_m, key=f"mu_{u['id']}_{ou['id']}"):
                        selected_managed.append(ou["id"])

            if st.form_submit_button("💾 Guardar permisos", use_container_width=True):
                pages_to_save = None if role == "admin" else (selected_pages or list(PAGE_LABELS.keys()))
                save_permission(u["id"], role, pages_to_save, selected_project_ids, selected_managed)
                st.success("Permisos actualizados.")
                st.rerun()

        # ── Reset password ────────────────────────────────────────────────
        st.markdown("**🔑 Restablecer contraseña**")
        with st.form(f"pwd_{u['id']}"):
            new_pwd = st.text_input("Nueva contraseña", type="password", key=f"pw_{u['id']}")
            if st.form_submit_button("Guardar contraseña", use_container_width=True):
                if len(new_pwd) < 6:
                    st.error("Mínimo 6 caracteres.")
                else:
                    set_password(u["id"], new_pwd)
                    st.success("Contraseña actualizada.")

        # ── Delete user ───────────────────────────────────────────────────
        st.markdown("**🗑 Eliminar usuario**")
        confirm_key = f"_confirm_del_{u['id']}"
        if not st.session_state.get(confirm_key, False):
            if st.button("Eliminar usuario", key=f"del_{u['id']}", type="secondary"):
                st.session_state[confirm_key] = True
                st.rerun()
        else:
            st.warning(f"¿Confirmas eliminar **{u['email']}**? Esta acción no se puede deshacer.")
            col_yes, col_no = st.columns(2)
            if col_yes.button("Sí, eliminar", key=f"yes_{u['id']}", type="primary"):
                with get_session() as s:
                    u_obj = s.get(User, u["id"])
                    if u_obj:
                        s.delete(u_obj)
                st.session_state.pop(confirm_key, None)
                st.success(f"Usuario {u['email']} eliminado.")
                st.rerun()
            if col_no.button("Cancelar", key=f"no_{u['id']}"):
                st.session_state.pop(confirm_key, None)
                st.rerun()
