"""Vendor / Proveedor CRUD operations."""
from __future__ import annotations

from typing import Optional

from db import Vendor, get_session


def create_vendor(
    project_id: int,
    company_name: str,
    contact_name: str = "",
    phone: str = "",
    email: str = "",
    trade: str = "",
    nit: str = "",
    status: str = "pending",
    notes: str = "",
    source_file_id: Optional[int] = None,
) -> Vendor:
    with get_session() as session:
        v = Vendor(
            project_id=project_id,
            company_name=company_name.strip(),
            contact_name=contact_name.strip() or None,
            phone=phone.strip() or None,
            email=email.strip() or None,
            trade=trade.strip() or None,
            nit=nit.strip() or None,
            status=status,
            notes=notes.strip() or None,
            source_file_id=source_file_id,
        )
        session.add(v)
        session.flush()
        return v


def get_vendors(project_id: int) -> list[Vendor]:
    with get_session() as session:
        return (
            session.query(Vendor)
            .filter_by(project_id=project_id)
            .order_by(Vendor.company_name)
            .all()
        )


def get_vendor(vendor_id: int) -> Optional[Vendor]:
    with get_session() as session:
        return session.get(Vendor, vendor_id)


def update_vendor(vendor_id: int, **kwargs) -> bool:
    with get_session() as session:
        v = session.get(Vendor, vendor_id)
        if not v:
            return False
        for field, value in kwargs.items():
            if hasattr(v, field):
                setattr(v, field, value or None if isinstance(value, str) else value)
        return True


def delete_vendor(vendor_id: int) -> bool:
    with get_session() as session:
        v = session.get(Vendor, vendor_id)
        if not v:
            return False
        session.delete(v)
        return True


def vendor_exists_from_file(project_id: int, file_id: int) -> bool:
    with get_session() as session:
        return (
            session.query(Vendor)
            .filter_by(project_id=project_id, source_file_id=file_id)
            .first()
        ) is not None
