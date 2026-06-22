"""
One-time script: load all Aspen Master Cost List categories into project_id=2.
Maps Excel A/B/C/D/E taxonomy to portal category codes (01-06).
All amounts set to 0; description stores the original Excel item name.
Run from the app directory:  python import_aspen_categories.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

import openpyxl
from db import BudgetLine, get_session

EXCEL_PATH = r"C:\Users\FelipeIllidge\OneDrive - Mercury Methods Ltda\ProjectAspen\AspenProjectMasterCostList_GCFeeTrackingCHYas52626workingdocument.xlsx"
PROJECT_ID = 2

# ---------------------------------------------------------------------------
# Mapping: Excel item code prefix → portal category code
# ---------------------------------------------------------------------------
def _map_code(excel_code: str) -> str:
    """Return the best portal category code for an Excel item code."""
    c = excel_code.upper().strip()

    # ── A) House Purchase → 01 ──────────────────────────────────────────────
    if c in ("A", "A) HOUSE PURCHASE"):
        return "01"
    if c == "A.1":    return "01.01"
    if c in ("A.2", "A.4", "A.5"):  return "01.02"
    if c == "A.3":    return "01.03"
    if c == "A.6":    return "01.04"
    if c == "A.6.I":  return "01.04.01"
    if c == "A.6.II": return "01.04.02"
    if c == "A.6.III":return "01.04.03"
    if c.startswith("A."):  return "01.05"   # A.7-A.11 → Due Diligence

    # ── B) Soft Costs → 02 ──────────────────────────────────────────────────
    if c in ("B", "B) SOFT COSTS"):
        return "02"
    # two-digit B codes first (else "B.10" matches "B.1" before "B.10")
    if c.startswith("B.10"): return "02.03"  # MEP Engineering → Instalaciones
    if c.startswith("B.11"): return "02.07"  # Waterproofing Consultant
    if c.startswith("B.12"): return "02.07"  # Energy Consultant
    if c.startswith("B.13"): return "02.04"  # Lighting Design → Interiores
    if c.startswith("B.14"): return "02.03"  # Low Voltage/AV → Instalaciones
    if c.startswith("B.15"): return "02.04"  # Pool Design → Interiores
    if c.startswith("B.16"): return "02.07"  # Environmental → Estudios
    if c.startswith("B.17"): return "02.05"  # Permit Expeditor → Tramites
    if c.startswith("B.18"): return "02.06"  # Owner's Rep → Gerencia
    if c.startswith("B.19"): return "02.06"  # Accounting → Gerencia
    if c.startswith("B.20"): return "02.06"  # Printing → Gerencia
    if c.startswith("B.21"): return "02.07"  # Special Inspections → Estudios
    # single-digit B codes
    if c.startswith("B.1"):  return "02.01"  # Architect & Interior Design
    if c.startswith("B.2"):  return "02.05"  # Legal Fees → Tramites
    if c.startswith("B.3"):  return "02.04"  # Landscape Architect → Diseno
    if c == "B.4":            return "02.06"  # GC Pre-Construction → Gerencia
    if c.startswith("B.5"):  return "02.07"  # Soil Testing → Estudios
    if c.startswith("B.6"):  return "02.07"  # Surveyor → Estudios
    if c.startswith("B.7"):  return "02.07"  # Arborist → Estudios
    if c.startswith("B.8"):  return "02.02"  # Civil Engineer → Estructural
    if c.startswith("B.9"):  return "02.02"  # Structural Engineer
    if c.startswith("B."):   return "02"

    # ── C) Construction Budget → 03 ─────────────────────────────────────────
    if c in ("C", "C) CONSTRUCTION BUDGET"):
        return "03"
    if c in ("C.GC", "C.GC."):     return "03"
    if c in ("C.OD", "C.OD."):     return "03"

    # C.GC sub-sections — two-digit codes first to avoid "C.GC.1" swallowing C.GC.10-15
    if c.startswith("C.GC.10"):    return "03.09"   # Specialties → Cielos
    if c.startswith("C.GC.11"):    return "03.09"   # Equipment → Cielos (misc)
    if c.startswith("C.GC.12"):    return "03.07"   # Special Const → Especiales
    if c.startswith("C.GC.13"):    return "03.07"   # Conveying/Elevators
    if c.startswith("C.GC.14"):    return "03.05"   # Mechanical/HVAC → Hidraulicas
    if c.startswith("C.GC.15"):    return "03.06"   # Electrical
    # single-digit C.GC codes
    if c.startswith("C.GC.1"):     return "03.01"   # General Req → Preliminares
    if c.startswith("C.GC.2"):     return "03.01"   # Site Work → Preliminares
    if c.startswith("C.GC.3"):     return "03.02"   # Concrete → Estructura
    if c.startswith("C.GC.4"):     return "03.03"   # Masonry → Mamposteria
    if c.startswith("C.GC.5"):     return "03.02"   # Metals → Estructura
    if c.startswith("C.GC.6"):     return "03.10"   # Carpentry → Carpinteria
    if c.startswith("C.GC.7"):     return "03.04"   # Thermal/Moisture → Cubierta
    if c.startswith("C.GC.8"):     return "03.10"   # Doors & Windows → Carpinteria
    if c.startswith("C.GC.9"):     return "03.08"   # Finishes → Pisos

    # C.OD owner-direct items
    if c in ("C.OD.1", "C.OD.2", "C.OD.3", "C.OD.4"): return "02.05"  # Permits
    if c in ("C.OD.5", "C.OD.6"):   return "03.01"   # Abatement/Demo
    if c in ("C.OD.7", "C.OD.8", "C.OD.9", "C.OD.10"): return "02.08"  # Insurance
    if c.startswith("C.OD."):       return "03.01"   # Remaining OD items

    # ── D) Carrying Costs → 04 ──────────────────────────────────────────────
    if c in ("D", "D) CARRYING COSTS"):
        return "04"
    if c in ("D.1", "D.2", "D.3"):  return "01.04"  # Construction Loan → Financiamiento
    if c == "D.4":                   return "04.01"  # Property Taxes → Predial
    if c == "D.5":                   return "02.08"  # Property Insurance → Seguros
    if c in ("D.6", "D.7", "D.8", "D.9"): return "04.02"  # Utilities
    if c in ("D.10", "D.11"):        return "04.03"  # Security → Vigilancia
    if c.startswith("D."):           return "04.04"  # HOA/Housing/Admin

    # ── E) Furniture & Decor → 05 ───────────────────────────────────────────
    if c in ("E", "E) FURNITURE & DECOR"):
        return "05"
    if c in ("E.1", "E.2"):          return "05.01"  # Furniture
    if c == "E.3":                   return "05.05"  # Decorative Lighting
    if c in ("E.4", "E.5"):          return "05.02"  # Rugs/Textiles
    if c == "E.6":                   return "05.06"  # Art
    if c in ("E.7", "E.8"):          return "05.02"  # Bedding/Kitchenware
    if c in ("E.9", "E.10"):         return "05.06"  # BBQ/Accessories
    if c.startswith("E."):           return "05.01"  # All other E.* → Muebles

    return "03"  # fallback


def _extract(cell_value: str):
    """Return (code, description) from an Excel cell like 'A.1 � A) ... � Purchase Price'."""
    raw = str(cell_value).strip()
    # openpyxl reads the em-dash separator as � (replacement char)
    sep = " — "
    parts = [p.strip() for p in raw.split(sep)]
    code = parts[0]
    # Description = last segment (most specific name)
    name = parts[-1] if len(parts) > 1 else parts[0]
    # Build human-readable description: "A.1 - Purchase Price"
    desc = f"{code} - {name}" if name != code else code
    return code, desc


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=True)
    ws = wb["Master List"]

    lines_to_create = []
    for row in ws.iter_rows(values_only=True):
        cell = row[0]
        if cell is None:
            continue
        raw = str(cell).strip()
        if not raw or raw == "MASTER LIST ITEM":
            continue  # skip header row

        code, desc = _extract(raw)
        cat_code = _map_code(code)
        lines_to_create.append((cat_code, desc))

    print(f"Parsed {len(lines_to_create)} items from Excel.")

    with get_session() as session:
        # Delete ALL existing budget lines for Aspen
        deleted = session.query(BudgetLine).filter_by(project_id=PROJECT_ID).delete()
        print(f"Deleted {deleted} existing budget lines.")

        # Insert new lines
        for cat_code, desc in lines_to_create:
            session.add(BudgetLine(
                project_id=PROJECT_ID,
                category_code=cat_code,
                description=desc,
                budgeted_amount=0,
                change_order_amount=0,
                contracted_amount=0,
            ))

    print(f"OK: Inserted {len(lines_to_create)} budget lines for project_id={PROJECT_ID}.")


if __name__ == "__main__":
    run()
