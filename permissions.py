"""User permissions: roles, page access, and project access."""
from __future__ import annotations

import json
from typing import Optional

import streamlit as st

from db import Project, User, UserPermission, get_session

ALL_PAGES = [
    "dashboard", "expenses", "import",
    "progress", "rooms", "account", "projects",
]

PAGE_FILES = {
    "dashboard":  "pages/dashboard.py",
    "expenses":   "pages/expenses.py",
    "import":     "pages/import_page.py",
    "progress":   "pages/progress.py",
    "rooms":      "pages/rooms.py",
    "account":    "pages/account.py",
    "projects":   "pages/project_list.py",
    "admin":      "pages/admin.py",
}


def get_permission(user_id: int) -> Optional[UserPermission]:
    with get_session() as session:
        return session.query(UserPermission).filter_by(user_id=user_id).first()


def is_super_admin(user_id: int) -> bool:
    """Only the configured super admin email has access to Configurar perfiles."""
    super_email = st.secrets.get("app", {}).get("super_admin_email", "").strip().lower()
    if not super_email:
        return False
    with get_session() as session:
        u = session.get(User, user_id)
        return bool(u and u.email == super_email)


def is_admin(user_id: int) -> bool:
    """Admins have full app access but NOT Configurar perfiles."""
    if is_super_admin(user_id):
        return True
    perm = get_permission(user_id)
    if perm is None:
        return True  # no record = full access
    return perm.role in ("admin", "super_admin")


def get_allowed_pages(user_id: int) -> list[str]:
    pages = ALL_PAGES[:]
    if is_super_admin(user_id):
        pages.append("admin")
    elif is_admin(user_id):
        perm = get_permission(user_id)
        if perm and perm.allowed_pages:
            pages = json.loads(perm.allowed_pages)
    else:
        perm = get_permission(user_id)
        if perm and perm.allowed_pages:
            pages = json.loads(perm.allowed_pages)
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
