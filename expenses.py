"""Expense CRUD and per-budget-line totals."""
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import func as sqlfunc

from db import BudgetLine, Expense, get_session


def get_expenses(project_id: int, budget_line_id: Optional[int] = None) -> list[Expense]:
    with get_session() as session:
        q = session.query(Expense).filter_by(project_id=project_id)
        if budget_line_id is not None:
            q = q.filter_by(budget_line_id=budget_line_id)
        return q.order_by(Expense.expense_date.desc()).all()


def create_expense(project_id: int, budget_line_id: int, amount: float,
                   expense_date: date, vendor: str = "", description: str = "",
                   notes: str = "") -> Expense:
    with get_session() as session:
        expense = Expense(
            project_id=project_id,
            budget_line_id=budget_line_id,
            amount=amount,
            expense_date=expense_date,
            vendor=vendor.strip() or None,
            description=description.strip() or None,
            notes=notes.strip() or None,
        )
        session.add(expense)
        session.flush()
        session.expunge(expense)
        return expense


def update_expense(expense_id: int, project_id: int, amount: float,
                   expense_date: date, vendor: str = "", description: str = "",
                   notes: str = "") -> bool:
    with get_session() as session:
        expense = session.query(Expense).filter_by(id=expense_id, project_id=project_id).first()
        if not expense:
            return False
        expense.amount = amount
        expense.expense_date = expense_date
        expense.vendor = vendor.strip() or None
        expense.description = description.strip() or None
        expense.notes = notes.strip() or None
        return True


def delete_expense(expense_id: int, project_id: int) -> bool:
    with get_session() as session:
        expense = session.query(Expense).filter_by(id=expense_id, project_id=project_id).first()
        if not expense:
            return False
        session.delete(expense)
        return True


def get_line_spent(budget_line_id: int) -> float:
    with get_session() as session:
        total = session.query(sqlfunc.sum(Expense.amount)).filter_by(budget_line_id=budget_line_id).scalar()
        return float(total) if total else 0.0


def get_budget_lines_for_project(project_id: int) -> list[BudgetLine]:
    with get_session() as session:
        return (
            session.query(BudgetLine)
            .filter_by(project_id=project_id)
            .order_by(BudgetLine.category_code)
            .all()
        )
