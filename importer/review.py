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
    code_to_label = {c.code: _cat_label(c) for c in categories}

    # Apply AI pending suggestions and re-translate stored codes — BEFORE widgets render
    for key in list(st.session_state.keys()):
        if key.startswith("_ai_pending_"):
            row_id = key[len("_ai_pending_"):]
            label = st.session_state.pop(key)
            if label:
                st.session_state[f"override_{row_id}"] = label
        elif key.startswith("_override_code_"):
            row_id = key[len("_override_code_"):]
            code = st.session_state[key]
            if code and code in code_to_label:
                st.session_state[f"override_{row_id}"] = code_to_label[code]

    has_api_key = bool(st.secrets.get("anthropic", {}).get("api_key", ""))
    flagged_ids: list[int] = []
    pending_overrides: dict[int, Optional[str]] = {}

    flagged_rows = [r for r in row_data if r["confidence"] < LOW_CONFIDENCE_THRESHOLD]
    unassigned_flags = [r for r in flagged_rows if not st.session_state.get(f"override_{r['id']}", "")]

    if unassigned_flags:
        st.warning(t("import.low_confidence_warning"))

    if flagged_rows and has_api_key:
        if st.button(t("import.ai_suggest_button")):
            from importer.ai_suggest import suggest_categories, suggest_category
            assigned_count = 0
            chunk_size = 15
            all_suggestions: dict = {}

            # Step 1 — batch (numeric-indexed, more reliable)
            with st.spinner(t("import.ai_suggest_loading")):
                descs = [r["desc"] for r in flagged_rows]
                for i in range(0, len(descs), chunk_size):
                    chunk = descs[i:i + chunk_size]
                    try:
                        result = suggest_categories(chunk, categories)
                        all_suggestions.update(result)
                    except Exception:
                        pass

            # Step 2 — per-row fallback for any still unassigned
            still_missing = [r for r in flagged_rows if not all_suggestions.get(r["desc"])]
            if still_missing:
                with st.spinner(f"Completando {len(still_missing)} fila(s) restante(s)..."):
                    for row in still_missing:
                        code = suggest_category(row["desc"], categories)
                        if code:
                            all_suggestions[row["desc"]] = code

            # Apply results
            for row in flagged_rows:
                code = all_suggestions.get(row["desc"])
                if code:
                    label = code_to_label.get(code, "")
                    if label:
                        st.session_state[f"_ai_pending_{row['id']}"] = label
                        st.session_state[f"_override_code_{row['id']}"] = code
                        assigned_count += 1

            if assigned_count > 0:
                st.success(f"{assigned_count} de {len(flagged_rows)} categoría(s) asignada(s).")
            else:
                st.warning("La IA no pudo asignar categorías. Verifica la API key en Secrets.")
            st.rerun()

    # Column headers
    h_desc, h_cat = st.columns([4, 4])
    h_desc.markdown(f"**{t('import.col_original')}**")
    h_cat.markdown(f"**{t('import.col_category')}**")
    st.divider()

    for row in row_data:
        conf = row["confidence"]
        flag = conf < LOW_CONFIDENCE_THRESHOLD
        is_assigned = bool(st.session_state.get(f"override_{row['id']}", ""))
        marker = ":green[✓]" if (not flag or is_assigned) else ":orange[⚠]"
        c_desc, c_cat = st.columns([4, 4])
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
            code = cat_map.get(selected) if selected else None
            pending_overrides[row["id"]] = code
            if code:
                st.session_state[f"_override_code_{row['id']}"] = code
        else:
            matched_label = code_to_label.get(row["code"], "—")
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
    if col1.button(t("nav.dashboard")):
        st.session_state["_import_step"] = "upload"
        st.session_state.pop("_import_job_id", None)
        st.session_state.pop("_import_mode", None)
        st.switch_page("pages/dashboard.py")
    if col2.button(t("import.upload_label")):
        st.session_state["_import_step"] = "upload"
        st.session_state.pop("_import_job_id", None)
        st.session_state.pop("_import_mode", None)
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


def _safe_amount(value) -> float:
    """Convert import amount to float, returning 0 for None/NaN."""
    import math
    try:
        f = float(value)
        return 0.0 if math.isnan(f) or math.isinf(f) else f
    except (TypeError, ValueError):
        return 0.0


def _commit_rows(project_id: int, job_id: int) -> int:
    import streamlit as _st
    merge_mode = _st.session_state.get("_import_mode", "new") == "merge"
    committed = 0
    with get_session() as session:
        rows = session.query(ImportRow).filter_by(import_job_id=job_id).all()
        for row in rows:
            effective_code = row.override_code or row.matched_taxonomy_code
            if not effective_code:
                row.status = "skipped"
                continue

            amount = _safe_amount(row.original_amount)

            existing = session.query(BudgetLine).filter_by(
                project_id=project_id, category_code=effective_code
            ).first()

            if existing:
                if merge_mode and amount > 0:
                    existing.budgeted_amount = float(existing.budgeted_amount) + amount
                    row.status = "confirmed"
                    committed += 1
                else:
                    row.status = "skipped"
                continue

            session.add(BudgetLine(
                project_id=project_id,
                category_code=effective_code,
                budgeted_amount=amount,
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
