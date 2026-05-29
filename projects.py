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


def project_selector_sidebar(user_id: int) -> Optional[int]:
    from i18n import t
    from permissions import get_visible_projects

    projects = get_visible_projects(user_id)
    if not projects:
        st.sidebar.caption(t("project.no_projects"))
        return None

    options = {p.name: p.id for p in projects}
    current_id = st.session_state.get("current_project_id")
    current_name = next((p.name for p in projects if p.id == current_id), projects[0].name)

    selected_name = st.sidebar.selectbox(
        t("project.selector_label"),
        list(options.keys()),
        index=list(options.keys()).index(current_name),
        key="_project_selector",
    )
    selected_id = options[selected_name]

    if selected_id != st.session_state.get("current_project_id"):
        st.session_state["current_project_id"] = selected_id
        st.rerun()

    return selected_id
