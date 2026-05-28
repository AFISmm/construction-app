"""Import review UI: upload → parse → match → review → confirm → commit."""
from __future__ import annotations

from datetime import date
from typing import Optional

import pandas as pd
import streamlit as st

from budget import get_all_categories
from db import BudgetLine, ImportJob, ImportRow, get_session
from i18n import t

from importer.matcher import LOW_CONFIDENCE_THRESHOLD, MatchResult, match_batch
from importer.parser import FileValidationError, ParsedRow, validate_and_parse


def run_import_page(project_id: int) -> None:
    step = st.session_state.get("_import_step", "upload")

    col1, col2, col3 = st.columns(3)
    for col, label, active_step in [
        (col1, t("import.upload_label"), "upload"),
        (col2, t("import.preview_title"), "review"),
        (col3, t("common.confirm"), "confirm"),
    ]:
        if step == active_step:
            col.markdown(f"**✅ {label}**")
        else:
            col.markdown(f"<span style='color:gray'>{label}</span>", unsafe_allow_html=True)
    st.divider()

    if step == "upload":
        _step_upload(project_id)
    elif step == "review":
        _step_review(project_id)
    elif step == "confirm":
        _step_confirm(project_id)

    _show_import_history(project_id)


def _step_upload(project_id: int) -> None:
    uploaded = st.file_uploader(
        t("import.upload_label"),
        type=["xlsx", "xls", "csv"],
        help=t("import.upload_help"),
    )
    if not uploaded:
        return

    job_id = _create_job(project_id, uploaded.name)

    try:
        parsed_rows = validate_and_parse(uploaded)
    except FileValidationError as e:
        _fail_job(job_id, str(e))
        st.error(str(e))
        return
    except Exception:
        msg = t("import.error_corrupt")
        _fail_job(job_id, msg)
        st.error(msg)
        return

    descriptions = [r.description for r in parsed_rows]
    match_results = match_batch(descriptions)

    _store_rows(job_id, parsed_rows, match_results)
    _update_job_counts(job_id, len(parsed_rows), match_results)

    st.session_state["_import_job_id"] = job_id
    st.session_state["_import_step"] = "review"
    st.rerun()


def _step_review(project_id: int) -> None:
    job_id = st.session_state.get("_import_job_id")
    if not job_id:
        st.session_state["_import_step"] = "upload"
        st.rerun()
        return

    with get_session() as session:
        rows = session.query(ImportRow).filter_by(import_job_id=job_id).all()
        row_data = [
            {
                "id": r.id,
                "desc": r.original_description,
                "amount": r.original_amount,
                "code": r.matched_taxonomy_code,
                "confidence": r.confidence_score or 0.0,
                "override": r.override_code,
                "status": r.status,
            }
            for r in rows
        ]

    categories = get_all_categories()

    def _cat_label(c) -> str:
        translated = t(f"cat.{c.code}")
        name = translated if translated != f"cat.{c.code}" else c.name
        return f"{c.code} — {name}"

    cat_options = [""] + [_cat_label(c) for c in categories]
    cat_map = {_cat_label(c): c.code for c in categories}

    has_api_key = bool(st.secrets.get("anthropic", {}).get("api_key", ""))
    flagged_ids: list[int] = []
    pending_overrides: dict[int, Optional[str]] = {}

    flagged_rows = [r for r in row_data if r["confidence"] < LOW_CONFIDENCE_THRESHOLD]
    if flagged_rows:
        st.warning(t("import.low_confidence_warning"))

    # Column headers
    h_desc, h_cat, h_ai = st.columns([4, 3.5, 0.5])
    h_desc.markdown(f"**{t('import.col_original')}**")
    h_cat.markdown(f"**{t('import.col_category')}**")
    if has_api_key:
        h_ai.markdown("**IA**")
    st.divider()

    for row in row_data:
        conf = row["confidence"]
        flag = conf < LOW_CONFIDENCE_THRESHOLD
        marker = ":orange[⚠]" if flag else ":green[✓]"
        c_desc, c_cat, c_ai = st.columns([4, 3.5, 0.5])
        c_desc.write(f"{marker} {row['desc']}")

        if flag:
            flagged_ids.append(row["id"])
            current_override = row["override"] or ""
            current_label = next((k for k, v in cat_map.items() if v == current_override), "")
            selected = c_cat.selectbox(
                "",
                cat_options,
                index=cat_options.index(current_label) if current_label in cat_options else 0,
                key=f"override_{row['id']}",
                label_visibility="collapsed",
            )
            pending_overrides[row["id"]] = cat_map.get(selected) if selected else None

            if has_api_key and c_ai.button("🤖", key=f"ai_{row['id']}", help=t("import.ai_suggest_button")):
                with st.spinner(""):
                    from importer.ai_suggest import suggest_categories
                    suggestions = suggest_categories([row["desc"]], categories)
                    code = suggestions.get(row["desc"])
                    if code:
                        label = next((k for k, v in cat_map.items() if v == code), "")
                        if label:
                            st.session_state[f"override_{row['id']}"] = label
                st.rerun()
        else:
            matched_label = next((k for k, v in cat_map.items() if v == row["code"]), "—")
            c_cat.write(matched_label)

    unresolved = sum(1 for rid in flagged_ids if not pending_overrides.get(rid))
    col_confirm, col_cancel = st.columns(2)

    if col_confirm.button(t("import.confirm_button"), disabled=unresolved > 0):
        _apply_overrides(pending_overrides)
        st.session_state["_import_step"] = "confirm"
        st.rerun()

    if unresolved > 0:
        st.caption(t("import.error_unreviewed"))

    if col_cancel.button(t("common.cancel")):
        _fail_job(job_id, "Cancelled by user")
        st.session_state["_import_step"] = "upload"
        st.session_state.pop("_import_job_id", None)
        st.rerun()


def _step_confirm(project_id: int) -> None:
    job_id = st.session_state.get("_import_job_id")
    if not job_id:
        st.session_state["_import_step"] = "upload"
        st.rerun()
        return

    committed = _commit_rows(project_id, job_id)
    st.success(t("import.success", n=committed))

    col1, col2 = st.columns(2)
    if col1.button(t("nav.budget")):
        st.session_state["_import_step"] = "upload"
        st.session_state.pop("_import_job_id", None)
        st.switch_page("pages/budget.py")
    if col2.button(t("import.upload_label")):
        st.session_state["_import_step"] = "upload"
        st.session_state.pop("_import_job_id", None)
        st.rerun()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _create_job(project_id: int, filename: str) -> int:
    import os
    safe_name = os.path.basename(filename)
    with get_session() as session:
        job = ImportJob(project_id=project_id, filename=safe_name, status="pending")
        session.add(job)
        session.flush()
        job_id = job.id
    return job_id


def _store_rows(job_id: int, parsed: list[ParsedRow], matches: list[MatchResult]) -> None:
    with get_session() as session:
        for row, match in zip(parsed, matches):
            session.add(ImportRow(
                import_job_id=job_id,
                original_description=row.description,
                original_amount=row.amount,
                matched_taxonomy_code=match.code,
                confidence_score=match.confidence,
                status="pending",
            ))


def _update_job_counts(job_id: int, total: int, matches: list[MatchResult]) -> None:
    matched = sum(1 for m in matches if m.confidence >= LOW_CONFIDENCE_THRESHOLD)
    with get_session() as session:
        job = session.get(ImportJob, job_id)
        if job:
            job.total_rows = total
            job.matched_rows = matched
            job.unmatched_rows = total - matched
            job.status = "partial"


def _fail_job(job_id: int, message: str) -> None:
    with get_session() as session:
        job = session.get(ImportJob, job_id)
        if job:
            job.status = "failed"
            job.error_message = message


def _apply_overrides(overrides: dict[int, Optional[str]]) -> None:
    with get_session() as session:
        for row_id, code in overrides.items():
            row = session.get(ImportRow, row_id)
            if row and code:
                row.override_code = code
                row.status = "overridden"


def _commit_rows(project_id: int, job_id: int) -> int:
    committed = 0
    today = date.today()
    with get_session() as session:
        rows = session.query(ImportRow).filter_by(import_job_id=job_id).all()
        for row in rows:
            effective_code = row.override_code or row.matched_taxonomy_code
            if not effective_code:
                row.status = "skipped"
                continue

            existing = session.query(BudgetLine).filter_by(
                project_id=project_id, category_code=effective_code
            ).first()
            if existing:
                row.status = "skipped"
                continue

            session.add(BudgetLine(
                project_id=project_id,
                category_code=effective_code,
                budgeted_amount=row.original_amount or 0,
                description=row.original_description,
            ))
            row.status = "confirmed"
            committed += 1

        job = session.get(ImportJob, job_id)
        if job:
            job.status = "complete"
            job.matched_rows = committed

    return committed


def _show_import_history(project_id: int) -> None:
    with get_session() as session:
        jobs = (
            session.query(ImportJob)
            .filter_by(project_id=project_id)
            .order_by(ImportJob.created_at.desc())
            .limit(10)
            .all()
        )
        if not jobs:
            return

    st.divider()
    st.subheader(t("import.history_title"))
    rows = [
        {
            t("import.history_col_file"): j.filename,
            t("import.history_col_status"): t(f"import.status_{j.status}"),
            t("import.history_col_date"): str(j.created_at)[:10],
            t("import.history_col_rows"): j.total_rows,
            t("import.history_col_matched"): j.matched_rows,
        }
        for j in jobs
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
