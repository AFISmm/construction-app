"""
Updates the description of each valued Aspen budget line to use the exact
description text from Aspen_Preliminary_Budget.csv, keeping the original
category code prefix so the line is still identifiable.

Result format: "C.GC.1.14 - Temp chain-link fencing"

Run from the app directory:  python update_aspen_descriptions.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from db import BudgetLine, get_session

# Explicit mapping: budget_line_id -> CSV description (exact text from CSV file)
DESC_MAP: dict[int, str] = {
    1209: "Permits & Fees",
    1211: "Testing",
    1212: "Survey and Layout",
    1214: "Temporary utilities",
    1215: "Temporary heating (enclosures+diesel)",
    1217: "Equipment rental",
    1218: "Trailer rental",
    1219: "Safety & fire (communications)",
    1221: "Traffic control allowance",
    1222: "Temp chain-link fencing",
    1223: "Trash removal",
    1224: "Snow removal",
    1225: "Material storage",
    1226: "Samples",
    1228: "Crane",
    1229: "Protection",
    1231: "Miscellaneous expense",
    1232: "Blueprints",
    1233: "Contractor's contingency",
    1234: "Punchlist",
    1235: "Final clean & Duct Cleaning",
    1237: "Project superintendent",
    1238: "Working Foreman",
    1241: "House Deconstruction",
    1245: "Tree Removal and maintenance of existing",
    1246: "Site work labor",
    1247: "Soils Stabilization/Micro Pile Walls",
    1248: "Excavation",
    1253: "Utilities",
    1254: "Utility street cut and patching allowance",
    1255: "Topsoil",
    1256: "Noise Mitigation",
    1257: "Landscaping",
    1259: "Footings & Walls",
    1263: "Topping slabs",
    1267: "Concrete cutting allowance",
    1270: "Exterior wall stone veneer - labor & materials",
    1277: "Structural steel",
    1278: "Architectural steel - stair stringers and railings",
    1281: "Steel special inspections",
    1283: "Window Well Ladders and Grates",
    1284: "Misc. metals allowance",
    1287: "Rough framing materials",
    1288: "Rough framing labor",
    1289: "General carpentry",
    1293: "Soffit/ceiling material (wood)",
    1298: "Exterior siding materials - composite",
    1302: "Exterior House Wrap",
    1303: "Exterior Insulation",
    1307: "Interior trim labor",
    1314: "Foundation waterproofing and Insulation",
    1315: "Building insulation",
    1316: "Under slab Insulation",
    1318: "Deck waterproofing - horizontal surfaces",
    1319: "Membrane roof drains and ballast",
    1320: "Roofing Gutters and Downspouts",
    1321: "Heat tape systems",
    1323: "Roofing - metal fascia",
    1324: "Metal siding and chimney cap",
    1325: "Flashings",
    1327: "Interior doors material",
    1329: "Exterior Windows & Doors material",
    1330: "Window & Door Installation labor",
    1333: "Garage doors",
    1334: "Door hardware/cabinet pull material",
    1337: "Stucco",
    1338: "Drywall",
    1341: "Drywall - metal dropped ceiling",
    1342: "Drywall - patches",
    1343: "Plaster",
    1344: "Wall Finishes - Faux/Wallpaper/Fabric",
    1345: "Painting/staining - interior",
    1349: "Stone/tile - materials",
    1350: "Stone/tile - labor",
    1353: "Countertops - materials",
    1355: "Wood flooring labor",
    1356: "Wood stair tread materials",
    1358: "Wood flooring material allowance",
    1361: "Cabinetry and install",
    1364: "Fireplaces - Living Room",
    1365: "Firepit",
    1366: "Bath accessories - material",
    1368: "Glass",
    1369: "Mirrors",
    1370: "Shades",
    1373: "Appliances - material & install",
    1377: "Hot tub and Sauna",
    1379: "Radon systems",
    1380: "Fire protection systems",
    1383: "Elevators - passenger",
    1387: "Mechanical/HVAC",
    1388: "Oxygen",
    1389: "Boiler/radiant heating system",
    1390: "Gas piping",
    1391: "HVAC Controls and Test/Balance",
    1394: "Air conditioning systems",
    1396: "Roof and storm drains",
    1397: "Pipe Insulation",
    1398: "Plumbing",
    1399: "Plumbing fixtures",
    1400: "Water treatment",
    1402: "Electrical",
    1404: "Electrical fixtures - recessed",
    1410: "Switching systems - Lutron",
    1413: "Security/Burglary System",
    1414: "Audio/visual systems",
    1418: "City of Aspen Building Permit Fees",
    1424: "GL and Builders Risk Insurance",
}


def _code_prefix(current_description: str) -> str:
    """Extract the code part before ' - ' from the existing description."""
    if " - " in current_description:
        return current_description.split(" - ", 1)[0].strip()
    return current_description


def run() -> None:
    updated = 0
    with get_session() as session:
        for line_id, csv_desc in DESC_MAP.items():
            line = session.get(BudgetLine, line_id)
            if not line:
                print(f"  WARN: id={line_id} not found")
                continue
            code = _code_prefix(line.description or "")
            new_desc = f"{code} - {csv_desc}" if code else csv_desc
            line.description = new_desc
            updated += 1

    print(f"Updated {updated} budget line descriptions for Aspen.")
    print()

    # Print final state for verification
    with get_session() as session:
        lines = (
            session.query(BudgetLine)
            .filter(BudgetLine.project_id == 2, BudgetLine.budgeted_amount > 0)
            .order_by(BudgetLine.id)
            .all()
        )
        print(f"{'Description':<60}  {'Amount':>14}")
        print("-" * 78)
        total = 0.0
        for l in lines:
            amt = float(l.budgeted_amount)
            total += amt
            print(f"{l.description:<60}  {amt:>14,.2f}")
        print("-" * 78)
        print(f"{'TOTAL':<60}  {total:>14,.2f}")


if __name__ == "__main__":
    run()
