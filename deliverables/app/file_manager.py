"""File management: storage, keyword-based classification, and retrieval."""
from __future__ import annotations

from typing import Optional

from db import ProjectFile, get_session


MODULES: dict[str, str] = {
    "presupuesto": "Presupuesto",
    "gastos": "Gastos",
    "proveedores": "Proveedores",
    "general": "General del Proyecto",
    "trazabilidad": "Versiones / Auditoría",
    "sin_clasificar": "Sin clasificar",
}

_AUDIT_KW = ["auditoria", "version", "historial", "changelog", "audit", "revision", "track", "bitacora"]
_BUDGET_KW = ["budget", "presupuesto", "costo", "cost", "monto", "valor", "precio", "partida", "estimado", "apu"]
_EXPENSE_KW = ["factura", "invoice", "receipt", "recibo", "gasto", "pago", "comprobante", "egreso", "payment", "bill"]
_PROVIDER_KW = ["contrato", "contract", "acuerdo", "agreement", "proveedor", "vendor", "legal", "terminos", "terms", "poliza"]
_PLANS_KW = ["plano", "render", "especificacion", "specification", "memoria", "planta", "arquitecto", "diseno", "design", "topografia", "estudio"]
_PLANS_EXT = {"dwg", "dxf", "rvt", "skp", "ifc", "nwd"}


def classify_file_by_name(filename: str) -> str:
    """Return module key based on filename keywords and extension heuristics."""
    name = filename.lower()

    for kw in _AUDIT_KW:
        if kw in name:
            return "trazabilidad"
    for kw in _BUDGET_KW:
        if kw in name:
            return "presupuesto"
    for kw in _EXPENSE_KW:
        if kw in name:
            return "gastos"
    for kw in _PROVIDER_KW:
        if kw in name:
            return "proveedores"
    for kw in _PLANS_KW:
        if kw in name:
            return "general"

    ext = name.rsplit(".", 1)[-1] if "." in name else ""
    if ext in _PLANS_EXT:
        return "general"

    return "sin_clasificar"


def save_file(
    project_id: int,
    user_id: int,
    filename: str,
    file_data: bytes,
    content_type: str = "application/octet-stream",
    module: Optional[str] = None,
) -> ProjectFile:
    """Persist a file to the database and return the detached record."""
    if module is None:
        module = classify_file_by_name(filename)
    with get_session() as session:
        pf = ProjectFile(
            project_id=project_id,
            filename=filename,
            file_data=file_data,
            file_size=len(file_data),
            content_type=content_type or "application/octet-stream",
            module=module,
            uploaded_by=user_id,
        )
        session.add(pf)
        session.flush()
        session.expunge(pf)
        return pf


def get_project_files(project_id: int, module: Optional[str] = None) -> list[ProjectFile]:
    """Return files for a project, optionally filtered by module."""
    with get_session() as session:
        q = session.query(ProjectFile).filter_by(project_id=project_id)
        if module:
            q = q.filter_by(module=module)
        files = q.order_by(ProjectFile.uploaded_at.desc()).all()
        session.expunge_all()
        return files


def delete_file(file_id: int) -> bool:
    """Delete a file; return True if it existed."""
    with get_session() as session:
        pf = session.get(ProjectFile, file_id)
        if not pf:
            return False
        session.delete(pf)
        return True


def move_file(file_id: int, new_module: str) -> bool:
    """Reassign a file to a different module; return True if it existed."""
    with get_session() as session:
        pf = session.get(ProjectFile, file_id)
        if not pf:
            return False
        pf.module = new_module
        return True
