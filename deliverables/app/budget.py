"""Budget line CRUD, category totals, and over-budget detection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import func as sqlfunc

from db import BudgetLine, Category, Expense, Room, get_session


@dataclass
class CategoryTotal:
    code: str
    name: str
    level: int
    budgeted: float
    spent: float
    lines: list[dict] = field(default_factory=list)

    @property
    def balance(self) -> float:
        return self.budgeted - self.spent

    @property
    def over_budget(self) -> bool:
        return self.spent > self.budgeted and self.budgeted > 0


def get_budget_lines(project_id: int, room_id: Optional[int] = None) -> list[BudgetLine]:
    with get_session() as session:
        q = session.query(BudgetLine).filter_by(project_id=project_id)
        if room_id is not None:
            q = q.filter_by(room_id=room_id)
        return q.order_by(BudgetLine.category_code).all()


def create_budget_line(project_id: int, category_code: str, budgeted_amount: float,
                       description: str = "", room_id: Optional[int] = None) -> BudgetLine:
    with get_session() as session:
        line = BudgetLine(
            project_id=project_id,
            category_code=category_code,
            budgeted_amount=budgeted_amount,
            description=description.strip() or None,
            room_id=room_id,
        )
        session.add(line)
        session.flush()
        session.expunge(line)
        return line


def update_budget_line(line_id: int, project_id: int, budgeted_amount: float,
                       description: str = "", room_id: Optional[int] = None,
                       change_order_amount: Optional[float] = None,
                       contracted_amount: Optional[float] = None) -> bool:
    with get_session() as session:
        line = session.query(BudgetLine).filter_by(id=line_id, project_id=project_id).first()
        if not line:
            return False
        line.budgeted_amount = budgeted_amount
        line.description = description.strip() or None
        line.room_id = room_id
        if change_order_amount is not None:
            line.change_order_amount = change_order_amount
        if contracted_amount is not None:
            line.contracted_amount = contracted_amount
        return True


def delete_budget_line(line_id: int, project_id: int) -> bool:
    with get_session() as session:
        line = session.query(BudgetLine).filter_by(id=line_id, project_id=project_id).first()
        if not line:
            return False
        session.delete(line)
        return True


def get_category_totals(project_id: int) -> list[CategoryTotal]:
    with get_session() as session:
        rows = (
            session.query(
                BudgetLine.category_code,
                Category.name,
                Category.level,
                sqlfunc.sum(BudgetLine.budgeted_amount).label("budgeted"),
            )
            .join(Category, BudgetLine.category_code == Category.code)
            .filter(BudgetLine.project_id == project_id)
            .group_by(BudgetLine.category_code, Category.name, Category.level)
            .all()
        )

        totals: list[CategoryTotal] = []
        for row in rows:
            spent = (
                session.query(sqlfunc.sum(Expense.amount))
                .join(BudgetLine, Expense.budget_line_id == BudgetLine.id)
                .filter(BudgetLine.project_id == project_id, BudgetLine.category_code == row.category_code)
                .scalar()
            ) or 0.0
            totals.append(CategoryTotal(
                code=row.category_code,
                name=row.name,
                level=row.level,
                budgeted=float(row.budgeted),
                spent=float(spent),
            ))

    return sorted(totals, key=lambda x: x.code)


def get_all_categories() -> list[Category]:
    with get_session() as session:
        return session.query(Category).order_by(Category.code).all()
