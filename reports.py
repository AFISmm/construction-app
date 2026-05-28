"""Progress reports: variance dataframe, chart data, CSV/Excel export."""
from __future__ import annotations

import io
from typing import TYPE_CHECKING

import pandas as pd

from budget import get_category_totals
from i18n import t

if TYPE_CHECKING:
    from .projects import ProjectSummary


def build_variance_df(project_id: int) -> pd.DataFrame:
    totals = get_category_totals(project_id)
    rows = []
    for ct in totals:
        pct = round((ct.spent / ct.budgeted * 100), 1) if ct.budgeted > 0 else 0.0
        rows.append({
            t("report.category_col"): f"{ct.code} {ct.name}",
            t("report.budgeted_col"): ct.budgeted,
            t("report.actual_col"): ct.spent,
            t("report.variance_col"): ct.balance,
            t("report.pct_col"): pct,
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
    totals = get_category_totals(project_id)
    rows = [{"Categoria": ct.code, t("report.planned"): ct.budgeted, t("report.actual"): ct.spent}
            for ct in totals if ct.level == 1]
    if not rows:
        return pd.DataFrame(columns=["Categoria", t("report.planned"), t("report.actual")]).set_index("Categoria")
    return pd.DataFrame(rows).set_index("Categoria")
