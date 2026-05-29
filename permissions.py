"""User permissions: roles, page access, and project access."""
from __future__ import annotations

import json
from typing import Optional

from db import Project, User, UserPermission, get_session

ALL_PAGES = [
    "dashboard", "budget", "expenses", "import",
    "progress", "rooms", "account", "projects",
]

PAGE_FILES = {
    "dashboard":  "pages/dashboard.py",
    "budget":     "pages/budget.py",
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


def is_admin(user_id: int) -> bool:
    perm = get_permission(user_id)
    if perm is None:
        return True  # no record = full access
    return perm.role == "admin"


def get_allowed_pages(user_id: int) -> list[str]:
    perm = get_permission(user_id)
    if perm is None or perm.allowed_pages is None:
        return ALL_PAGES + (["admin"] if is_admin(user_id) else [])
    pages = json.loads(perm.allowed_pages)
    if perm.role == "admin" and "admin" not in pages:
        pages.append("admin")
    return pages


def get_allowed_projects(user_id: int) -> list[int] | None:
    """Returns list of allowed project IDs, or None = all projects."""
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
                    allowed_project_ids: list[int] | None) -> None:
    with get_session() as session:
        perm = session.query(UserPermission).filter_by(user_id=user_id).first()
        pages_json = json.dumps(allowed_pages) if allowed_pages is not None else None
        projects_json = json.dumps(allowed_project_ids) if allowed_project_ids is not None else None
        if perm:
            perm.role = role
            perm.allowed_pages = pages_json
            perm.allowed_project_ids = projects_json
        else:
            session.add(UserPermission(
                user_id=user_id, role=role,
                allowed_pages=pages_json,
                allowed_project_ids=projects_json,
            ))


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
