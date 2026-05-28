"""One-time database initialisation script.

Run this once against a fresh PostgreSQL database before starting the app:

    python init_db.py

Requires .streamlit/secrets.toml to be present with a valid [database] url.
"""
from __future__ import annotations

import sys


def main() -> None:
    # Import after streamlit so secrets are available.
    try:
        import streamlit as st  # noqa: F401  — triggers secrets loading
    except Exception as exc:
        print(f"WARNING: streamlit import issue — {exc}", file=sys.stderr)

    # Import must happen after streamlit so _get_engine() can read st.secrets.
    from app.db import Base, _get_engine, seed_categories

    engine = _get_engine()
    print("Creating tables...")
    Base.metadata.create_all(engine)

    table_names = list(Base.metadata.tables.keys())
    for name in sorted(table_names):
        print(f"  OK  {name}")

    print("\nSeeding taxonomy categories...")
    seed_categories()
    print("Done. Database is ready.")


if __name__ == "__main__":
    main()
