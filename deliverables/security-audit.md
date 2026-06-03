# Security Audit

**Auditor:** Luciana — Analista de Seguridad
**Date:** 2026-05-28
**Instruction:** `ronaldo-files/instructions/011-fase6-luciana-seguridad.md`
**Scope:** `deliverables/app/auth.py`, `db.py`, `i18n.py`, `main.py`, `import/parser.py`, `import/review.py`, `import/matcher.py`

---

## Executive summary

The application has a sound overall security posture. Secrets are externalized to `secrets.toml`, no credentials appear in code, and user-facing errors are controlled. Two findings require remediation before production deployment: a path-traversal vector in the i18n loader (HIGH) and the absence of a `.gitignore` that would prevent accidental credential commits (HIGH). All other findings are Medium or Low.

---

## Finding register

### SEC-001 — OTP hashed with SHA-256 (fast hash)

| Attribute | Value |
|---|---|
| **Severity** | Medium |
| **File** | `auth.py:21` |
| **CWE** | CWE-916 — Use of Password Hash With Insufficient Computational Effort |

**Description:** OTP tokens are 6-digit integers (space of 1,000,000 values). They are stored as `hashlib.sha256(token.encode()).hexdigest()`. SHA-256 is a general-purpose hash — on commodity hardware, a full 6-digit brute-force takes under one second if an attacker gains read access to the `otp_tokens` table.

**Mitigating controls present:**
- OTP TTL is 10 minutes — tokens expire before any useful window opens.
- Attempt limiting (MAX_ATTEMPTS = 5) prevents online guessing.
- Tokens are invalidated on successful use (`used = True`).
- Old unused tokens are revoked when a new one is issued.

**Risk:** Low in normal operation. Elevated only if database is directly compromised AND attacker acts within the 10-minute TTL window.

**Remediation:** Replace `hashlib.sha256` with `hashlib.pbkdf2_hmac("sha256", token.encode(), salt, 200_000)` with a per-token salt stored alongside the hash. Alternatively, accept the current risk given the TTL and attempt-limit mitigations — document the decision.

---

### SEC-002 — Path traversal via unsanitized `lang` value in i18n loader

| Attribute | Value |
|---|---|
| **Severity** | High |
| **File** | `i18n.py:13–21` |
| **CWE** | CWE-22 — Improper Limitation of a Pathname to a Restricted Directory |

**Description:** `_load(lang)` constructs the translation file path as `_TRANSLATIONS_DIR / f"{lang}.json"` where `lang` is read directly from `st.session_state["lang"]` without validation. If an attacker can write a crafted value to session state (e.g., through a future deserialization bug or session-fixation vector), they could read arbitrary `.json` files reachable from the translations directory. A path like `../../app/db` combined with a `.json` extension may not exist, but the attack surface is unnecessarily open.

**Current code:**
```python
lang = st.session_state.get("lang", "es")
path = _TRANSLATIONS_DIR / f"{lang}.json"
```

**Remediation (required before production):** Add an allowlist check before path construction:
```python
ALLOWED_LANGS = {"es", "en"}
lang = st.session_state.get("lang", "es")
if lang not in ALLOWED_LANGS:
    lang = "es"
path = _TRANSLATIONS_DIR / f"{lang}.json"
```
This also applies in `language_toggle()` — validate the radio value against `ALLOWED_LANGS` before writing to session state.

---

### SEC-003 — No rate limiting on `send_otp()`

| Attribute | Value |
|---|---|
| **Severity** | Medium |
| **File** | `auth.py:70–86` |
| **CWE** | CWE-770 — Allocation of Resources Without Limits or Throttling |

**Description:** `send_otp()` can be called for any email address with no frequency restriction. An attacker can spam OTP requests to: (a) exhaust the email service quota/cost, (b) harass a target email address with repeated messages.

**Mitigating controls present:** Each new `send_otp()` invalidates prior unused tokens (line 83), so multiple outstanding tokens cannot be used to brute-force in parallel.

**Remediation:** Add a per-email cooldown check before dispatching. Store the last send timestamp on the `User` record or in a Redis/DB cooldown table. Reject new sends within 60 seconds of the prior send. Alternatively, integrate with Streamlit's session-level debounce or an email provider's own rate limiting.

---

### SEC-004 — No `.gitignore` file — `secrets.toml` can be accidentally committed

| Attribute | Value |
|---|---|
| **Severity** | High |
| **File** | Project root (missing) |
| **CWE** | CWE-312 — Cleartext Storage of Sensitive Information |

**Description:** No `.gitignore` file exists at the project root. The `.streamlit/secrets.toml.example` file correctly documents that `secrets.toml` must not be committed, but without a `.gitignore` entry, a `git add .` will silently include real credentials.

**Remediation (required before first `git init` or `git add`):** Create `.gitignore` with at minimum:
```
.streamlit/secrets.toml
*.db
__pycache__/
.env
*.pyc
```

---

### SEC-005 — SMTP credentials transmitted in cleartext if `use_tls = false`

| Attribute | Value |
|---|---|
| **Severity** | Low |
| **File** | `auth.py:58–59` |

**Description:** The SMTP connection uses `starttls()` only when `cfg.get("use_tls", True)` is truthy. If a deployment sets `use_tls = false` in `secrets.toml`, credentials travel over plaintext. The default is safe, but the option allows insecure configuration.

**Remediation:** Remove the conditional — always call `s.starttls()` before login, or add a startup check that raises a `RuntimeError` if `use_tls` is False and SMTP credentials are configured.

---

### SEC-006 — `urllib.request.urlopen` used without explicit timeout (SendGrid path)

| Attribute | Value |
|---|---|
| **Severity** | Low |
| **File** | `auth.py:50` |

**Description:** The SendGrid HTTP call uses `urllib.request.urlopen(req)` with no timeout. If the SendGrid endpoint hangs, the Streamlit request thread blocks indefinitely, degrading availability.

**Remediation:** Pass `timeout=10` to `urlopen`: `urllib.request.urlopen(req, timeout=10)`.

---

### SEC-007 — Error message in `_fail_job` stores user-supplied filename

| Attribute | Value |
|---|---|
| **Severity** | Low |
| **File** | `import/review.py:168–176` |

**Description:** `_create_job()` calls `os.path.basename(filename)` before storing the filename, which correctly strips directory separators. However, the stored `safe_name` could still contain characters that may cause display issues if rendered without escaping. `st.dataframe` renders as text, so XSS risk is contained to Streamlit's own rendering engine, which is safe.

**Status:** Low risk. No action required for MVP.

---

## File upload security checklist

| Control | Requirement | Implementation | Status |
|---|---|---|---|
| Extension whitelist | Only .xlsx, .xls, .csv | `ACCEPTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}` — checked in `_validate_file` | ✅ Pass |
| MIME type check | Validate MIME against known types | `ACCEPTED_MIME` set checked with broad spreadsheet/csv fallback | ✅ Pass |
| File size limit | Configurable max, default 10 MB | `max_mb = st.secrets.get("import", {}).get("max_file_size_mb", 10)` | ✅ Pass |
| Path traversal prevention | Filename sanitized before DB storage | `os.path.basename(filename)` in `_create_job` | ✅ Pass |
| Error message safety | Validation errors use i18n keys | All errors raised with `t("import.error_*")` keys | ✅ Pass |
| No file content execution | File parsed as data only | `pd.read_excel` / `pd.read_csv` — no eval, no shell | ✅ Pass |
| Summary row filtering | Totals skipped | `_SKIP_PATTERNS` filters recognized summary strings | ✅ Pass |
| Stack trace not surfaced | Generic error on parse failure | Bare `except Exception` shows `t("import.error_corrupt")` | ✅ Pass |

---

## Credentials checklist

| Control | Requirement | Implementation | Status |
|---|---|---|---|
| No credentials in code | Zero hardcoded passwords/keys | All credentials read from `st.secrets` | ✅ Pass |
| No credentials in example file | `.toml.example` uses placeholder values only | `"your_smtp_password"`, `"SG.xxx..."` placeholders | ✅ Pass |
| `.gitignore` covers `secrets.toml` | Must be present | `.gitignore` does not exist | ❌ Fail (SEC-004) |
| Database URL externalized | Connection string not in code | `st.secrets["database"]["url"]` used in `db.py` | ✅ Pass |
| Email API key externalized | API key not in code | `cfg['api_key']` read from secrets | ✅ Pass |

---

## Error message safety review

| Location | User-facing message | Stack trace exposed? | Verdict |
|---|---|---|---|
| `main.py:_login_page()` send_otp failure | `t("error.server")` via bare `except Exception` | No | ✅ Safe |
| `main.py:_login_page()` verify_otp failure | `t("auth.otp_invalid", n=1)` | No | ✅ Safe |
| `import/review.py` parse failure | `str(e)` from `FileValidationError` — but these only contain `t()` outputs | No | ✅ Safe |
| `import/review.py` bare exception | `t("import.error_corrupt")` | No | ✅ Safe |
| `i18n.py` missing key | Returns key string itself (e.g. `"error.not_found"`) | No | ✅ Safe |
| SQLAlchemy exceptions | Not caught at page level — Streamlit catches and shows default error | Potentially visible in dev mode | ⚠️ Note |

**Note on SQLAlchemy exceptions:** Uncaught DB errors propagate to Streamlit's built-in error display, which in development mode shows the full traceback. In production Streamlit Cloud deployments, the default behavior hides tracebacks from the UI. Consider wrapping DB calls in page-level `try/except` blocks for hardened deployments.

---

## Remediation priority

| Finding | Severity | Required before production? | Effort |
|---|---|---|---|
| SEC-002 — i18n path traversal | High | Yes | XS — 4 lines |
| SEC-004 — Missing .gitignore | High | Yes (before first git add) | XS — create file |
| SEC-001 — SHA-256 OTP hash | Medium | Recommended | S |
| SEC-003 — No OTP rate limiting | Medium | Recommended | S |
| SEC-005 — TLS optional | Low | No | XS |
| SEC-006 — No HTTP timeout | Low | No | XS |
| SEC-007 — Filename storage | Low | No | None required |

---

## Sign-off

**SEC-002 and SEC-004 are blocking findings.** The application must not be deployed to production until:
1. `i18n.py` validates `lang` against `ALLOWED_LANGS = {"es", "en"}` before path construction.
2. A `.gitignore` file exists at the project root that excludes `.streamlit/secrets.toml`.

All other findings are non-blocking. The application passes the security audit **conditionally**, pending remediation of the two HIGH findings above.

| Category | Result |
|---|---|
| Credentials hygiene | ✅ Pass (pending .gitignore — SEC-004) |
| OTP security | ✅ Acceptable with documented risk (SEC-001) |
| File upload security | ✅ Pass |
| Input validation / path traversal | ❌ Requires fix (SEC-002) |
| Error message safety | ✅ Pass (note re: uncaught DB exceptions) |
| Rate limiting | ⚠️ Acceptable for MVP, remediate for production (SEC-003) |

**Overall: CONDITIONAL PASS — remediate SEC-002 and SEC-004 before production deployment.**
