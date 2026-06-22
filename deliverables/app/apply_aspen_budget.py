"""
Applies Aspen Preliminary Budget amounts to project_id=2 (Aspen),
then replicates the 337-item master template (all $0) to all other
grouped projects so every project shares the same category structure.

Run from the app directory:  python apply_aspen_budget.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from db import BudgetLine, Project, get_session

# ---------------------------------------------------------------------------
# Explicit mapping: Aspen budget_line.id -> CSV amount
# (built by hand from Aspen_Preliminary_Budget.csv vs master list IDs)
# ---------------------------------------------------------------------------
AMOUNT_MAP: dict[int, float] = {
    1209: 5500,          # Permits & Fees
    1211: 2500,          # Testing
    1212: 20000,         # Survey and Layout
    1214: 17900,         # Temporary Utilities
    1215: 20000,         # Temporary Heating / Enclosures / Diesel
    1217: 135000,        # Equipment Rental
    1218: 10000,         # Trailer Rental
    1219: 850,           # Safety & Fire / Communications
    1221: 7500,          # Traffic Control Allowance
    1222: 52473,         # Temporary Chainlink Fencing
    1223: 36000,         # Trash Removal
    1224: 40000,         # Snow Removal
    1225: 10000,         # Material Storage
    1226: 5000,          # Samples / Mockups
    1228: 10000,         # Crane
    1229: 30000,         # Protection of Installed Work
    1231: 10000,         # Miscellaneous Expense
    1232: 2500,          # Blueprints
    1233: 500000,        # Contractor Contingency
    1234: 15000,         # Punchlist
    1235: 20000,         # Final Clean & Duct Cleaning
    1237: 375000,        # Project Superintendent
    1238: 250000,        # Site Foreman (Working Foreman)
    1241: 63050,         # House Deconstruction
    1245: 17275,         # Tree Removal and Maintenance
    1246: 90000,         # Site Work Labor
    1247: 305735,        # Soils Stabilization / Micro Pile Walls
    1248: 600286,        # Excavation
    1253: 20000,         # Utilities (Site Work)
    1254: 10000,         # Utility Street Cut and Patching
    1255: 7500,          # Topsoil
    1256: 50000,         # Noise Mitigation
    1257: 225000,        # Landscaping
    1259: 325000,        # Footings & Walls
    1263: 215000,        # Topping Slabs
    1267: 5000,          # Concrete Cutting Allowance
    1270: 400000,        # Exterior Wall Stone Veneer
    1277: 595924,        # Structural Steel
    1278: 125000,        # Architectural Steel / Stair Stringers / Railings
    1281: 15000,         # Steel Special Inspections
    1283: 45000,         # Window Well Ladders and Grates
    1284: 15000,         # Miscellaneous Metals
    1287: 425000,        # Rough Framing Materials
    1288: 435000,        # Rough Framing Labor
    1289: 125000,        # General Carpentry
    1293: 56000,         # Soffit / Ceiling Material
    1298: 35000,         # Exterior Siding Materials
    1302: 35000,         # Exterior House Wrap
    1303: 55000,         # Exterior Insulation
    1307: 265000,        # Interior Trim Labor
    1311: 750000,        # Cabinetry and Millwork
    1314: 174919,        # Foundation Waterproofing and Insulation
    1315: 122501,        # Building Insulation
    1316: 48500,         # Underslab Insulation
    1318: 80172,         # Deck Waterproofing / Horizontal Surfaces
    1319: 78003,         # Membrane, Roof Drains, and Ballast
    1320: 8690,          # Roofing, Gutters, and Downspouts
    1321: 26170,         # Heat Tape Systems
    1323: 20245,         # Roofing Metal Fascia
    1324: 31827,         # Metal Siding and Chimney Cap
    1325: 25000,         # Flashings
    1327: 125000,        # Interior Doors Material
    1329: 325000,        # Exterior Windows & Doors Material
    1330: 171000,        # Window & Door Installation Labor
    1333: 15000,         # Garage Doors
    1334: 48212.51,      # Door Hardware / Cabinet Pull Material
    1337: 15000,         # Stucco
    1338: 375000,        # Drywall
    1341: 78500,         # Drywall Metal Dropped Ceiling
    1342: 10000,         # Drywall Patches
    1343: 175000,        # Plaster
    1344: 35000,         # Wall Finishes / Faux / Wallpaper / Fabric
    1345: 175000,        # Painting / Staining Interior
    1349: 125000,        # Stone / Tile Materials
    1350: 85000,         # Stone / Tile Labor
    1353: 170000,        # Countertops Materials
    1355: 50000,         # Wood Flooring Labor
    1356: 50000,         # Wood Stair Tread Materials
    1358: 100000,        # Wood Flooring Material Allowance
    1361: 750000,        # Cabinetry and Install (Finishes)
    1364: 115520.93,     # Fireplaces
    1365: 10348.75,      # Firepit
    1366: 5000,          # Bath Accessories Material
    1368: 187030.31,     # Glass / Shower Enclosures / Railings
    1369: 14810.76,      # Mirrors
    1370: 60000,         # Shades
    1373: 168537.07,     # Appliances Material & Install
    1377: 60000,         # Hot Tub (and Sauna combined)
    1379: 15000,         # Radon Systems
    1380: 40016,         # Fire Protection Systems
    1383: 46985.82,      # Passenger Elevator
    1387: 714951,        # Mechanical / HVAC
    1388: 50000,         # Oxygen System
    1389: 203300,        # Boiler / Radiant Heating System
    1390: 27985,         # Gas Piping
    1391: 58000,         # HVAC Controls and Test / Balance
    1394: 232700,        # Air Conditioning Systems
    1396: 74870,         # Roof and Storm Drains
    1397: 25000,         # Pipe Insulation
    1398: 318163,        # Plumbing
    1399: 344750,        # Plumbing Fixtures
    1400: 10200,         # Water Treatment
    1402: 493213,        # Electrical (C.GC.15.1)
    1404: 430511.76,     # Electrical Fixtures Recessed
    1410: 160393.27,     # Switching Systems / Lutron
    1413: 34156.99,      # Security / Burglary System
    1414: 175000,        # Audio / Visual Systems
    1418: 1250000,       # Building Department Fees (City of Aspen)
    1424: 450000,        # Builder's Risk (GL and Builders Risk Insurance)
}

ASPEN_ID = 2


def update_aspen_amounts() -> int:
    """Apply CSV amounts to Aspen budget lines by ID. Returns count updated."""
    updated = 0
    with get_session() as session:
        for line_id, amount in AMOUNT_MAP.items():
            line = session.get(BudgetLine, line_id)
            if line and line.project_id == ASPEN_ID:
                line.budgeted_amount = amount
                updated += 1
            else:
                print(f"  WARN: line_id={line_id} not found or not in Aspen")
    return updated


def replicate_template_to_project(target_project_id: int, template_lines: list) -> int:
    """Replace all budget lines of target project with $0 copies of template."""
    with get_session() as session:
        deleted = session.query(BudgetLine).filter_by(project_id=target_project_id).delete()
        for tl in template_lines:
            session.add(BudgetLine(
                project_id=target_project_id,
                category_code=tl.category_code,
                description=tl.description,
                budgeted_amount=0,
                change_order_amount=0,
                contracted_amount=0,
            ))
    return deleted


def run() -> None:
    # 1) Update Aspen amounts
    n = update_aspen_amounts()
    print(f"Updated {n} Aspen budget lines with CSV amounts.")

    # 2) Get the Aspen template (337 lines) to copy to other projects
    with get_session() as session:
        template = (
            session.query(BudgetLine)
            .filter_by(project_id=ASPEN_ID)
            .order_by(BudgetLine.id)
            .all()
        )
        # Detach so they survive the session closing
        session.expunge_all()

    # 3) Find all grouped projects (those with a group_name) except Aspen
    with get_session() as session:
        others = (
            session.query(Project)
            .filter(Project.group_name.isnot(None))
            .filter(Project.id != ASPEN_ID)
            .all()
        )
        other_ids = [(p.id, p.name) for p in others]

    for pid, pname in other_ids:
        deleted = replicate_template_to_project(pid, template)
        print(f"Project '{pname}' (id={pid}): deleted {deleted} old lines, inserted {len(template)} template lines.")

    # Verify
    with get_session() as session:
        aspen_valued = session.query(BudgetLine).filter(
            BudgetLine.project_id == ASPEN_ID,
            BudgetLine.budgeted_amount > 0
        ).count()
        aspen_total = session.query(BudgetLine).filter_by(project_id=ASPEN_ID).count()
    print(f"Aspen: {aspen_total} total lines, {aspen_valued} with values > 0.")


if __name__ == "__main__":
    run()
