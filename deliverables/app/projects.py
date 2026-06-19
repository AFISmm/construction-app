"""Project CRUD and project-switcher logic."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import streamlit as st

from db import Project, get_session


@dataclass
class ProjectSummary:
    id: int
    name: str
    project_type: str
    currency: str
    total_budgeted: float
    total_spent: float

    @property
    def balance(self) -> float:
        return self.total_budgeted - self.total_spent

    @property
    def pct_executed(self) -> float:
        if self.total_budgeted == 0:
            return 0.0
        return round((self.total_spent / self.total_budgeted) * 100, 1)


def get_user_projects(user_id: int) -> list[Project]:
    with get_session() as session:
        return session.query(Project).order_by(Project.created_at.desc()).all()


def get_project(project_id: int, user_id: int) -> Optional[Project]:
    with get_session() as session:
        return session.query(Project).filter_by(id=project_id).first()


def create_project(user_id: int, name: str, project_type: str, description: str = "", currency: str = "COP") -> Project:
    with get_session() as session:
        project = Project(user_id=user_id, name=name.strip(), project_type=project_type,
                          description=description.strip() or None, currency=currency)
        session.add(project)
        session.flush()
        session.expunge(project)
        return project


def update_project(project_id: int, user_id: int, name: str, project_type: str,
                   description: str = "", currency: str = "COP") -> bool:
    with get_session() as session:
        project = session.query(Project).filter_by(id=project_id, user_id=user_id).first()
        if not project:
            return False
        project.name = name.strip()
        project.project_type = project_type
        project.description = description.strip() or None
        project.currency = currency
        return True


def delete_project(project_id: int, user_id: int) -> bool:
    with get_session() as session:
        project = session.query(Project).filter_by(id=project_id, user_id=user_id).first()
        if not project:
            return False
        session.delete(project)
        return True


def get_project_summary(project_id: int) -> Optional[ProjectSummary]:
    from sqlalchemy import func as sqlfunc
    from db import BudgetLine, Expense

    with get_session() as session:
        project = session.get(Project, project_id)
        if not project:
            return None

        budgeted = session.query(sqlfunc.sum(BudgetLine.budgeted_amount)).filter_by(project_id=project_id).scalar() or 0.0
        spent = session.query(sqlfunc.sum(Expense.amount)).filter_by(project_id=project_id).scalar() or 0.0

        return ProjectSummary(
            id=project.id,
            name=project.name,
            project_type=project.project_type,
            currency=project.currency,
            total_budgeted=float(budgeted),
            total_spent=float(spent),
        )


@st.dialog("➕ Agregar Proyecto")
def _add_project_dialog(user_id: int) -> None:
    """Modal form for creating a new project."""
    from db import User, UserPermission, get_session as _gs
    import json as _json

    # --- Group ---
    _existing_groups = []
    with __import__("db").get_session() as _sg:
        rows = _sg.execute(__import__("sqlalchemy").text(
            "SELECT DISTINCT group_name FROM projects WHERE group_name IS NOT NULL ORDER BY group_name"
        )).fetchall()
        _existing_groups = [r[0] for r in rows]
    group_opts = _existing_groups + ["➕ Nuevo grupo..."]
    _sel_grp = st.selectbox("Grupo *", group_opts, key="_np_grp")
    if _sel_grp == "➕ Nuevo grupo...":
        group_name = st.text_input("Nombre del nuevo grupo *", placeholder="Ej: Maria González")
    else:
        group_name = _sel_grp

    # --- Project name ---
    name = st.text_input("Nombre del proyecto *", placeholder="Ej: Edificio Central")

    # --- Administrator dropdown (approved users only) ---
    with _gs() as _s:
        approved_emails: list[str] = []
        for perm in _s.query(UserPermission).all():
            if perm.role not in ("pending", "pending_extended", "rejected"):
                u = _s.get(User, perm.user_id)
                if u:
                    approved_emails.append(u.email)

    admin_options = ["— seleccionar —"] + sorted(approved_emails)
    admin_email = st.selectbox("Administrador *", admin_options)

    # --- Project type ---
    ptype_label = st.radio(
        "Tipo de proyecto *",
        ["Residencial", "Comercial"],
        horizontal=True,
    )
    ptype = "residential" if ptype_label == "Residencial" else "commercial"

    # --- File upload ---
    uploaded_files = st.file_uploader(
        "Adjuntar archivos (opcional — acepta cualquier formato)",
        accept_multiple_files=True,
        key="_new_proj_files",
    )

    # Show pending files
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} archivo(s) adjunto(s):**")
        for f in uploaded_files:
            size_kb = round(len(f.getvalue()) / 1024, 1)
            st.markdown(f"- 📄 `{f.name}` ({size_kb} KB)")

    st.markdown("---")
    col_save, col_cancel = st.columns(2)

    if col_cancel.button("Cancelar", use_container_width=True, key="_np_cancel"):
        st.rerun()

    if col_save.button("💾 Guardar", type="primary", use_container_width=True, key="_np_save"):
        errors: list[str] = []
        if not group_name.strip():
            errors.append("⛔ El grupo es obligatorio.")
        if not name.strip():
            errors.append("⛔ El nombre del proyecto es obligatorio.")
        if admin_email == "— seleccionar —":
            errors.append("⛔ Debes seleccionar un administrador.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            # Create project
            new_proj = create_project(user_id, name.strip(), ptype)

            # Set admin_user_id and group_name
            with _gs() as _s:
                p = _s.get(Project, new_proj.id)
                if p:
                    p.group_name = group_name.strip()
                    u_admin = _s.query(User).filter_by(email=admin_email).first()
                    if u_admin:
                        p.admin_user_id = u_admin.id

            # Save and classify files
            if uploaded_files:
                from file_manager import classify_file_by_name, save_file, MODULES
                classifications: list[dict] = []
                for f in uploaded_files:
                    data = f.getvalue()
                    module = classify_file_by_name(f.name)
                    save_file(new_proj.id, user_id, f.name, data, f.type or "application/octet-stream", module)
                    classifications.append({"filename": f.name, "module": MODULES.get(module, module)})
                st.session_state["_classify_summary"] = classifications

            st.session_state["current_project_id"] = new_proj.id
            st.success(f"✅ Proyecto **{name.strip()}** creado exitosamente.")
            if uploaded_files:
                st.info("Los archivos fueron clasificados automáticamente. Puedes moverlos desde el módulo correspondiente.")
            st.rerun()


def project_selector_sidebar(user_id: int) -> Optional[int]:
    from i18n import t
    from permissions import get_visible_projects

    projects = get_visible_projects(user_id)

    # Show file-classification summary after project creation
    if st.session_state.get("_classify_summary"):
        summary = st.session_state.pop("_classify_summary")
        with st.sidebar:
            with st.expander("📁 Archivos clasificados", expanded=True):
                st.markdown("**Clasificación automática:**")
                for item in summary:
                    st.markdown(f"- `{item['filename']}` → **{item['module']}**")
                st.caption("Puedes mover archivos manualmente desde el módulo correspondiente.")

    # Split projects into grouped and ungrouped
    grouped: dict[str, list] = {}   # group_name → [Project]
    for p in projects:
        g = getattr(p, "group_name", None) or ""
        if g:
            grouped.setdefault(g, []).append(p)

    if not grouped:
        st.sidebar.caption(t("project.no_projects"))
        if st.sidebar.button("➕ Agregar proyecto", key="_add_proj_btn_empty",
                             use_container_width=True):
            _add_project_dialog(user_id)
        return None

    # ── Level 1: group selector ──────────────────────────────────────────────
    group_names = sorted(grouped.keys())
    current_id  = st.session_state.get("current_project_id")

    # Determine which group the current project belongs to
    current_group = group_names[0]
    for g, projs in grouped.items():
        if any(p.id == current_id for p in projs):
            current_group = g
            break

    selected_group = st.sidebar.selectbox(
        "Grupos",
        group_names,
        index=group_names.index(current_group),
        key="_group_selector",
    )

    # ── Level 2: project selector within group ───────────────────────────────
    group_projects = sorted(grouped[selected_group], key=lambda p: p.name)
    proj_names = [p.name for p in group_projects]

    # Default: first project in group, or the already-selected one if it's in this group
    default_proj_name = proj_names[0]
    for p in group_projects:
        if p.id == current_id:
            default_proj_name = p.name
            break

    selected_proj_name = st.sidebar.selectbox(
        selected_group,             # label = group name acts as sub-header
        proj_names,
        index=proj_names.index(default_proj_name),
        key=f"_proj_selector_{selected_group}",
    )

    selected_id = next(p.id for p in group_projects if p.name == selected_proj_name)

    if selected_id != st.session_state.get("current_project_id"):
        st.session_state["current_project_id"] = selected_id
        st.rerun()

    if st.sidebar.button("➕ Agregar proyecto", key="_add_proj_btn",
                         use_container_width=True):
        _add_project_dialog(user_id)

    return selected_id
