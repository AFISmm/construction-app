# UI Design

**Producido por:** Camila — Diseñadora de Aplicación Web
**Fecha:** 2026-05-28
**Instrucción:** `ronaldo-files/instructions/007-fase3-diseno-ui.md`
**Fuentes:** `deliverables/data-model.md`, `deliverables/taxonomy.md`, `inicio-proyecto.md`

---

## UX Flow

```
[Unauthenticated]
    Login
      |
      v
    OTP Verification
      |
      v
[Authenticated]
    Project List -------> Project Create/Edit
      |
      v (select project)
    Project Dashboard
      |
      +-------> Budget Setup -----> Room Detail
      |
      +-------> Expense Entry
      |
      +-------> File Import
      |
      +-------> Progress View
      |
      +-------> User Management

Sidebar (persistent on all authenticated screens):
  - Language toggle (ES | EN)
  - Active project selector + "New project" link
  - Navigation links
  - User email + logout
```

---

## Screen inventory

| # | Screen | Nav label (ES) | Nav label (EN) | Primary action | Owner entity |
|---|---|---|---|---|---|
| 1 | Login | — | — | Send OTP | users |
| 2 | OTP Verification | — | — | Verify code | otp_tokens |
| 3 | Project List | Proyectos | Projects | Create project | projects |
| 4 | Project Create/Edit | Nuevo proyecto | New project | Save | projects |
| 5 | Project Dashboard | Inicio | Dashboard | Navigate to sub-screens | projects, budget_lines, expenses |
| 6 | Budget Setup | Presupuesto | Budget | Add / edit budget lines | budget_lines, categories, rooms |
| 7 | Expense Entry | Gastos | Expenses | Record expense | expenses, budget_lines |
| 8 | File Import | Importar | Import | Upload, review, confirm | import_jobs, import_rows |
| 9 | Progress View | Progreso | Progress | Export report | budget_lines, expenses |
| 10 | Room Detail | Habitaciones | Rooms | Add room / view room budget | rooms, budget_lines, expenses |
| 11 | User Management | Mi cuenta | My account | Log out | users |

---

## Sidebar component

Reused unchanged on every authenticated screen. Project selector and language toggle are the two highest-priority elements.

```
+-------------------------------+
| [ES]  [EN]                    |  <- st.radio horizontal, key="lang"
|-------------------------------|
| Proyecto activo               |  <- st.caption
| [Proyecto actual          v]  |  <- st.selectbox, options=user_projects
| + Nuevo proyecto              |  <- st.page_link / st.button
|-------------------------------|
| Inicio                        |  <- st.page_link
| Presupuesto                   |
| Gastos                        |
| Importar                      |
| Progreso                      |
| Habitaciones                  |
| Mi cuenta                     |
|-------------------------------|
| usuario@email.com             |  <- st.caption
| [Cerrar sesion]               |  <- st.button
+-------------------------------+
```

| Element | ES | EN | i18n key | Component |
|---|---|---|---|---|
| Language toggle label | Idioma | Language | `nav.language_toggle` | `st.radio` (horizontal) |
| Project selector label | Proyecto activo | Active project | `project.selector_label` | `st.selectbox` |
| New project link | + Nuevo proyecto | + New project | `nav.new_project` | `st.page_link` |
| Nav: Dashboard | Inicio | Dashboard | `nav.dashboard` | `st.page_link` |
| Nav: Budget | Presupuesto | Budget | `nav.budget` | `st.page_link` |
| Nav: Expenses | Gastos | Expenses | `nav.expenses` | `st.page_link` |
| Nav: Import | Importar | Import | `nav.import` | `st.page_link` |
| Nav: Progress | Progreso | Progress | `nav.progress` | `st.page_link` |
| Nav: Rooms | Habitaciones | Rooms | `nav.rooms` | `st.page_link` |
| Nav: Account | Mi cuenta | My account | `nav.account` | `st.page_link` |
| User email | (dynamic) | (dynamic) | — | `st.caption` |
| Logout button | Cerrar sesion | Log out | `nav.logout` | `st.button` |

---

## Language key map

All keys defined here are the single source of truth for `translations/es.json` and `translations/en.json`. Both files must contain identical key sets.

### auth.*

| Key | ES | EN |
|---|---|---|
| `auth.page_title` | Control de Presupuesto | Budget Control |
| `auth.email_label` | Correo electronico | Email address |
| `auth.email_placeholder` | tu@correo.com | you@email.com |
| `auth.send_otp_button` | Enviar codigo | Send code |
| `auth.otp_label` | Codigo de verificacion | Verification code |
| `auth.otp_placeholder` | 000000 | 000000 |
| `auth.verify_button` | Verificar | Verify |
| `auth.resend_link` | Reenviar codigo | Resend code |
| `auth.otp_sent` | Codigo enviado a {email} | Code sent to {email} |
| `auth.otp_expired` | El codigo expiro. Solicita uno nuevo. | Code expired. Request a new one. |
| `auth.otp_invalid` | Codigo incorrecto. Intento {n} de 5. | Incorrect code. Attempt {n} of 5. |
| `auth.otp_locked` | Demasiados intentos. Solicita un nuevo codigo. | Too many attempts. Request a new code. |
| `auth.welcome` | Bienvenido | Welcome |

### nav.*

| Key | ES | EN |
|---|---|---|
| `nav.language_toggle` | Idioma | Language |
| `nav.dashboard` | Inicio | Dashboard |
| `nav.budget` | Presupuesto | Budget |
| `nav.expenses` | Gastos | Expenses |
| `nav.import` | Importar | Import |
| `nav.progress` | Progreso | Progress |
| `nav.rooms` | Habitaciones | Rooms |
| `nav.account` | Mi cuenta | My account |
| `nav.projects` | Proyectos | Projects |
| `nav.new_project` | + Nuevo proyecto | + New project |
| `nav.logout` | Cerrar sesion | Log out |
| `nav.selector_label` | Proyecto activo | Active project |

### common.*

| Key | ES | EN |
|---|---|---|
| `common.save` | Guardar | Save |
| `common.cancel` | Cancelar | Cancel |
| `common.delete` | Eliminar | Delete |
| `common.edit` | Editar | Edit |
| `common.add` | Agregar | Add |
| `common.confirm` | Confirmar | Confirm |
| `common.back` | Volver | Back |
| `common.search` | Buscar | Search |
| `common.export` | Exportar | Export |
| `common.loading` | Cargando... | Loading... |
| `common.no_data` | Sin datos | No data |
| `common.success` | Operacion exitosa | Operation successful |
| `common.required_field` | Campo obligatorio | Required field |
| `common.currency` | Moneda | Currency |
| `common.actions` | Acciones | Actions |

### project.*

| Key | ES | EN |
|---|---|---|
| `project.list_title` | Mis proyectos | My projects |
| `project.create_title` | Nuevo proyecto | New project |
| `project.edit_title` | Editar proyecto | Edit project |
| `project.create_button` | Crear proyecto | Create project |
| `project.name_label` | Nombre del proyecto | Project name |
| `project.name_placeholder` | Ej: Remodelacion Casa Bogota | E.g.: Bogota Home Renovation |
| `project.type_label` | Tipo de proyecto | Project type |
| `project.type_residential` | Residencial | Residential |
| `project.type_commercial` | Comercial | Commercial |
| `project.description_label` | Descripcion | Description |
| `project.no_projects` | No tienes proyectos. Crea uno para comenzar. | No projects yet. Create one to get started. |
| `project.total_budget` | Presupuesto total | Total budget |
| `project.total_spent` | Ejecutado | Spent |
| `project.balance` | Saldo disponible | Available balance |
| `project.pct_executed` | % Ejecutado | % Executed |
| `project.created_at` | Creado el | Created on |
| `project.type_badge_residential` | Residencial | Residential |
| `project.type_badge_commercial` | Comercial | Commercial |
| `project.delete_confirm` | Eliminar este proyecto eliminara todos sus datos. Esta accion no se puede deshacer. | Deleting this project will remove all its data. This action cannot be undone. |

### budget.*

| Key | ES | EN |
|---|---|---|
| `budget.title` | Presupuesto | Budget |
| `budget.add_line` | Agregar linea | Add line |
| `budget.category_label` | Categoria | Category |
| `budget.room_label` | Habitacion | Room |
| `budget.room_all` | Todo el proyecto | Whole project |
| `budget.description_label` | Descripcion | Description |
| `budget.amount_label` | Monto presupuestado | Budgeted amount |
| `budget.line_saved` | Linea guardada | Line saved |
| `budget.line_deleted` | Linea eliminada | Line deleted |
| `budget.no_lines` | Sin lineas de presupuesto. Agrega una. | No budget lines yet. Add one. |
| `budget.over_budget_warning` | Esta categoria supera el presupuesto | This category exceeds budget |
| `budget.total_row` | Total | Total |

### expense.*

| Key | ES | EN |
|---|---|---|
| `expense.title` | Gastos | Expenses |
| `expense.add_expense` | Registrar gasto | Record expense |
| `expense.vendor_label` | Proveedor | Vendor |
| `expense.description_label` | Descripcion | Description |
| `expense.amount_label` | Monto | Amount |
| `expense.date_label` | Fecha | Date |
| `expense.notes_label` | Notas | Notes |
| `expense.budget_line_label` | Linea de presupuesto | Budget line |
| `expense.saved` | Gasto registrado | Expense recorded |
| `expense.deleted` | Gasto eliminado | Expense deleted |
| `expense.no_expenses` | Sin gastos registrados | No expenses recorded |

### import.*

| Key | ES | EN |
|---|---|---|
| `import.title` | Importar presupuesto | Import budget |
| `import.upload_label` | Selecciona archivo | Select file |
| `import.upload_help` | Formatos aceptados: .xlsx, .xls, .csv | Accepted formats: .xlsx, .xls, .csv |
| `import.preview_title` | Vista previa | Preview |
| `import.col_original` | Descripcion original | Original description |
| `import.col_category` | Categoria asignada | Assigned category |
| `import.col_confidence` | Confianza | Confidence |
| `import.col_override` | Corregir | Override |
| `import.col_amount` | Monto | Amount |
| `import.confirm_button` | Confirmar importacion | Confirm import |
| `import.low_confidence_warning` | Las filas marcadas requieren revision antes de confirmar. | Flagged rows require review before confirming. |
| `import.success` | Importacion completada. {n} filas importadas. | Import complete. {n} rows imported. |
| `import.error_file_type` | Tipo de archivo no admitido. Use .xlsx, .xls o .csv. | Unsupported file type. Use .xlsx, .xls, or .csv. |
| `import.error_file_size` | El archivo supera el tamano maximo permitido ({max} MB). | File exceeds the maximum allowed size ({max} MB). |
| `import.error_corrupt` | No se pudo leer el archivo. Verifique que no este danado. | Could not read the file. Please verify it is not corrupted. |
| `import.error_no_rows` | El archivo no contiene filas de datos validas. | The file contains no valid data rows. |
| `import.error_unreviewed` | Revisa todas las filas marcadas antes de confirmar. | Review all flagged rows before confirming. |
| `import.history_title` | Historial de importaciones | Import history |
| `import.history_col_file` | Archivo | File |
| `import.history_col_status` | Estado | Status |
| `import.history_col_date` | Fecha | Date |
| `import.history_col_rows` | Filas | Rows |
| `import.history_col_matched` | Coincidencias | Matched |
| `import.status_pending` | Pendiente | Pending |
| `import.status_partial` | Parcial | Partial |
| `import.status_complete` | Completado | Complete |
| `import.status_failed` | Fallido | Failed |
| `import.duplicate_warning` | Esta fila crearia una linea duplicada. | This row would create a duplicate line. |

### error.*

| Key | ES | EN |
|---|---|---|
| `error.required` | Este campo es obligatorio. | This field is required. |
| `error.invalid_email` | Ingresa un correo electronico valido. | Enter a valid email address. |
| `error.invalid_amount` | Ingresa un monto mayor a cero. | Enter an amount greater than zero. |
| `error.not_found` | No se encontro el recurso solicitado. | The requested resource was not found. |
| `error.unauthorized` | No tienes acceso a este recurso. | You do not have access to this resource. |
| `error.server` | Error interno. Intenta de nuevo. | Internal error. Please try again. |
| `error.duplicate_budget_line` | Ya existe una linea para esta categoria en este proyecto. | A line for this category already exists in this project. |

### report.*

| Key | ES | EN |
|---|---|---|
| `report.title` | Progreso | Progress |
| `report.planned` | Presupuestado | Budgeted |
| `report.actual` | Ejecutado | Actual |
| `report.variance` | Variacion | Variance |
| `report.over_budget` | Sobre presupuesto | Over budget |
| `report.under_budget` | Bajo presupuesto | Under budget |
| `report.chart_title` | Presupuesto vs. Ejecutado por categoria | Budget vs. Actual by category |
| `report.gauge_title` | Ejecucion total del proyecto | Total project execution |
| `report.export_csv` | Exportar CSV | Export CSV |
| `report.export_xlsx` | Exportar Excel | Export Excel |
| `report.category_col` | Categoria | Category |
| `report.budgeted_col` | Presupuestado | Budgeted |
| `report.actual_col` | Ejecutado | Actual |
| `report.variance_col` | Variacion | Variance |
| `report.pct_col` | % Ejecucion | % Execution |

### room.*

| Key | ES | EN |
|---|---|---|
| `room.title` | Habitaciones | Rooms |
| `room.add_room` | Agregar habitacion | Add room |
| `room.name_label` | Nombre | Name |
| `room.description_label` | Descripcion | Description |
| `room.no_rooms` | Sin habitaciones definidas. | No rooms defined. |
| `room.budget_section` | Presupuesto de la habitacion | Room budget |
| `room.expenses_section` | Gastos de la habitacion | Room expenses |
| `room.total_budgeted` | Total presupuestado | Total budgeted |
| `room.total_spent` | Total ejecutado | Total spent |

---

## Wireframes

### Screen 1 — Login

```
+---------------------------------------------------+
|        Control de Presupuesto de Construccion     |
+---------------------------------------------------+
|                                                   |
|   Correo electronico                              |
|   [tu@correo.com                             ]    |
|                                                   |
|   [        Enviar codigo        ]                 |
|                                                   |
+---------------------------------------------------+
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Page title | Control de Presupuesto de Construccion | Construction Budget Control | `auth.page_title` |
| Email label | Correo electronico | Email address | `auth.email_label` |
| Email placeholder | tu@correo.com | you@email.com | `auth.email_placeholder` |
| Send button | Enviar codigo | Send code | `auth.send_otp_button` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Page container | `st.container` | Centered, max-width 420px |
| Email input | `st.text_input` | type="default", key="login_email" |
| Send button | `st.form_submit_button` inside `st.form` | Submits form; triggers OTP generation |

---

### Screen 2 — OTP Verification

```
+---------------------------------------------------+
|        Control de Presupuesto de Construccion     |
+---------------------------------------------------+
|                                                   |
|   Codigo enviado a tu@correo.com                  |
|                                                   |
|   Codigo de verificacion                          |
|   [000000                                    ]    |
|                                                   |
|   [          Verificar          ]                 |
|                                                   |
|   Reenviar codigo                                 |
|                                                   |
+---------------------------------------------------+
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Info message | Codigo enviado a {email} | Code sent to {email} | `auth.otp_sent` |
| Code label | Codigo de verificacion | Verification code | `auth.otp_label` |
| Code placeholder | 000000 | 000000 | `auth.otp_placeholder` |
| Verify button | Verificar | Verify | `auth.verify_button` |
| Resend link | Reenviar codigo | Resend code | `auth.resend_link` |
| Expired error | El codigo expiro. Solicita uno nuevo. | Code expired. Request a new one. | `auth.otp_expired` |
| Invalid error | Codigo incorrecto. Intento {n} de 5. | Incorrect code. Attempt {n} of 5. | `auth.otp_invalid` |
| Locked error | Demasiados intentos. Solicita un nuevo codigo. | Too many attempts. Request a new code. | `auth.otp_locked` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Info | `st.info` | Shows email address where OTP was sent |
| Code input | `st.text_input` | max_chars=6, key="otp_code" |
| Verify button | `st.form_submit_button` | Calls verify logic |
| Resend link | `st.button` | Outside form; re-sends OTP, resets timer |
| Error messages | `st.error` | Shown on invalid/expired/locked |

---

### Screen 3 — Project List

```
+------------------+------------------------------------+
| [ES]  [EN]       | Mis proyectos          [Nuevo +]   |
|------------------|                                    |
| Proyecto activo  | +----------------------------+     |
| [Ninguno     v]  | | Casa Chapinero            |     |
| + Nuevo proyecto | | Residencial  |  Creado: ... |    |
|------------------|  | Ppto: $80M  Ejec: 12%    |     |
| Inicio           | +----------------------------+     |
| Presupuesto      | +----------------------------+     |
| Gastos           | | Bodega Fontibon           |     |
| Importar         | | Comercial    |  Creado: ... |    |
| Progreso         | | Ppto: $200M  Ejec: 45%    |     |
| Habitaciones     | +----------------------------+     |
| Mi cuenta        |                                    |
|------------------|                                    |
| tu@email.com     |                                    |
| [Cerrar sesion]  |                                    |
+------------------+------------------------------------+
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Page title | Mis proyectos | My projects | `project.list_title` |
| Create button | + Nuevo proyecto | + New project | `project.create_button` |
| Project type: residential | Residencial | Residential | `project.type_badge_residential` |
| Project type: commercial | Comercial | Commercial | `project.type_badge_commercial` |
| Total budget label | Ppto: | Budget: | `project.total_budget` |
| Executed label | Ejec: | Exec: | `project.pct_executed` |
| Empty state | No tienes proyectos. Crea uno para comenzar. | No projects yet. Create one to get started. | `project.no_projects` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Page layout | `st.columns([1, 3])` | Sidebar left, content right |
| Create button | `st.button` | Links to Project Create screen |
| Project cards | `st.container` per project | Click sets `st.session_state["current_project_id"]` |
| Type badge | `st.badge` or styled `st.markdown` | Color: blue = residential, orange = commercial |
| Budget metric | `st.metric` | Shows total budgeted amount |
| Executed % | `st.progress` | Value = pct_executed / 100 |

---

### Screen 4 — Project Create / Edit

```
+------------------+------------------------------------+
| [ES]  [EN]       | Nuevo proyecto                     |
|------------------|                                    |
| Proyecto activo  | Nombre del proyecto *              |
| [Ninguno     v]  | [Remodelacion Casa Bogota     ]    |
| + Nuevo proyecto |                                    |
|------------------|  Tipo de proyecto *                |
| Inicio           | ( ) Residencial  ( ) Comercial     |
| Presupuesto      |                                    |
| Gastos           | Descripcion                        |
| Importar         | [                              ]   |
| Progreso         | [                              ]   |
| Habitaciones     |                                    |
| Mi cuenta        | Moneda                             |
|------------------|  [COP                         v]  |
| tu@email.com     |                                    |
| [Cerrar sesion]  | [Guardar]        [Cancelar]        |
+------------------+------------------------------------+
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Create title | Nuevo proyecto | New project | `project.create_title` |
| Edit title | Editar proyecto | Edit project | `project.edit_title` |
| Name label | Nombre del proyecto | Project name | `project.name_label` |
| Name placeholder | Ej: Remodelacion Casa Bogota | E.g.: Bogota Home Renovation | `project.name_placeholder` |
| Type label | Tipo de proyecto | Project type | `project.type_label` |
| Residential option | Residencial | Residential | `project.type_residential` |
| Commercial option | Comercial | Commercial | `project.type_commercial` |
| Description label | Descripcion | Description | `project.description_label` |
| Currency label | Moneda | Currency | `common.currency` |
| Save button | Guardar | Save | `common.save` |
| Cancel button | Cancelar | Cancel | `common.cancel` |
| Required marker | * Campo obligatorio | * Required field | `common.required_field` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Form wrapper | `st.form("project_form")` | Prevents partial submission |
| Name input | `st.text_input` | max_chars=120, required |
| Type selector | `st.radio` | options=["residential","commercial"], labels via t() |
| Description | `st.text_area` | Optional, max_chars=500 |
| Currency | `st.selectbox` | Default "COP"; options: COP, USD, EUR |
| Save | `st.form_submit_button` | Validates before DB write |
| Cancel | `st.button` (outside form) | Returns to Project List |

---

### Screen 5 — Project Dashboard

```
+------------------+--------------------------------------------+
| [ES]  [EN]       | Casa Chapinero  [Residencial]  [Editar]    |
|------------------|                                            |
| Proyecto activo  | [Presupuesto]  [Ejecutado]  [Saldo]  [%]  |
| [Casa Chap.  v]  |  $80,000,000   $9,600,000  $70,400,000  12%|
| + Nuevo proyecto |                                            |
|------------------|  Presupuesto vs. Ejecutado por categoria   |
| Inicio  <        | +--------------------------------------+   |
| Presupuesto      | | 01 Adq. del Bien  |===|              |  |
| Gastos           | | 02 Costos Blandos |====|             |  |
| Importar         | | 03 Construccion   |=|                |  |
| Progreso         | +--------------------------------------+   |
| Habitaciones     |  [Presupuestado]  [Ejecutado]              |
| Mi cuenta        |                                            |
|------------------|  Accesos rapidos                          |
| tu@email.com     | [Agregar gasto] [Importar] [Ver progreso]  |
| [Cerrar sesion]  |                                            |
+------------------+--------------------------------------------+
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Total budget metric | Presupuesto total | Total budget | `project.total_budget` |
| Spent metric | Ejecutado | Spent | `project.total_spent` |
| Balance metric | Saldo disponible | Available balance | `project.balance` |
| % executed metric | % Ejecutado | % Executed | `project.pct_executed` |
| Chart title | Presupuesto vs. Ejecutado por categoria | Budget vs. Actual by category | `report.chart_title` |
| Planned legend | Presupuestado | Budgeted | `report.planned` |
| Actual legend | Ejecutado | Actual | `report.actual` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Metrics row | `st.columns(4)` with `st.metric` | Delta shows variance vs. budget |
| Bar chart | `st.bar_chart` | Grouped by category; color-coded |
| Quick-action buttons | `st.columns(3)` with `st.button` | Link to Expense, Import, Progress screens |
| Edit project link | `st.button` inline with title | Opens Project Create/Edit in edit mode |

---

### Screen 6 — Budget Setup

```
+------------------+------------------------------------------------+
| [ES]  [EN]       | Presupuesto — Casa Chapinero                   |
|------------------|                                                |
| Proyecto activo  | [+ Agregar linea]                              |
| [Casa Chap.  v]  |                                                |
|                  | 01 Adquisicion del Bien                        |
|------------------|  | Cod  | Descripcion  | Hab  | Monto    | [+] |
| Inicio           |  | 01.01| Precio Comp. | —    | $50,000,000|   |
| Presupuesto <    |  | 01.02| Costos Cier. | —    | $5,000,000 |   |
| Gastos           |                                                |
| Importar         | 02 Costos Blandos                              |
| Progreso         |  | Cod  | Descripcion  | Hab  | Monto    | [+] |
| Habitaciones     |  | 02.01| Diseno Arq.  | —    | $8,000,000 |   |
| Mi cuenta        |                                                |
|------------------|  Total presupuestado: $80,000,000              |
| tu@email.com     |                                                |
| [Cerrar sesion]  |                                                |
+------------------+------------------------------------------------+
```

**Add budget line form (shown inline on "+" click):**
```
| Categoria *        | [01.02 Costos de Cierre          v] |
| Habitacion         | [Todo el proyecto                v] |
| Descripcion        | [Notaria y registro               ] |
| Monto *            | [5000000                          ] |
|                    | [Guardar]  [Cancelar]               |
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Page title | Presupuesto — {project} | Budget — {project} | `budget.title` |
| Add line button | + Agregar linea | + Add line | `budget.add_line` |
| Category column | Categoria | Category | `budget.category_label` |
| Room column | Habitacion | Room | `budget.room_label` |
| Room all | Todo el proyecto | Whole project | `budget.room_all` |
| Description column | Descripcion | Description | `budget.description_label` |
| Amount column | Monto presupuestado | Budgeted amount | `budget.amount_label` |
| Total row | Total presupuestado | Total budgeted | `budget.total_row` |
| Over-budget warning | Esta categoria supera el presupuesto | This category exceeds budget | `budget.over_budget_warning` |
| Saved message | Linea guardada | Line saved | `budget.line_saved` |
| Deleted message | Linea eliminada | Line deleted | `budget.line_deleted` |
| Empty state | Sin lineas de presupuesto. Agrega una. | No budget lines yet. Add one. | `budget.no_lines` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Category grouping | `st.expander` per top-level category | Collapsed by default if no lines |
| Budget lines table | `st.data_editor` | Editable rows; delete icon per row |
| Add line form | `st.form` | Inline below category group |
| Category selector | `st.selectbox` | Options from categories table; grouped |
| Room selector | `st.selectbox` | First option = "Todo el proyecto" (room_id=NULL) |
| Amount input | `st.number_input` | min_value=0, step=1000 |
| Over-budget highlight | `st.warning` | Shown when sum(expenses) > budgeted_amount for category |

---

### Screen 7 — Expense Entry

```
+------------------+------------------------------------------------+
| [ES]  [EN]       | Gastos — Casa Chapinero                        |
|------------------|                                                |
| Proyecto activo  | Linea de presupuesto                           |
| [Casa Chap.  v]  | [01.02 Costos de Cierre - Notaria    v]        |
|                  |   Presupuestado: $5,000,000  Ejecutado: $3,000,000|
|------------------|                                                |
| Inicio           | [+ Registrar gasto]                            |
| Presupuesto      |                                                |
| Gastos       <   | | Proveedor | Descripcion | Monto  | Fecha | |
| Importar         | | Notaria X | Escritura   |$3,000K | 05/01 | |
| Progreso         |                                                |
| Habitaciones     |                                                |
| Mi cuenta        |                                                |
|------------------|                                                |
| tu@email.com     |                                                |
| [Cerrar sesion]  |                                                |
+------------------+------------------------------------------------+
```

**Add expense form:**
```
| Proveedor          | [Notaria Lopez                    ] |
| Descripcion        | [Escritura y registro             ] |
| Monto *            | [3000000                          ] |
| Fecha *            | [2026-05-01                       ] |
| Notas              | [                                 ] |
|                    | [Guardar]   [Cancelar]              |
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Page title | Gastos — {project} | Expenses — {project} | `expense.title` |
| Budget line selector | Linea de presupuesto | Budget line | `expense.budget_line_label` |
| Add expense button | + Registrar gasto | + Record expense | `expense.add_expense` |
| Vendor label | Proveedor | Vendor | `expense.vendor_label` |
| Description label | Descripcion | Description | `expense.description_label` |
| Amount label | Monto | Amount | `expense.amount_label` |
| Date label | Fecha | Date | `expense.date_label` |
| Notes label | Notas | Notes | `expense.notes_label` |
| Saved message | Gasto registrado | Expense recorded | `expense.saved` |
| Deleted message | Gasto eliminado | Expense deleted | `expense.deleted` |
| Empty state | Sin gastos registrados | No expenses recorded | `expense.no_expenses` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Budget line selector | `st.selectbox` | Filters expense table; shows budgeted/spent inline |
| Expense table | `st.data_editor` | Delete icon per row; sortable by date |
| Add form | `st.form("expense_form")` | Hidden until "+" button clicked |
| Vendor input | `st.text_input` | Optional |
| Amount input | `st.number_input` | min_value=0.01, required |
| Date input | `st.date_input` | Default: today |
| Notes input | `st.text_area` | Optional |

---

### Screen 8 — File Import

Three-step flow on one screen; active step advances on user action.

#### Step 1 — Upload

```
+------------------+------------------------------------------------+
| [ES]  [EN]       | Importar presupuesto                           |
|------------------|                                                |
| Proyecto activo  | [1. Cargar] ------ [2. Revisar] --- [3. Confirmar]|
| [Casa Chap.  v]  |                                                |
|                  | Selecciona archivo                             |
|------------------|  [    Arrastra o haz clic para cargar    ]     |
| Inicio           |   Formatos aceptados: .xlsx, .xls, .csv       |
| Presupuesto      |                                                |
| Gastos           |                                                |
| Importar     <   |                                                |
| Progreso         |                                                |
| Habitaciones     |                                                |
| Mi cuenta        |                                                |
|------------------|                                                |
| tu@email.com     |                                                |
| [Cerrar sesion]  |                                                |
+------------------+------------------------------------------------+
```

#### Step 2 — Preview and review

```
| Vista previa (32 filas detectadas)                              |
|                                                                  |
| Las filas marcadas en naranja requieren revision antes          |
| de confirmar.                                                    |
|                                                                  |
| Descripcion original | Categoria asignada | Confianza | Corregir |
| Compra del lote      | 01.01 Precio Comp. |  0.95     | —        |
| Diseño arquitect.    | 02.01 Diseño Arq.  |  0.88     | —        |
| >> Pintura exterior  | ???                |  0.43     | [v]      | <- flagged
| Honorarios notaria   | 01.02.02 Notaria   |  0.91     | —        |
|                                                                  |
| [Confirmar importacion]                [Cancelar]                |
```

#### Step 3 — Confirmation

```
| Importacion completada.                                         |
| 31 filas importadas. 1 fila omitida (sin categoria asignada).   |
|                                                                  |
| [Ver presupuesto]    [Importar otro archivo]                    |
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Page title | Importar presupuesto | Import budget | `import.title` |
| Upload label | Selecciona archivo | Select file | `import.upload_label` |
| Upload help | Formatos aceptados: .xlsx, .xls, .csv | Accepted formats: .xlsx, .xls, .csv | `import.upload_help` |
| Preview title | Vista previa | Preview | `import.preview_title` |
| Original desc col | Descripcion original | Original description | `import.col_original` |
| Category col | Categoria asignada | Assigned category | `import.col_category` |
| Confidence col | Confianza | Confidence | `import.col_confidence` |
| Override col | Corregir | Override | `import.col_override` |
| Amount col | Monto | Amount | `import.col_amount` |
| Confirm button | Confirmar importacion | Confirm import | `import.confirm_button` |
| Cancel button | Cancelar | Cancel | `common.cancel` |
| Low confidence warning | Las filas marcadas requieren revision antes de confirmar. | Flagged rows require review before confirming. | `import.low_confidence_warning` |
| Success message | Importacion completada. {n} filas importadas. | Import complete. {n} rows imported. | `import.success` |
| Error: file type | Tipo de archivo no admitido. Use .xlsx, .xls o .csv. | Unsupported file type. Use .xlsx, .xls, or .csv. | `import.error_file_type` |
| Error: file size | El archivo supera el tamano maximo ({max} MB). | File exceeds the maximum allowed size ({max} MB). | `import.error_file_size` |
| Error: corrupt | No se pudo leer el archivo. Verifique que no este danado. | Could not read the file. Please verify it is not corrupted. | `import.error_corrupt` |
| Error: unreviewed | Revisa todas las filas marcadas antes de confirmar. | Review all flagged rows before confirming. | `import.error_unreviewed` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Progress stepper | `st.steps` or styled `st.columns` | 3 steps: Cargar / Revisar / Confirmar |
| File uploader | `st.file_uploader` | type=["xlsx","xls","csv"]; on upload → parse |
| Preview table | `st.data_editor` | Disabled cols: original, category, confidence. Editable col: override (selectbox per row with confidence < 0.7) |
| Low-confidence rows | Row styling via `st.dataframe` with `Styler` | Background orange for confidence < 0.7 |
| Confirm button | `st.button` | Disabled until all flagged rows have override or are marked skip |
| Cancel button | `st.button` | Discards import_job, returns to step 1 |
| Success message | `st.success` | Shown after commit |

---

### Screen 9 — Progress View

```
+------------------+------------------------------------------------+
| [ES]  [EN]       | Progreso — Casa Chapinero                      |
|------------------|                                                |
| Proyecto activo  | [============================   ] 12%          |
| [Casa Chap.  v]  |  Ejecucion total del proyecto                  |
|                  |                                                |
|------------------|  Presupuesto vs. Ejecutado por categoria       |
| Inicio           | +------------------------------------------+  |
| Presupuesto      | | 01 Adq. del Bien  |=====|               |  |
| Gastos           | | 02 Costos Blandos |====|                |  |
| Importar         | | 03 Construccion   |=|                   |  |
| Progreso     <   | | 04 Cos. Tenencia  |                     |  |
| Habitaciones     | | 05 Mobiliario     |                     |  |
| Mi cuenta        | | 06 Habitaciones   |===|                 |  |
|                  | +------------------------------------------+  |
|------------------|  [Presupuestado]  [Ejecutado]                  |
| tu@email.com     |                                                |
| [Cerrar sesion]  | Tabla de variacion                             |
|                  | | Categoria | Ppto | Ejec | Var | % Ejec |   |
|                  | | 01 ...    | $55M | $10M | $45M|  18%   |   |  <- green
|                  | | 02 ...    | $10M | $12M | -$2M| 120%   |   |  <- red (over)
|                  |                                                |
|                  | [Exportar CSV]   [Exportar Excel]              |
+------------------+------------------------------------------------+
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Page title | Progreso — {project} | Progress — {project} | `report.title` |
| Gauge title | Ejecucion total del proyecto | Total project execution | `report.gauge_title` |
| Chart title | Presupuesto vs. Ejecutado por categoria | Budget vs. Actual by category | `report.chart_title` |
| Planned legend | Presupuestado | Budgeted | `report.planned` |
| Actual legend | Ejecutado | Actual | `report.actual` |
| Variance table title | Tabla de variacion | Variance table | `report.variance` |
| Category col | Categoria | Category | `report.category_col` |
| Budgeted col | Presupuestado | Budgeted | `report.budgeted_col` |
| Actual col | Ejecutado | Actual | `report.actual_col` |
| Variance col | Variacion | Variance | `report.variance_col` |
| % Execution col | % Ejecucion | % Execution | `report.pct_col` |
| Over budget label | Sobre presupuesto | Over budget | `report.over_budget` |
| Export CSV | Exportar CSV | Export CSV | `report.export_csv` |
| Export Excel | Exportar Excel | Export Excel | `report.export_xlsx` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Overall progress bar | `st.progress` + `st.metric` | Value = sum(expenses) / sum(budgeted) |
| Category bar chart | `st.bar_chart` | Two series: budgeted (blue), actual (green/red) |
| Variance table | `st.dataframe` with `Styler` | Over-budget rows highlighted red; under-budget green |
| Export CSV | `st.download_button` | Returns CSV with headers in active language |
| Export Excel | `st.download_button` | Returns .xlsx using openpyxl |

---

### Screen 10 — Room Detail

```
+------------------+------------------------------------------------+
| [ES]  [EN]       | Habitaciones — Casa Chapinero  [+ Agregar]     |
|------------------|                                                |
| Proyecto activo  | [Sala]  [Cocina]  [Alcoba Ppal]  [Banos]       |
| [Casa Chap.  v]  |  <- tab per room                               |
|                  |                                                |
|------------------|  Sala                                          |
| Inicio           |  Presupuestado: $8,000,000   Ejecutado: $1,200,000|
| Presupuesto      |                                                |
| Gastos           |  Presupuesto de la habitacion                  |
| Importar         |  | Categoria     | Monto        |             |
| Progreso         |  | 05.01 Muebles | $5,000,000   |             |
| Habitaciones <   |  | 05.02 Textiles| $3,000,000   |             |
| Mi cuenta        |                                                |
|                  |  Gastos de la habitacion                       |
|------------------|  | Proveedor | Desc   | Monto    | Fecha |    |
| tu@email.com     |  | Muebles X | Sofa   | $800,000 | 05/10 |    |
| [Cerrar sesion]  |                                                |
+------------------+------------------------------------------------+
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Page title | Habitaciones — {project} | Rooms — {project} | `room.title` |
| Add room button | + Agregar habitacion | + Add room | `room.add_room` |
| Room name label | Nombre | Name | `room.name_label` |
| Description label | Descripcion | Description | `room.description_label` |
| Empty state | Sin habitaciones definidas. | No rooms defined. | `room.no_rooms` |
| Budget section | Presupuesto de la habitacion | Room budget | `room.budget_section` |
| Expenses section | Gastos de la habitacion | Room expenses | `room.expenses_section` |
| Total budgeted | Total presupuestado | Total budgeted | `room.total_budgeted` |
| Total spent | Total ejecutado | Total spent | `room.total_spent` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Room tabs | `st.tabs` | One tab per room; "+" opens add-room form |
| Budget table | `st.dataframe` | budget_lines filtered by room_id |
| Expense table | `st.data_editor` | expenses filtered via budget_lines.room_id |
| Add room form | `st.form` | name (required), description (optional) |
| Room metrics | `st.metric` | Budgeted, spent, balance per room |

---

### Screen 11 — User Management

```
+------------------+------------------------------------------------+
| [ES]  [EN]       | Mi cuenta                                      |
|------------------|                                                |
| Proyecto activo  | Correo electronico                             |
| [Casa Chap.  v]  | tu@correo.com                                  |
|                  |                                                |
|------------------|  Sesion activa                                 |
| Inicio           |  Iniciada el 2026-05-28 14:32                  |
| Presupuesto      |                                                |
| Gastos           |                                                |
| Importar         |  [    Cerrar sesion    ]                        |
| Progreso         |                                                |
| Habitaciones     |                                                |
| Mi cuenta    <   |                                                |
|------------------|                                                |
| tu@email.com     |                                                |
| [Cerrar sesion]  |                                                |
+------------------+------------------------------------------------+
```

#### Bilingual copy

| Element | ES | EN | i18n key |
|---|---|---|---|
| Page title | Mi cuenta | My account | `nav.account` |
| Email label | Correo electronico | Email address | `auth.email_label` |
| Active session label | Sesion activa | Active session | `auth.welcome` |
| Logout button | Cerrar sesion | Log out | `nav.logout` |

#### Streamlit components

| Element | Component | Notes |
|---|---|---|
| Email display | `st.text` + `st.caption` | Read-only; no edit (auth is OTP-based) |
| Session info | `st.info` | Shows session start time |
| Logout button | `st.button` | Clears `st.session_state`; redirects to Login |

---

## Import history (embedded in Screen 8)

Shown below the upload area when past imports exist for the current project.

```
| Historial de importaciones                                      |
| Archivo            | Estado     | Fecha        | Filas | Match |
| presupuesto_v1.xlsx| Completado | 2026-05-01   | 32    | 31    |
| costos_soft.csv    | Parcial    | 2026-04-15   | 18    | 14    |
| borrador.xlsx      | Fallido    | 2026-04-10   | —     | —     |
```

| Element | ES | EN | i18n key |
|---|---|---|---|
| Section title | Historial de importaciones | Import history | `import.history_title` |
| File col | Archivo | File | `import.history_col_file` |
| Status col | Estado | Status | `import.history_col_status` |
| Date col | Fecha | Date | `import.history_col_date` |
| Rows col | Filas | Rows | `import.history_col_rows` |
| Matched col | Coincidencias | Matched | `import.history_col_matched` |
| Status: complete | Completado | Complete | `import.status_complete` |
| Status: partial | Parcial | Partial | `import.status_partial` |
| Status: failed | Fallido | Failed | `import.status_failed` |
| Status: pending | Pendiente | Pending | `import.status_pending` |

Streamlit component: `st.dataframe` — status column styled with color badges.
