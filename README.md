# Control de Presupuesto de Construccion / Construction Budget Control

**ES:** Aplicacion Streamlit para el seguimiento de presupuestos y gastos en proyectos de construccion. Soporta multiples proyectos, interfaz bilingue (espanol / ingles) e importacion de archivos con normalizacion de taxonomia.

**EN:** Streamlit application for tracking construction project budgets and expenses. Supports multiple projects, bilingual UI (Spanish / English), and file import with taxonomy normalization.

---

## Requisitos previos / Prerequisites

- Python 3.11+
- PostgreSQL externo — se recomienda [Supabase](https://supabase.com) (plan gratuito disponible)
- Cuenta de correo electronico para envio de codigos OTP (Gmail con App Password o SendGrid)

## Variables de configuracion requeridas / Required secrets

Crea el archivo `.streamlit/secrets.toml` a partir del ejemplo:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Estructura requerida:

```toml
[database]
url = "postgresql://user:password@host:5432/dbname"

[email]
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_user = "usuario@ejemplo.com"
smtp_password = "app-password-de-16-chars"
from_address = "usuario@ejemplo.com"

[app]
secret_key = "cadena-aleatoria-de-32-caracteres"
otp_ttl_minutes = 10
max_file_size_mb = 10
```

## Ejecucion local / Running locally

```bash
pip install -r requirements.txt

# Crear .streamlit/secrets.toml con los valores reales (ver seccion anterior)

python init_db.py   # solo la primera vez — crea tablas y siembra taxonomia

streamlit run main.py
```

## Estructura del proyecto / Project structure

```
app/
├── main.py           — Entry point (streamlit run this file)
├── init_db.py        — One-time DB initialisation script
├── requirements.txt  — Pinned dependencies
├── db.py             — SQLAlchemy models and session factory
├── auth.py           — OTP authentication
├── i18n.py           — t(key) translation helper
├── projects.py       — Project CRUD
├── budget.py         — Budget line CRUD
├── expenses.py       — Expense CRUD
├── reports.py        — Variance analysis and export
├── import/           — File import pipeline (parser, matcher, review)
└── pages/            — One file per screen
    ├── dashboard.py
    ├── budget.py
    ├── expenses.py
    ├── import_page.py
    ├── progress.py
    ├── rooms.py
    ├── account.py
    └── project_form.py

translations/
├── es.json           — Spanish UI strings
└── en.json           — English UI strings
```

## Deployment

For step-by-step instructions on deploying to Streamlit Community Cloud with Supabase, see `deliverables/deployment-checklist.md`.
