"""Progress reports: variance dataframe, chart data, CSV/Excel export."""
from __future__ import annotations

import io
from typing import Optional

import pandas as pd

from budget import get_category_totals
from i18n import t


def _fmt(value: float, currency: str = "") -> str:
    """Format a currency value with 2 decimals: US$1,234.56"""
    prefix = f"{currency}$" if currency and currency.upper() != "COP" else (f"{currency} " if currency else "")
    return f"{prefix}{value:,.2f}"


def build_variance_df(project_id: int, currency: str = "") -> pd.DataFrame:
    totals = get_category_totals(project_id)
    rows = []
    for ct in totals:
        pct = round((ct.spent / ct.budgeted * 100), 1) if ct.budgeted > 0 else 0.0
        rows.append({
            t("report.category_col"): f"{ct.code} {ct.name}",
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


def chart_data(project_id: int) -> pd.DataFrame:
    """Roll up budget/spent to level-1 categories for the bar chart."""
    totals = get_category_totals(project_id)
    level1: dict[str, dict] = {}
    for ct in totals:
        top_code = ct.code.split(".")[0]
        label = t(f"cat.{top_code}")
        if label == f"cat.{top_code}":
            label = top_code
        key = f"{top_code} — {label}"
        if key not in level1:
            level1[key] = {t("report.planned"): 0.0, t("report.actual"): 0.0}
        level1[key][t("report.planned")] += ct.budgeted
        level1[key][t("report.actual")]  += ct.spent

    if not level1:
        return pd.DataFrame(
            columns=["Categoria", t("report.planned"), t("report.actual")]
        ).set_index("Categoria")

    rows = [{"Categoria": k, **v} for k, v in sorted(level1.items())]
    return pd.DataFrame(rows).set_index("Categoria")
