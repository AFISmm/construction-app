# Database Migration Notes: SQLite to PostgreSQL

**Date:** 2026-05-28
**Author:** Sebastian (Full-Stack Developer)

---

## Files modified

| File | Change type |
|---|---|
| `deliverables/app/db.py` | Engine connection updated |
| `deliverables/app/auth.py` | SMTP field names aligned with secrets.toml.example |
| `deliverables/app/requirements.txt` | Created with pinned versions including psycopg2-binary |
| `deliverables/app/init_db.py` | Created — standalone initialisation script |
| `deliverables/app/.gitignore` | Created |
| `deliverables/app/.streamlit/config.toml` | Created |
| `deliverables/app/README.md` | Rewritten with PostgreSQL instructions |
| `.streamlit/secrets.toml.example` | Updated — database.url now shows PostgreSQL format |

---

## Database connection changes

### Before (`db.py` lines 26-31)

```python
def _get_engine():
    global _engine
    if _engine is None:
        url = st.secrets.get("database", {}).get("url", "sqlite:///app.db")
        _engine = create_engine(url, echo=False, connect_args={"check_same_thread": False})
    return _engine
```

Problems with the old code:
- `connect_args={"check_same_thread": False}` is a SQLite-only argument; passing it to psycopg2 raises a `TypeError`.
- The `sqlite:///app.db` fallback silently creates a local file database that is lost on every Streamlit Cloud deployment (ephemeral filesystem).
- `pool_pre_ping=True` was absent — without it, long-idle connections from the cloud's connection pool raise `OperationalError: server closed the connection unexpectedly`.

### After

```python
def _get_engine():
    global _engine
    if _engine is None:
        url = st.secrets["database"]["url"]
        _engine = create_engine(url, echo=False, pool_pre_ping=True)
    return _engine
```

Changes:
- Hard requirement on `st.secrets["database"]["url"]` — the app will raise a clear `KeyError` at startup if the secret is missing rather than silently falling back to SQLite.
- `connect_args` removed — no SQLite-specific arguments remain.
- `pool_pre_ping=True` added — SQLAlchemy will issue a lightweight `SELECT 1` before each connection is handed to the application, recycling stale connections automatically.

---

## Data type audit — no corrections required

All SQLAlchemy models in `db.py` already use portable ORM types:

| Column type used | PostgreSQL mapping | Notes |
|---|---|---|
| `Integer, primary_key=True` | `SERIAL` / `BIGSERIAL` | ORM handles auto-increment — no `AUTOINCREMENT` keyword |
| `String(n)` | `VARCHAR(n)` | Compatible |
| `Text` | `TEXT` | Compatible |
| `DateTime` | `TIMESTAMP` | SQLAlchemy type, not raw string |
| `Date` | `DATE` | Compatible |
| `Numeric(15, 2)` | `NUMERIC(15,2)` | Compatible |
| `Float` | `DOUBLE PRECISION` | Compatible |
| `Boolean` | `BOOLEAN` | Compatible |
| `CheckConstraint(...)` | Inline check constraint | Supported by PostgreSQL |

No raw SQL strings with SQLite-specific syntax (`AUTOINCREMENT`, `PRAGMA`, etc.) were found anywhere in the codebase.

---

## secrets.toml.example — updated structure

The example now shows a PostgreSQL URL as the primary (and only) database option. The `[email]` section was aligned with field names the SMTP path in `auth.py` actually reads (`smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`). A new `[app]` section was added to document `secret_key`, `otp_ttl_minutes`, and `max_file_size_mb`.

---

## Developer notes

1. **First-time setup:** Run `python init_db.py` from the `deliverables/app/` directory after placing a valid `secrets.toml`. This calls `Base.metadata.create_all(engine)` and seeds the 50-entry taxonomy. On subsequent deploys, `create_all` is idempotent and safe to re-run.

2. **Supabase connection string:** In Supabase, use the "Transaction pooler" URI (port 6543) when deploying to Streamlit Cloud, not the direct connection (port 5432). The transaction pooler is compatible with serverless environments where connections are not persistent. Example format:
   ```
   postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

3. **Password special characters:** If the database password contains `@`, `/`, or other URL-special characters, percent-encode them or wrap the entire URL in quotes in `secrets.toml`.

4. **init_db.py entry point:** The script imports `app.db` using the package path, so it must be run from the `deliverables/app/` parent directory (i.e., `deliverables/`) or with `PYTHONPATH` set accordingly. The Streamlit Cloud entry point `main.py` calls `init_db()` internally on first load via `st.session_state["_db_ready"]`, so explicit `init_db.py` execution is only needed for local development or CI seeding.
