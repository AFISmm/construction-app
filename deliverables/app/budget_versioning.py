"""Budget versioning, audit trail, and snapshot management."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from db import (Budget, BudgetAuditLog, BudgetLine, BudgetVersion,
                Category, get_session)

STATUSES = ["draft", "review", "approved", "rejected"]
STATUS_LABELS_ES = {
    "draft":    "Borrador",
    "review":   "En revisión",
    "approved": "Aprobado",
    "rejected": "Rechazado",
}
STATUS_LABELS_EN = {
    "draft":    "Draft",
    "review":   "In review",
    "approved": "Approved",
    "rejected": "Rejected",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _version_label(major: int, minor: int) -> str:
    return f"{major}.{minor}"


def _snapshot_from_lines(lines: list) -> str:
    """Serialize budget lines to JSON snapshot."""
    data = [
        {
            "category_code": bl.category_code,
            "description": bl.description or "",
            "budgeted_amount": float(bl.budgeted_amount),
            "room_id": bl.room_id,
        }
        for bl in lines
    ]
    return json.dumps(data, ensure_ascii=False)


def _snapshot_from_dict(rows: list[dict]) -> str:
    return json.dumps(rows, ensure_ascii=False)


def _parse_snapshot(snapshot_json: str) -> list[dict]:
    return json.loads(snapshot_json)


def _log(session, budget_id: int, action: str, version_id: Optional[int] = None,
         field: Optional[str] = None, old: Optional[str] = None,
         new: Optional[str] = None, notes: Optional[str] = None,
         user_id: Optional[int] = None) -> None:
    session.add(BudgetAuditLog(
        budget_id=budget_id,
        version_id=version_id,
        action=action,
        field_changed=field,
        old_value=str(old) if old is not None else None,
        new_value=str(new) if new is not None else None,
        notes=notes,
        user_id=user_id,
    ))


# ── CRUD ──────────────────────────────────────────────────────────────────────

def get_budgets(project_id: int) -> list[Budget]:
    with get_session() as session:
        return (session.query(Budget)
                .filter_by(project_id=project_id)
                .order_by(Budget.created_at.desc())
                .all())


def get_budget(budget_id: int) -> Optional[Budget]:
    with get_session() as session:
        return session.get(Budget, budget_id)


def create_budget(project_id: int, name: str, user_id: int) -> Budget:
    """Create a budget capturing a snapshot of current budget_lines."""
    with get_session() as session:
        lines = session.query(BudgetLine).filter_by(project_id=project_id).all()
        snapshot = _snapshot_from_lines(lines)

        budget = Budget(
            project_id=project_id,
            name=name,
            status="draft",
            version_major=1,
            version_minor=0,
            created_by=user_id,
            updated_by=user_id,
        )
        session.add(budget)
        session.flush()

        version = BudgetVersion(
            budget_id=budget.id,
            version_major=1,
            version_minor=0,
            version_label="1.0",
            change_type="major",
            change_description="Versión inicial",
            status="draft",
            snapshot_json=snapshot,
            created_by=user_id,
        )
        session.add(version)
        session.flush()

        _log(session, budget.id, "create", version.id,
             notes=f"Presupuesto '{name}' creado — V1.0", user_id=user_id)

        session.expunge(budget)
        return budget


def create_version(budget_id: int, change_type: str, description: str,
                   line_items: list[dict], user_id: int) -> BudgetVersion:
    """Create a new version with the provided line items as snapshot."""
    with get_session() as session:
        budget = session.get(Budget, budget_id)
        if not budget:
            raise ValueError(f"Budget {budget_id} not found")

        if change_type == "major":
            new_major = budget.version_major + 1
            new_minor = 0
        else:
            new_major = budget.version_major
            new_minor = budget.version_minor + 1

        label = _version_label(new_major, new_minor)
        old_label = _version_label(budget.version_major, budget.version_minor)

        snapshot = _snapshot_from_dict(line_items)
        version = BudgetVersion(
            budget_id=budget_id,
            version_major=new_major,
            version_minor=new_minor,
            version_label=label,
            change_type=change_type,
            change_description=description,
            status="draft",
            snapshot_json=snapshot,
            created_by=user_id,
        )
        session.add(version)
        session.flush()

        budget.version_major = new_major
        budget.version_minor = new_minor
        budget.status = "draft"
        budget.updated_by = user_id
        budget.updated_at = datetime.utcnow()

        _log(session, budget_id, "version_created", version.id,
             field="version", old=old_label, new=label,
             notes=description, user_id=user_id)

        session.expunge(version)
        return version


def change_status(budget_id: int, new_status: str, user_id: int,
                  notes: Optional[str] = None) -> None:
    with get_session() as session:
        budget = session.get(Budget, budget_id)
        if not budget:
            return
        old_status = budget.status
        budget.status = new_status
        budget.updated_by = user_id
        budget.updated_at = datetime.utcnow()

        # Also update current version status
        latest = (session.query(BudgetVersion)
                  .filter_by(budget_id=budget_id,
                             version_major=budget.version_major,
                             version_minor=budget.version_minor)
                  .first())
        if latest:
            latest.status = new_status

        _log(session, budget_id, "status_change",
             version_id=latest.id if latest else None,
             field="status", old=old_status, new=new_status,
             notes=notes, user_id=user_id)


def get_versions(budget_id: int) -> list[BudgetVersion]:
    with get_session() as session:
        return (session.query(BudgetVersion)
                .filter_by(budget_id=budget_id)
                .order_by(BudgetVersion.version_major.desc(),
                          BudgetVersion.version_minor.desc())
                .all())


def get_version(version_id: int) -> Optional[BudgetVersion]:
    with get_session() as session:
        return session.get(BudgetVersion, version_id)


def restore_version(budget_id: int, version_id: int, description: str,
                    user_id: int) -> BudgetVersion:
    """Create a new version from a previous snapshot (restore)."""
    with get_session() as session:
        old_v = session.get(BudgetVersion, version_id)
        if not old_v:
            raise ValueError(f"Version {version_id} not found")
        items = _parse_snapshot(old_v.snapshot_json)

    full_desc = f"Restaurado desde V{old_v.version_label}: {description}"
    new_v = create_version(budget_id, "major", full_desc, items, user_id)

    with get_session() as session:
        _log(session, budget_id, "restored",
             notes=f"Snapshot de V{old_v.version_label} restaurado como nueva versión",
             user_id=user_id)

    return new_v


def get_audit_log(budget_id: int) -> list[BudgetAuditLog]:
    with get_session() as session:
        return (session.query(BudgetAuditLog)
                .filter_by(budget_id=budget_id)
                .order_by(BudgetAuditLog.timestamp.desc())
                .all())


def compare_versions(version_id_a: int, version_id_b: int) -> list[dict]:
    """Return diff of two snapshots. Each item: {code, desc, val_a, val_b, changed}."""
    with get_session() as session:
        va = session.get(BudgetVersion, version_id_a)
        vb = session.get(BudgetVersion, version_id_b)
        if not va or not vb:
            return []

    rows_a = {r["category_code"]: r for r in _parse_snapshot(va.snapshot_json)}
    rows_b = {r["category_code"]: r for r in _parse_snapshot(vb.snapshot_json)}

    all_codes = sorted(set(rows_a) | set(rows_b))
    diff = []
    for code in all_codes:
        a = rows_a.get(code)
        b = rows_b.get(code)
        val_a = a["budgeted_amount"] if a else None
        val_b = b["budgeted_amount"] if b else None
        desc = (b or a).get("description", code)
        diff.append({
            "code": code,
            "description": desc,
            "val_a": val_a,
            "val_b": val_b,
            "changed": val_a != val_b,
            "added": a is None,
            "removed": b is None,
        })
    return diff


def get_user_email(user_id: Optional[int]) -> str:
    if not user_id:
        return "—"
    from db import User
    with get_session() as session:
        u = session.get(User, user_id)
        return u.email if u else f"#{user_id}"
