"""Progress reports: variance dataframe, chart data, CSV/Excel export."""
from __future__ import annotations

import io
from typing import Optional

import pandas as pd

from budget import get_category_totals
from i18n import t


def _cat_name(code: str, fallback: str) -> str:
    key = f"cat.{code}"
    translated = t(key)
    return translated if translated != key else fallback


def _fmt(value: float, currency: str = "") -> str:
    from i18n import fmt_money
    return fmt_money(value)


def build_variance_df(project_id: int, currency: str = "") -> pd.DataFrame:
    totals = get_category_totals(project_id)
    rows = []
    for ct in totals:
        pct = round((ct.spent / ct.budgeted * 100), 1) if ct.budgeted > 0 else 0.0
        rows.append({
            t("report.category_col"): f"{ct.code} {_cat_name(ct.code, ct.name)}",
            t("report.budgeted_col"): _fmt(ct.budgeted, currency),
            t("report.actual_col"):   _fmt(ct.spent, currency),
            t("report.variance_col"): _fmt(ct.balance, currency),
            t("report.pct_col"):      f"{pct:.1f}%",
            "_over_budget": ct.over_budget,
        })
    return pd.DataFrame(rows)


def export_csv(project_id: int) -> bytes:
    df = build_variance_df(project_id).drop(columns=["_over_budget"])
    return df.to_csv(index=False).encode("utf-8-sig")


def export_xlsx(project_id: int) -> bytes:
    df = build_variance_df(project_id).drop(columns=["_over_budget"])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Progreso")
    return buf.getvalue()


def export_pdf(project_id: int, project_name: str = "", currency: str = "") -> bytes:
    """Generate a professional PDF report with project summary and variance table."""
    import io as _io
    from datetime import datetime as _dt
    try:
        from reportlab.lib import colors as _colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate,
                                        Spacer, Table, TableStyle)
    except ImportError:
        # Fallback: return a plain CSV as bytes if reportlab is not installed
        return export_csv(project_id)

    from i18n import fmt_money as _fmt_money
    from projects import get_project_summary as _get_summary

    summary = _get_summary(project_id)
    buf = _io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    story = []
    styles = getSampleStyleSheet()

    ORANGE = _colors.HexColor("#e05a20")
    BLUE   = _colors.HexColor("#4fc3f7")
    DARK   = _colors.HexColor("#1a1a1a")
    LIGHT  = _colors.HexColor("#f5f5f5")

    title_style = ParagraphStyle(
        "rpt_title", parent=styles["Heading1"],
        fontSize=22, textColor=ORANGE, spaceAfter=6, alignment=1,
    )
    sub_style = ParagraphStyle(
        "rpt_sub", parent=styles["Normal"],
        fontSize=11, textColor=_colors.HexColor("#555555"),
        spaceAfter=4, alignment=1,
    )
    section_style = ParagraphStyle(
        "rpt_section", parent=styles["Heading2"],
        fontSize=13, textColor=DARK, spaceBefore=14, spaceAfter=6,
    )

    # Cover
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph(project_name or "Budget Report", title_style))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Budget Report", sub_style))
    story.append(Paragraph(_dt.now().strftime("%B %d, %Y"), sub_style))
    story.append(Spacer(1, 1.5 * inch))

    if summary:
        sum_data = [
            ["Metric", "Value"],
            ["Total Budget", _fmt_money(summary.total_budgeted)],
            ["Total Spent",  _fmt_money(summary.total_spent)],
            ["Balance",      _fmt_money(summary.balance)],
            ["% Executed",   f"{summary.pct_executed}%"],
        ]
        sum_table = Table(sum_data, colWidths=[3 * inch, 3 * inch])
        sum_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), BLUE),
            ("TEXTCOLOR",    (0, 0), (-1, 0), _colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 11),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, _colors.white]),
            ("GRID",         (0, 0), (-1, -1), 0.5, _colors.grey),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ]))
        story.append(Paragraph("Summary", section_style))
        story.append(sum_table)

    story.append(PageBreak())

    # Variance table
    df = build_variance_df(project_id, currency).drop(columns=["_over_budget"])
    if not df.empty:
        story.append(Paragraph("Budget Variance", section_style))
        var_data = [df.columns.tolist()] + df.values.tolist()
        col_count = len(df.columns)
        col_w = (7 * inch) / col_count
        var_table = Table(var_data, colWidths=[col_w] * col_count, repeatRows=1)
        row_styles = [
            ("BACKGROUND",   (0, 0), (-1, 0), ORANGE),
            ("TEXTCOLOR",    (0, 0), (-1, 0), _colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, -1), 8),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("GRID",         (0, 0), (-1, -1), 0.3, _colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHT, _colors.white]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ]
        var_table.setStyle(TableStyle(row_styles))
        story.append(var_table)

    doc.build(story)
    return buf.getvalue()


def get_budget_increase_pct(project_id: int) -> tuple[float | None, str]:
    """Return (pct_increase, label) comparing first vs latest budget version for the project.

    Returns (None, "") if no budgets or only one version exists.
    pct_increase is positive if cost grew, negative if it shrank.
    label is like "V1.0 → V2.3"
    """
    from budget_versioning import _parse_snapshot, get_budgets, get_versions
    budgets = get_budgets(project_id)
    if not budgets:
        return None, ""
    # Use the most recently created budget
    budget = budgets[0]
    versions = get_versions(budget.id)
    if len(versions) < 2:
        return None, ""
    # versions is ordered DESC — latest first, oldest last
    latest = versions[0]
    first = versions[-1]
    first_items = _parse_snapshot(first.snapshot_json)
    latest_items = _parse_snapshot(latest.snapshot_json)
    first_total = sum(r["budgeted_amount"] for r in first_items)
    latest_total = sum(r["budgeted_amount"] for r in latest_items)
    if first_total == 0:
        return None, ""
    pct = ((latest_total - first_total) / first_total) * 100
    label = f"V{first.version_label} → V{latest.version_label}"
    return round(pct, 1), label


def chart_data(project_id: int) -> pd.DataFrame:
    """Roll up budget/spent to level-1 categories. Returns long-format df for grouped bars."""
    totals = get_category_totals(project_id)
    level1: dict[str, dict] = {}
    for ct in totals:
        top_code = ct.code.split(".")[0]   # "01", "02", etc.
        if top_code not in level1:
            level1[top_code] = {t("report.planned"): 0.0, t("report.actual"): 0.0}
        level1[top_code][t("report.planned")] += ct.budgeted
        level1[top_code][t("report.actual")]  += ct.spent

    if not level1:
        return pd.DataFrame(columns=["Categoria", "Tipo", "Valor"])

    rows = []
    for code in sorted(level1.keys()):
        vals = level1[code]
        rows.append({"Categoria": code, "Tipo": t("report.planned"), "Valor": vals[t("report.planned")]})
        rows.append({"Categoria": code, "Tipo": t("report.actual"),  "Valor": vals[t("report.actual")]})
    return pd.DataFrame(rows)
