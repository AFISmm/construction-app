"""Admin panel — manage users, roles, and permissions."""
import streamlit as st

from auth import require_auth, set_password
from db import User, get_session
from i18n import t
from permissions import (
    get_all_users_with_permissions, get_managed_users,
    is_super_admin, save_permission,
)
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

# ── Add new user ──────────────────────────────────────────────────────────────
st.subheader("➕ Agregar usuario")
with st.form("add_user_form"):
    new_email = st.text_input("Correo electrónico")
    new_role  = st.selectbox("Rol", ["viewer", "admin"],
                             help="Admin: acceso total a la app. Viewer: acceso restringido.")
    new_pwd   = st.text_input("Contraseña inicial", type="password")
    new_pwd2  = st.text_input("Confirmar contraseña", type="password")
    if st.form_submit_button("Crear usuario", use_container_width=True):
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
                st.success(f"Usuario {new_email} creado como {new_role}.")
                st.rerun()

st.divider()

# ── Manage existing users ─────────────────────────────────────────────────────
st.subheader("👥 Usuarios registrados")

for u in all_users:
    is_self = u["id"] == user["id"]
    icon = "⭐" if u["role"] in ("admin", "super_admin") else "👤"
    header = f"{icon} {u['email']}" + (" (tú)" if is_self else "")

    with st.expander(header, expanded=False):
        if is_self:
            st.caption("No puedes modificar tus propios permisos.")
            continue

        with st.form(key=f"perm_{u['id']}"):
            role = st.selectbox(
                "Rol",
                ["admin", "viewer"],
                index=0 if u["role"] in ("admin", "super_admin") else 1,
                help="Admin: acceso total a la app. Viewer: acceso restringido.",
            )

            st.markdown("**Páginas visibles** *(aplica para Viewer)*:")
            current_pages = u["allowed_pages"] if u["allowed_pages"] is not None else list(PAGE_LABELS.keys())
            selected_pages = []
            cols = st.columns(2)
            for i, (key, lbl) in enumerate(PAGE_LABELS.items()):
                if cols[i % 2].checkbox(lbl, value=key in current_pages, key=f"p_{u['id']}_{key}"):
                    selected_pages.append(key)

            st.markdown("**Proyectos visibles** *(aplica para Viewer)*:")
            all_proj = st.checkbox("Todos los proyectos",
                                   value=u["allowed_project_ids"] is None,
                                   key=f"ap_{u['id']}")
            selected_project_ids = None
            if not all_proj:
                selected_project_ids = []
                for pname, pid in project_options.items():
                    checked_p = u["allowed_project_ids"] is not None and pid in u["allowed_project_ids"]
                    if st.checkbox(pname, value=checked_p, key=f"proj_{u['id']}_{pid}"):
                        selected_project_ids.append(pid)

            st.markdown("**Usuarios visibles en Configurar perfiles** *(si este usuario es admin)*:")
            st.caption("Selecciona qué correos puede ver y gestionar este administrador.")
            other_users = [x for x in all_users if x["id"] != u["id"] and not is_super_admin(x["id"])]
            try:
                import json as _json
                from db import UserPermission, get_session as _gs
                with _gs() as _s:
                    perm_rec = _s.query(UserPermission).filter_by(user_id=u["id"]).first()
                    current_managed = _json.loads(perm_rec.managed_user_ids) if perm_rec and perm_rec.managed_user_ids else None
            except Exception:
                current_managed = None

            all_managed = st.checkbox("Todos los usuarios",
                                      value=current_managed is None,
                                      key=f"am_{u['id']}")
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
                st.success(f"Permisos actualizados para {u['email']}")
                st.rerun()

        with st.expander("🔑 Restablecer contraseña"):
            with st.form(f"pwd_{u['id']}"):
                new_pwd = st.text_input("Nueva contraseña", type="password")
                if st.form_submit_button("Guardar contraseña", use_container_width=True):
                    if len(new_pwd) < 6:
                        st.error("Mínimo 6 caracteres.")
                    else:
                        set_password(u["id"], new_pwd)
                        st.success("Contraseña actualizada.")
