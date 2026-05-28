"""SQLAlchemy 2.x models and session factory for the construction budget app."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from typing import Generator, Optional

import streamlit as st
from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey,
    Integer, Numeric, String, Text, create_engine, func,
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, Session, mapped_column,
    relationship, sessionmaker,
)

# ---------------------------------------------------------------------------
# Engine / session
# ---------------------------------------------------------------------------

_engine = None
_SessionLocal: sessionmaker | None = None


def _get_engine():
    global _engine
    if _engine is None:
        url = st.secrets["database"]["url"]
        _engine = create_engine(url, echo=False, pool_pre_ping=True)
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_get_engine(), expire_on_commit=False)
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    otp_tokens: Mapped[list[OtpToken]] = relationship(back_populates="user", cascade="all, delete-orphan")
    projects: Mapped[list[Project]] = relationship(back_populates="user", cascade="all, delete-orphan")


class OtpToken(Base):
    __tablename__ = "otp_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="otp_tokens")


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("project_type IN ('residential', 'commercial')", name="chk_project_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    project_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    currency: Mapped[str] = mapped_column(String(3), default="COP", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    user: Mapped[User] = relationship(back_populates="projects")
    rooms: Mapped[list[Room]] = relationship(back_populates="project", cascade="all, delete-orphan")
    budget_lines: Mapped[list[BudgetLine]] = relationship(back_populates="project", cascade="all, delete-orphan")
    expenses: Mapped[list[Expense]] = relationship(back_populates="project", cascade="all, delete-orphan")
    import_jobs: Mapped[list[ImportJob]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint("level IN (1, 2, 3)", name="chk_category_level"),
    )

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_code: Mapped[Optional[str]] = mapped_column(String(10), ForeignKey("categories.code"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    level: Mapped[int] = mapped_column(Integer, nullable=False)

    children: Mapped[list[Category]] = relationship(back_populates="parent")
    parent: Mapped[Optional[Category]] = relationship(back_populates="children", remote_side="Category.code")
    budget_lines: Mapped[list[BudgetLine]] = relationship(back_populates="category")


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="rooms")
    budget_lines: Mapped[list[BudgetLine]] = relationship(back_populates="room")


class BudgetLine(Base):
    __tablename__ = "budget_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    category_code: Mapped[str] = mapped_column(String(10), ForeignKey("categories.code"), nullable=False)
    room_id: Mapped[Optional[int]] = mapped_column(ForeignKey("rooms.id", ondelete="SET NULL"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    budgeted_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="budget_lines")
    category: Mapped[Category] = relationship(back_populates="budget_lines")
    room: Mapped[Optional[Room]] = relationship(back_populates="budget_lines")
    expenses: Mapped[list[Expense]] = relationship(back_populates="budget_line")


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    budget_line_id: Mapped[int] = mapped_column(ForeignKey("budget_lines.id", ondelete="RESTRICT"), nullable=False)
    vendor: Mapped[Optional[str]] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="expenses")
    budget_line: Mapped[BudgetLine] = relationship(back_populates="expenses")


class ImportJob(Base):
    __tablename__ = "import_jobs"
    __table_args__ = (
        CheckConstraint("status IN ('pending','partial','complete','failed')", name="chk_import_job_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matched_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unmatched_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    project: Mapped[Project] = relationship(back_populates="import_jobs")
    rows: Mapped[list[ImportRow]] = relationship(back_populates="job", cascade="all, delete-orphan")


class ImportRow(Base):
    __tablename__ = "import_rows"
    __table_args__ = (
        CheckConstraint("status IN ('pending','confirmed','skipped','overridden')", name="chk_import_row_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    import_job_id: Mapped[int] = mapped_column(ForeignKey("import_jobs.id", ondelete="CASCADE"), nullable=False)
    original_description: Mapped[str] = mapped_column(Text, nullable=False)
    original_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 2))
    matched_taxonomy_code: Mapped[Optional[str]] = mapped_column(String(10), ForeignKey("categories.code"))
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    override_code: Mapped[Optional[str]] = mapped_column(String(10), ForeignKey("categories.code"))
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    job: Mapped[ImportJob] = relationship(back_populates="rows")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)


# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

def init_db() -> None:
    Base.metadata.create_all(_get_engine())


_TAXONOMY_CODES: list[dict] = [
    # Level 1
    {"code": "01", "name": "Adquisicion del Bien", "parent_code": None, "level": 1, "description": "Costos de compra del inmueble"},
    {"code": "02", "name": "Costos Blandos", "parent_code": None, "level": 1, "description": "Honorarios profesionales y permisos"},
    {"code": "03", "name": "Presupuesto de Construccion", "parent_code": None, "level": 1, "description": "Obra civil y acabados"},
    {"code": "04", "name": "Costos de Tenencia", "parent_code": None, "level": 1, "description": "Impuestos y servicios durante construccion"},
    {"code": "05", "name": "Mobiliario y Decoracion", "parent_code": None, "level": 1, "description": "Muebles, equipos y decoracion"},
    {"code": "06", "name": "Detalle por Habitacion", "parent_code": None, "level": 1, "description": "Costos desglosados por espacio"},
    # Level 2 — 01
    {"code": "01.01", "name": "Precio de Compra", "parent_code": "01", "level": 2, "description": "Valor de adquisicion del inmueble"},
    {"code": "01.02", "name": "Costos de Cierre", "parent_code": "01", "level": 2, "description": "Escrituracion, registro e impuestos"},
    {"code": "01.03", "name": "Honorarios Legales de Adquisicion", "parent_code": "01", "level": 2, "description": "Abogados para cierre"},
    {"code": "01.04", "name": "Financiamiento de Compra", "parent_code": "01", "level": 2, "description": "Credito hipotecario o constructor"},
    {"code": "01.05", "name": "Debida Diligencia Pre-Compra", "parent_code": "01", "level": 2, "description": "Inspecciones y estudios"},
    # Level 3 — 01.02
    {"code": "01.02.01", "name": "Seguros de Titulo", "parent_code": "01.02", "level": 3, "description": "Prima seguro de titulo"},
    {"code": "01.02.02", "name": "Honorarios de Notaria y Registro", "parent_code": "01.02", "level": 3, "description": "Notaria y registro"},
    {"code": "01.02.03", "name": "Impuestos de Transferencia", "parent_code": "01.02", "level": 3, "description": "Timbre y derechos de registro"},
    # Level 3 — 01.04
    {"code": "01.04.01", "name": "Capital del Prestamo", "parent_code": "01.04", "level": 3, "description": "Monto principal desembolsado"},
    {"code": "01.04.02", "name": "Honorarios y Comisiones del Prestamo", "parent_code": "01.04", "level": 3, "description": "Originacion y legalización"},
    {"code": "01.04.03", "name": "Peritaje / Avaluo", "parent_code": "01.04", "level": 3, "description": "Avaluo comercial para banco"},
    {"code": "01.04.04", "name": "Reserva de Intereses", "parent_code": "01.04", "level": 3, "description": "Intereses pre-constituidos"},
    # Level 2 — 02
    {"code": "02.01", "name": "Diseno Arquitectonico", "parent_code": "02", "level": 2, "description": "Honorarios de arquitectura"},
    {"code": "02.02", "name": "Diseno Estructural", "parent_code": "02", "level": 2, "description": "Ingenieria estructural"},
    {"code": "02.03", "name": "Disenos de Instalaciones", "parent_code": "02", "level": 2, "description": "Hidraulico, electrico, mecanico"},
    {"code": "02.04", "name": "Diseno de Interiores", "parent_code": "02", "level": 2, "description": "Interiorismo y paisajismo"},
    {"code": "02.05", "name": "Tramites y Licencias", "parent_code": "02", "level": 2, "description": "Licencia de construccion y permisos"},
    {"code": "02.06", "name": "Gerencia de Proyecto", "parent_code": "02", "level": 2, "description": "Honorarios de gerencia o interventoria"},
    {"code": "02.07", "name": "Estudios Tecnicos", "parent_code": "02", "level": 2, "description": "Suelos, topografia, ambiental"},
    {"code": "02.08", "name": "Seguros de Construccion", "parent_code": "02", "level": 2, "description": "Polizas de obra"},
    # Level 2 — 03
    {"code": "03.01", "name": "Preliminares y Demolicion", "parent_code": "03", "level": 2, "description": "Descapote, demoliccion, cerramiento"},
    {"code": "03.02", "name": "Estructura", "parent_code": "03", "level": 2, "description": "Cimentacion, columnas, vigas, losas"},
    {"code": "03.03", "name": "Mamposteria y Muros", "parent_code": "03", "level": 2, "description": "Muros, divisiones, bloques"},
    {"code": "03.04", "name": "Cubierta y Fachada", "parent_code": "03", "level": 2, "description": "Tejados, impermeabilizacion, fachadas"},
    {"code": "03.05", "name": "Instalaciones Hidraulicas", "parent_code": "03", "level": 2, "description": "Fontaneria, tuberias, equipos"},
    {"code": "03.06", "name": "Instalaciones Electricas", "parent_code": "03", "level": 2, "description": "Red electrica, tableros, luminarias"},
    {"code": "03.07", "name": "Instalaciones Especiales", "parent_code": "03", "level": 2, "description": "Gas, datos, CCTV, domotica"},
    {"code": "03.08", "name": "Pisos y Revestimientos", "parent_code": "03", "level": 2, "description": "Baldosa, madera, enchapes"},
    {"code": "03.09", "name": "Cielos y Drywall", "parent_code": "03", "level": 2, "description": "Cielos rasos y divisiones en drywall"},
    {"code": "03.10", "name": "Carpinteria", "parent_code": "03", "level": 2, "description": "Puertas, ventanas, closets, cocina"},
    {"code": "03.11", "name": "Pintura y Acabados", "parent_code": "03", "level": 2, "description": "Pintura interior y exterior, estuco"},
    {"code": "03.12", "name": "Aparatos Sanitarios y Griferia", "parent_code": "03", "level": 2, "description": "Sanitarios, lavamanos, duchas, grifos"},
    # Level 2 — 04
    {"code": "04.01", "name": "Impuesto Predial", "parent_code": "04", "level": 2, "description": "Impuesto predial durante construccion"},
    {"code": "04.02", "name": "Servicios Publicos", "parent_code": "04", "level": 2, "description": "Agua, luz, gas durante obra"},
    {"code": "04.03", "name": "Seguridad y Vigilancia", "parent_code": "04", "level": 2, "description": "Guardas y monitoreo"},
    {"code": "04.04", "name": "Administracion de Propiedad Horizontal", "parent_code": "04", "level": 2, "description": "Cuotas de administracion"},
    # Level 2 — 05
    {"code": "05.01", "name": "Muebles", "parent_code": "05", "level": 2, "description": "Muebles de sala, comedor, alcobas"},
    {"code": "05.02", "name": "Textiles y Decoracion", "parent_code": "05", "level": 2, "description": "Cortinas, cojines, alfombras, cuadros"},
    {"code": "05.03", "name": "Electrodomesticos", "parent_code": "05", "level": 2, "description": "Nevera, estufa, lavadora, etc."},
    {"code": "05.04", "name": "Equipos de Tecnologia", "parent_code": "05", "level": 2, "description": "TV, sonido, equipos de computo"},
    {"code": "05.05", "name": "Iluminacion Decorativa", "parent_code": "05", "level": 2, "description": "Lamparas y luminarias de diseno"},
    {"code": "05.06", "name": "Obras de Arte y Accesorios", "parent_code": "05", "level": 2, "description": "Arte, espejos, plantas"},
    # Level 2 — 06
    {"code": "06.01", "name": "Sala", "parent_code": "06", "level": 2, "description": "Costos sala de estar"},
    {"code": "06.02", "name": "Comedor", "parent_code": "06", "level": 2, "description": "Costos comedor"},
    {"code": "06.03", "name": "Cocina", "parent_code": "06", "level": 2, "description": "Costos cocina"},
    {"code": "06.04", "name": "Alcoba Principal", "parent_code": "06", "level": 2, "description": "Costos alcoba principal"},
    {"code": "06.05", "name": "Alcobas Secundarias", "parent_code": "06", "level": 2, "description": "Costos alcobas secundarias"},
    {"code": "06.06", "name": "Banos", "parent_code": "06", "level": 2, "description": "Costos banos"},
    {"code": "06.07", "name": "Estudio", "parent_code": "06", "level": 2, "description": "Costos estudio u oficina"},
    {"code": "06.08", "name": "Zona de Servicio", "parent_code": "06", "level": 2, "description": "Costos zona de servicio"},
    {"code": "06.09", "name": "Garaje", "parent_code": "06", "level": 2, "description": "Costos garaje"},
    {"code": "06.10", "name": "Exteriores y Jardines", "parent_code": "06", "level": 2, "description": "Costos exteriores"},
    {"code": "06.11", "name": "Espacios Comerciales", "parent_code": "06", "level": 2, "description": "Costos locales y bodegas"},
    {"code": "06.12", "name": "Areas Comunes", "parent_code": "06", "level": 2, "description": "Costos areas comunes del conjunto"},
]


def seed_categories() -> None:
    with get_session() as session:
        for row in _TAXONOMY_CODES:
            existing = session.get(Category, row["code"])
            if not existing:
                session.add(Category(**row))
