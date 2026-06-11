"""User permissions: roles, page access, and project access."""
from __future__ import annotations

import json
from typing import Optional

import streamlit as st

from db import Project, User, UserPermission, get_session

ALL_PAGES = [
    "dashboard", "presupuesto", "expenses", "trazabilidad", "timeline",
    "proveedores", "account",
]

# Roles del sistema
INTERNAL_ROLES = [
    "coordinador_construccion",
    "coordinador_pagos",
    "gestor_permisos",
    "usuario_general",
]
EXTERNAL_ROLES = ["proveedor", "contratista"]
ALL_ROLES = ["admin"] + INTERNAL_ROLES + EXTERNAL_ROLES
ROLE_LABELS_ES = {
    "proveedor":                "Proveedor",
    "coordinador_construccion": "Coordinador de Construcción",
    "contratista":              "Contratista",
    "coordinador_pagos":        "Coordinador de Pagos",
    "gestor_permisos":          "Gestor de Permisos",
    "usuario_general":          "Usuario General",
    "admin":                    "Administrador",
    "super_admin":              "Super Administrador",
    "pending":                  "Pendiente",
    "pending_extended":         "Registro pendiente",
    "rejected":                 "Rechazado",
}
ROLE_LABELS_EN = {
    "proveedor":                "Vendor",
    "coordinador_construccion": "Construction Coordinator",
    "contratista":              "Contractor",
    "coordinador_pagos":        "Payments Coordinator",
    "gestor_permisos":          "Permits Manager",
    "usuario_general":          "General User",
    "admin":                    "Administrator",
    "super_admin":              "Super Administrator",
    "pending":                  "Pending",
    "pending_extended":         "Registration pending",
    "rejected":                 "Rejected",
}

PAGE_FILES = {
    "dashboard":    "pages/dashboard.py",
    "presupuesto":  "pages/presupuesto.py",
    "expenses":     "pages/expenses.py",
    "trazabilidad": "pages/trazabilidad.py",
    "timeline":     "pages/timeline.py",
    "proveedores":  "pages/proveedores.py",
    "account":      "pages/account.py",
    "admin":        "pages/admin.py",
}


def is_pending(user_id: int) -> bool:
    """True if user is registered but not yet approved by super admin."""
    perm = get_permission(user_id)
    return perm is not None and perm.role in ("pending", "rejected", "pending_extended")


def is_pending_extended(user_id: int) -> bool:
    """True if user was approved as vendor/contractor and must fill the extended form."""
    perm = get_permission(user_id)
    return perm is not None and perm.role == "pending_extended"


def is_external_role(role: str) -> bool:
    """True if the given role belongs to the external category."""
    return role in EXTERNAL_ROLES


def get_pending_users() -> list[dict]:
    """Return all users waiting for approval."""
    with get_session() as session:
        perms = session.query(UserPermission).filter_by(role="pending").all()
        result = []
        for p in perms:
            u = session.get(User, p.user_id)
            if u:
                result.append({"id": u.id, "email": u.email})
        return result


def get_pending_count() -> int:
    with get_session() as session:
        return session.query(UserPermission).filter_by(role="pending").count()


def get_permission(user_id: int) -> Optional[UserPermission]:
    with get_session() as session:
        return session.query(UserPermission).filter_by(user_id=user_id).first()


def is_super_admin(user_id: int) -> bool:
    """Only the configured super admin email has access to Configurar perfiles.
    Falls back to: user with no permission record (original full-access default)."""
    super_email = st.secrets.get("app", {}).get("super_admin_email", "").strip().lower()
    with get_session() as session:
        u = session.get(User, user_id)
        if not u:
            return False
        # Match configured email
        if super_email and u.email.strip().lower() == super_email:
            return True
        # Fallback: if no super_admin_email configured, user with no permission record is super admin
        if not super_email:
            perm = session.query(UserPermission).filter_by(user_id=user_id).first()
            return perm is None
    return False


VIEWER_DEFAULT_PAGES = ["dashboard", "presupuesto", "expenses", "trazabilidad", "timeline", "account"]


def is_viewer(user_id: int) -> bool:
    """True if user has any non-admin, non-pending role (i.e., a restricted active user)."""
    if is_super_admin(user_id):
        return False
    perm = get_permission(user_id)
    if perm is None:
        return False
    return perm.role not in ("admin", "super_admin", "pending", "rejected", "pending_extended")


def can_edit_trazabilidad(user_id: int) -> bool:
    """True if user can create versions / change status in Trazabilidad."""
    if is_super_admin(user_id):
        return True
    perm = get_permission(user_id)
    if perm is None:
        return True
    pages = json.loads(perm.allowed_pages) if perm.allowed_pages else []
    return "trazabilidad_edit" in pages


def is_admin(user_id: int) -> bool:
    """Admins have full app access but NOT Configurar perfiles."""
    if is_super_admin(user_id):
        return True
    perm = get_permission(user_id)
    if perm is None:
        return True  # no record = full access
    return perm.role in ("admin", "super_admin")


def get_allowed_pages(user_id: int) -> list[str]:
    if is_super_admin(user_id):
        return ALL_PAGES + ["admin"]
    perm = get_permission(user_id)
    if perm is None:
        return ALL_PAGES  # no record = full access, but not super admin
    pages = json.loads(perm.allowed_pages) if perm.allowed_pages else ALL_PAGES[:]
    return pages
    return pages


def get_allowed_projects(user_id: int) -> list[int] | None:
    perm = get_permission(user_id)
    if perm is None or perm.allowed_project_ids is None:
        return None
    return json.loads(perm.allowed_project_ids)


def get_visible_projects(user_id: int) -> list:
    allowed = get_allowed_projects(user_id)
    with get_session() as session:
        q = session.query(Project).order_by(Project.created_at.desc())
        if allowed is not None:
            q = q.filter(Project.id.in_(allowed))
        return q.all()


def save_permission(user_id: int, role: str,
                    allowed_pages: list[str] | None,
                    allowed_project_ids: list[int] | None,
                    managed_user_ids: list[int] | None = None) -> None:
    with get_session() as session:
        perm = session.query(UserPermission).filter_by(user_id=user_id).first()
        pages_json    = json.dumps(allowed_pages)       if allowed_pages       is not None else None
        projects_json = json.dumps(allowed_project_ids) if allowed_project_ids is not None else None
        managed_json  = json.dumps(managed_user_ids)    if managed_user_ids    is not None else None
        if perm:
            perm.role = role
            perm.allowed_pages = pages_json
            perm.allowed_project_ids = projects_json
            perm.managed_user_ids = managed_json
        else:
            session.add(UserPermission(
                user_id=user_id, role=role,
                allowed_pages=pages_json,
                allowed_project_ids=projects_json,
                managed_user_ids=managed_json,
            ))


def get_managed_users(user_id: int, all_users: list[dict]) -> list[dict]:
    """Return the users visible to this admin in Configurar perfiles."""
    if is_super_admin(user_id):
        return all_users
    perm = get_permission(user_id)
    if perm is None:
        return []
    try:
        managed = json.loads(getattr(perm, 'managed_user_ids', None) or '[]')
        return [u for u in all_users if u["id"] in managed]
    except Exception:
        return []


def get_budget_approver_email() -> str | None:
    """Return email of the designated budget approver, or None if not set."""
    with get_session() as session:
        perm = session.query(UserPermission).filter_by(is_budget_approver=True).first()
        if not perm:
            return None
        u = session.get(User, perm.user_id)
        return u.email if u else None


def set_budget_approver(user_id: int | None) -> None:
    """Set one user as budget approver; clears all others. Pass None to clear."""
    with get_session() as session:
        session.query(UserPermission).update({"is_budget_approver": False})
        if user_id is not None:
            perm = session.query(UserPermission).filter_by(user_id=user_id).first()
            if perm:
                perm.is_budget_approver = True


def get_all_users_with_permissions() -> list[dict]:
    with get_session() as session:
        users = session.query(User).order_by(User.id).all()
        perms = {p.user_id: p for p in session.query(UserPermission).all()}
        result = []
        for u in users:
            p = perms.get(u.id)
            result.append({
                "id": u.id,
                "email": u.email,
                "role": p.role if p else "admin",
                "allowed_pages": json.loads(p.allowed_pages) if p and p.allowed_pages else None,
                "allowed_project_ids": json.loads(p.allowed_project_ids) if p and p.allowed_project_ids else None,
            })
        return result
