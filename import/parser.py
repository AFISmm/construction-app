"""File parsing: type validation, size enforcement, column auto-detection, row extraction."""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Optional

import pandas as pd
import streamlit as st

from app.i18n import t

ACCEPTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}
ACCEPTED_MIME = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "text/csv",
    "application/csv",
}
# Summary-row patterns to skip
_SKIP_PATTERNS = ("total", "subtotal", "grand total", "suma", "gran total")


@dataclass
class ParsedRow:
    description: str
    amount: Optional[float]
    source_row: int


class FileValidationError(Exception):
    pass


def validate_and_parse(uploaded_file) -> list[ParsedRow]:
    _validate_file(uploaded_file)
    ext = _get_extension(uploaded_file.name)
    raw_bytes = uploaded_file.read()

    try:
        df = _read_file(raw_bytes, ext)
    except Exception:
        raise FileValidationError(t("import.error_corrupt"))

    rows = _extract_rows(df)
    if not rows:
        raise FileValidationError(t("import.error_no_rows"))
    return rows


def _validate_file(f) -> None:
    max_mb = st.secrets.get("import", {}).get("max_file_size_mb", 10)
    size_bytes = f.size if hasattr(f, "size") else len(f.read())
    if hasattr(f, "read"):
        f.seek(0)
    if size_bytes > max_mb * 1024 * 1024:
        raise FileValidationError(t("import.error_file_size", max=max_mb))

    ext = _get_extension(f.name)
    if ext not in ACCEPTED_EXTENSIONS:
        raise FileValidationError(t("import.error_file_type"))

    mime = getattr(f, "type", "")
    if mime and mime not in ACCEPTED_MIME and "spreadsheet" not in mime and "csv" not in mime:
        raise FileValidationError(t("import.error_file_type"))


def _get_extension(filename: str) -> str:
    import os
    return os.path.splitext(filename.lower())[1]


def _read_file(raw_bytes: bytes, ext: str) -> pd.DataFrame:
    buf = io.BytesIO(raw_bytes)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(buf, header=None, dtype=str)
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            buf.seek(0)
            return pd.read_csv(buf, header=None, dtype=str, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Cannot decode CSV with known encodings")


def _is_summary_row(values: list) -> bool:
    combined = " ".join(str(v).lower() for v in values if v and str(v).strip())
    return any(pat in combined for pat in _SKIP_PATTERNS)


def _detect_desc_col(df: pd.DataFrame) -> int:
    """Return the column index most likely to contain descriptions (longest avg string)."""
    best, best_col = 0.0, 0
    for col_idx in range(df.shape[1]):
        col = df.iloc[:, col_idx].dropna().astype(str)
        avg_len = col.apply(len).mean() if not col.empty else 0
        if avg_len > best:
            best, best_col = avg_len, col_idx
    return best_col


def _detect_amount_col(df: pd.DataFrame) -> Optional[int]:
    """Return the column index most likely to contain numeric amounts."""
    for col_idx in range(df.shape[1]):
        col = df.iloc[:, col_idx].dropna().astype(str)
        numeric = pd.to_numeric(col.str.replace(r"[,$\s]", "", regex=True), errors="coerce").dropna()
        if len(numeric) / max(len(col), 1) > 0.5:
            return col_idx
    return None


def _extract_rows(df: pd.DataFrame) -> list[ParsedRow]:
    desc_col = _detect_desc_col(df)
    amount_col = _detect_amount_col(df)
    rows: list[ParsedRow] = []

    for row_idx, row in df.iterrows():
        values = row.tolist()
        if _is_summary_row(values):
            continue
        raw_desc = str(row.iloc[desc_col]).strip() if desc_col < len(row) else ""
        if not raw_desc or raw_desc.lower() in ("nan", "none", ""):
            continue

        amount: Optional[float] = None
        if amount_col is not None and amount_col < len(row):
            raw_amt = str(row.iloc[amount_col]).replace(",", "").replace("$", "").strip()
            try:
                amount = float(raw_amt)
            except ValueError:
                pass

        rows.append(ParsedRow(description=raw_desc, amount=amount, source_row=int(row_idx) + 1))

    return rows
