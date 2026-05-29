"""Admin panel — manage users, roles, and permissions."""
import streamlit as st

from auth import require_auth
from i18n import t
from permissions import (
    ALL_PAGES, PAGE_FILES, get_all_users_with_permissions,
    is_admin, save_permission,
)
from projects import get_user_projects

user = require_auth()

if not is_admin(user["id"]):
    st.error("Acceso restringido / Access restricted")
    st.stop()

st.title("👤 Administración de usuarios")
st.caption("Gestiona roles y permisos de acceso por usuario.")
st.divider()

all_projects = get_user_projects(user["id"])
project_options = {f"{p.name}": p.id for p in all_projects}

users = get_all_users_with_permissions()

PAGE_LABELS = {
    "dashboard":  "Inicio / Dashboard",
    "budget":     "Presupuesto / Budget",
    "expenses":   "Gastos / Expenses",
    "import":     "Importar / Import",
    "progress":   "Progreso / Progress",
    "rooms":      "Habitaciones / Rooms",
    "account":    "Mi cuenta / Account",
    "projects":   "Proyectos / Projects",
}

for u in users:
    is_self = u["id"] == user["id"]
    with st.expander(f"{'⭐ ' if u['role'] == 'admin' else '👤 '}{u['email']}" + (" (tú)" if is_self else "")):
        with st.form(key=f"perm_form_{u['id']}"):
            role = st.selectbox(
                "Rol",
                ["admin", "viewer"],
                index=0 if u["role"] == "admin" else 1,
                key=f"role_{u['id']}",
                disabled=is_self,
                help="Admin: acceso total. Viewer: acceso restringido.",
            )

            st.markdown("**Páginas visibles:**")
            current_pages = u["allowed_pages"] if u["allowed_pages"] is not None else ALL_PAGES
            selected_pages = []
            cols = st.columns(2)
            for i, page_key in enumerate(ALL_PAGES):
                label = PAGE_LABELS.get(page_key, page_key)
                checked = page_key in current_pages
                if cols[i % 2].checkbox(label, value=checked, key=f"page_{u['id']}_{page_key}", disabled=is_self):
                    selected_pages.append(page_key)

            st.markdown("**Proyectos visibles:**")
            current_proj_ids = u["allowed_project_ids"]
            all_proj = st.checkbox(
                "Todos los proyectos",
                value=current_proj_ids is None,
                key=f"allproj_{u['id']}",
                disabled=is_self,
            )
            selected_project_ids = None
            if not all_proj:
                selected_project_ids = []
                for pname, pid in project_options.items():
                    checked_p = current_proj_ids is not None and pid in current_proj_ids
                    if st.checkbox(pname, value=checked_p, key=f"proj_{u['id']}_{pid}", disabled=is_self):
                        selected_project_ids.append(pid)

            if not is_self:
                if st.form_submit_button("💾 Guardar permisos", use_container_width=True):
                    pages_to_save = None if role == "admin" else (selected_pages or ALL_PAGES)
                    proj_to_save = None if role == "admin" else selected_project_ids
                    save_permission(u["id"], role, pages_to_save, proj_to_save)
                    st.success(f"Permisos actualizados para {u['email']}")
                    st.rerun()
            else:
                st.caption("No puedes modificar tus propios permisos.")
