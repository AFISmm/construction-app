"""Admin panel — manage users, roles, and permissions."""
import streamlit as st

from auth import require_auth, set_password
from i18n import t
from permissions import ALL_PAGES, get_all_users_with_permissions, is_admin, save_permission
from projects import get_user_projects

user = require_auth()

if not is_admin(user["id"]):
    st.error("Acceso restringido / Access restricted")
    st.stop()

st.title(t("nav.admin"))
st.divider()

all_projects = get_user_projects(user["id"])
project_options = {p.name: p.id for p in all_projects}

PAGE_LABELS = {
    "dashboard": "Inicio",
    "import":    "Importar",
    "projects":  "Proyectos",
    "progress":  "Progreso",
    "expenses":  "Gastos",
    "rooms":     "Habitaciones",
    "account":   "Mi cuenta",
}

users = get_all_users_with_permissions()

for u in users:
    is_self = u["id"] == user["id"]
    icon = "⭐" if u["role"] == "admin" else "👤"
    label = f"{icon} {u['email']}" + (" (tú)" if is_self else "")

    with st.expander(label, expanded=False):
        if is_self:
            st.caption("No puedes modificar tus propios permisos.")
            continue

        with st.form(key=f"perm_{u['id']}"):
            role = st.selectbox(
                "Rol",
                ["admin", "viewer"],
                index=0 if u["role"] == "admin" else 1,
                help="Admin: acceso total + Configurar perfiles. Viewer: acceso restringido.",
            )

            st.markdown("**Páginas visibles** (solo aplica para Viewer):")
            current_pages = u["allowed_pages"] if u["allowed_pages"] is not None else list(PAGE_LABELS.keys())
            selected_pages = []
            cols = st.columns(2)
            for i, (key, label_p) in enumerate(PAGE_LABELS.items()):
                if cols[i % 2].checkbox(label_p, value=key in current_pages, key=f"p_{u['id']}_{key}"):
                    selected_pages.append(key)

            st.markdown("**Proyectos visibles** (solo aplica para Viewer):")
            all_proj = st.checkbox(
                "Todos los proyectos",
                value=u["allowed_project_ids"] is None,
                key=f"ap_{u['id']}",
            )
            selected_project_ids = None
            if not all_proj:
                selected_project_ids = []
                for pname, pid in project_options.items():
                    checked_p = u["allowed_project_ids"] is not None and pid in u["allowed_project_ids"]
                    if st.checkbox(pname, value=checked_p, key=f"proj_{u['id']}_{pid}"):
                        selected_project_ids.append(pid)

            if st.form_submit_button("💾 Guardar permisos", use_container_width=True):
                pages_to_save = None if role == "admin" else (selected_pages or list(PAGE_LABELS.keys()))
                proj_to_save = None if role == "admin" else selected_project_ids
                save_permission(u["id"], role, pages_to_save, proj_to_save)
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
