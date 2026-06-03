# Import Pipeline — Design Doc

**Producido por:** Isabela — Ingeniería de Importación
**Fecha:** 2026-05-28
**Instrucción:** `ronaldo-files/instructions/009-fase45-isabela-import.md`
**Módulos:** `deliverables/app/import/parser.py`, `matcher.py`, `review.py`

---

## Overview

The import pipeline allows users to upload a budget file in .xlsx, .xls, or .csv format. Each row is parsed, its description is fuzzy-matched against the canonical taxonomy, and a confidence score is assigned. The user reviews the preview — correcting low-confidence rows — before confirming. On confirmation, matched rows are inserted as `budget_lines` in the active project. Every import attempt is logged in `import_jobs` regardless of outcome.

**Flow:** Upload → Validate → Parse → Match → User Review → Confirm → Commit → Log

---

## Matching algorithm

| Step | Action | Library / method |
|---|---|---|
| 1. Normalize | Lowercase, strip accents (NFD decomposition), remove punctuation, collapse whitespace | `unicodedata`, stdlib |
| 2. Exact match | If normalized strings are identical, score = 1.0 | String equality |
| 3. Fuzzy match (name) | `fuzz.token_sort_ratio(norm_desc, norm_cat_name) / 100` | `rapidfuzz.fuzz` |
| 4. Fuzzy match (desc) | `fuzz.token_sort_ratio(norm_desc, norm_cat_desc) / 100 * 0.9` | `rapidfuzz.fuzz` |
| 5. Best score | `max(score_name, score_desc)` per category; highest wins | — |
| 6. Threshold | If best score < 0.50, return unmatched | — |

Token-sort-ratio handles word-order variation common in Spanish descriptions (e.g., "compra lote" vs "lote compra").

---

## Confidence thresholds

| Range | Behavior | UI indicator |
|---|---|---|
| >= 0.90 | Auto-assigned | No flag |
| 0.70 – 0.89 | Auto-assigned; shown in preview | No flag |
| 0.50 – 0.69 | Needs user review | Orange `>>` marker; override required |
| < 0.50 | Unmatched | Orange `>>` marker; override required |
| 0.00 (no match) | Unmatched | Orange `>>` marker; row will be skipped if not overridden |

Confirm button is disabled until all flagged rows have an override or are marked skip.

---

## File format support

| Format | Parser | Notes |
|---|---|---|
| .xlsx | `openpyxl` via `pandas.read_excel` | Binary format; no encoding issues |
| .xls | `openpyxl` via `pandas.read_excel` | Legacy Excel; same API |
| .csv | `pandas.read_csv` | UTF-8 tried first, then latin-1, then cp1252 (handles Spanish headers) |

**Column auto-detection:**
- Description column: column with highest average string length.
- Amount column: column where > 50% of rows parse as numeric after removing `,`, `$`.
- Summary rows (containing "total", "subtotal", "grand total", "suma") are skipped.

---

## Error handling matrix

| Condition | User-facing message (ES) | User-facing message (EN) | i18n key | Job status |
|---|---|---|---|---|
| Unsupported file type | Tipo de archivo no admitido. Use .xlsx, .xls o .csv. | Unsupported file type. Use .xlsx, .xls, or .csv. | `import.error_file_type` | failed |
| File exceeds size limit | El archivo supera el tamano maximo ({max} MB). | File exceeds the maximum allowed size ({max} MB). | `import.error_file_size` | failed |
| Corrupt / unreadable file | No se pudo leer el archivo. Verifique que no este danado. | Could not read the file. Please verify it is not corrupted. | `import.error_corrupt` | failed |
| No valid data rows found | El archivo no contiene filas de datos validas. | The file contains no valid data rows. | `import.error_no_rows` | failed |
| Unreviewed flagged rows | Revisa todas las filas marcadas antes de confirmar. | Review all flagged rows before confirming. | `import.error_unreviewed` | — (blocks confirm) |
| Duplicate budget line | Esta fila crearia una linea duplicada. | This row would create a duplicate line. | `import.duplicate_warning` | row skipped |

Stack traces are never shown to the user. All exceptions are caught in `review.py` and surfaced via `t()`.

---

## import_jobs schema reference

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| project_id | INTEGER FK | Scopes job to project |
| filename | TEXT | `os.path.basename()` — never a full path |
| status | TEXT | pending → partial → complete / failed |
| total_rows | INTEGER | Count of parsed data rows |
| matched_rows | INTEGER | Confidence >= 0.70 at parse time; updated to confirmed count after commit |
| unmatched_rows | INTEGER | Confidence < 0.70 |
| error_message | TEXT | Populated on status = failed |
| created_at / updated_at | TIMESTAMP | |

---

## import_rows schema reference

| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | |
| import_job_id | INTEGER FK | |
| original_description | TEXT | Raw text from source file |
| original_amount | DECIMAL | Optional — None if column not detected |
| matched_taxonomy_code | TEXT FK → categories | Best match code; NULL if unmatched |
| confidence_score | REAL | 0.0 – 1.0 |
| override_code | TEXT FK → categories | User-selected correction; NULL if not overridden |
| status | TEXT | pending → confirmed / skipped / overridden |
| created_at | TIMESTAMP | |

---

## Security notes

- `filename` is stored as `os.path.basename(f.name)` — the raw uploaded filename is never used as a filesystem path.
- File size is validated before any parsing begins; parsing is never attempted on files exceeding the limit.
- MIME type and extension are both checked; a `.csv` with MIME `application/octet-stream` is still accepted if extension is correct (common with some browsers).
- Uploaded bytes are read into `io.BytesIO` — no file is written to disk.
- Luciana's security review (`deliverables/security-audit.md`) covers this module under "file upload security."

---

## Integration handoff to Sebastián

`deliverables/app/import/__init__.py` exports `run_import_page(project_id: int)`.  
Call it from `deliverables/app/pages/import_page.py`:

```python
from app.import_ import run_import_page
run_import_page(st.session_state["current_project_id"])
```

Note: the Python package is `app.import_` (trailing underscore) because `import` is a reserved keyword. The directory is named `import/` for filesystem clarity.
