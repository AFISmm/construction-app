export type Lang = "en" | "es";
export const STORAGE_KEY = "ck_lang";
export const COOKIE_KEY  = "ck_lang";

// ─── Translation dictionary ───────────────────────────────────────────────────

const T = {
  // ── Sidebar / nav ──
  nav_dashboard:      { en: "Dashboard",    es: "Dashboard" },
  nav_budget:         { en: "Budget",       es: "Presupuesto" },
  nav_payments:       { en: "Payments",     es: "Pagos" },
  nav_vendors:        { en: "Vendors",      es: "Proveedores" },
  nav_versioning:     { en: "Versioning",   es: "Trazabilidad" },
  nav_import:         { en: "Import",       es: "Importar" },
  nav_account:        { en: "Account",      es: "Cuenta" },
  nav_profile:        { en: "Profile",      es: "Perfil" },
  nav_admin:          { en: "Admin",        es: "Admin" },
  lbl_client:         { en: "Client",       es: "Cliente" },
  lbl_subproject:     { en: "Subproject",   es: "Subproyecto" },
  lbl_no_projects:    { en: "No projects",  es: "Sin proyectos" },
  btn_sign_out:       { en: "Sign out",     es: "Cerrar sesión" },
  lbl_projects:       { en: "Projects",     es: "Proyectos" },

  // ── Common ──
  lbl_loading:        { en: "Loading…",     es: "Cargando…" },
  lbl_select_project: { en: "Select a project from the sidebar to continue.", es: "Selecciona un proyecto en el menú lateral para continuar." },
  btn_save:           { en: "Save",         es: "Guardar" },
  btn_cancel:         { en: "Cancel",       es: "Cancelar" },
  btn_delete:         { en: "Delete",       es: "Eliminar" },
  lbl_total:          { en: "Total",        es: "Total" },
  lbl_no_data:        { en: "No data yet.", es: "Sin datos aún." },

  // ── Column headers ──
  col_category:       { en: "Category",           es: "Categoría" },
  col_estimated:      { en: "Estimated Budget",    es: "Presupuesto Estimado" },
  col_adjusted:       { en: "Adjusted Budget",     es: "Presupuesto Ajustado" },
  col_paid:           { en: "Payments to Date",    es: "Pagos a la Fecha" },
  col_balance:        { en: "Balance",             es: "Balance" },

  // ── Dashboard ──
  dash_subtitle:      { en: "Budget Dashboard",    es: "Dashboard de Presupuesto" },
  dash_no_lines:      { en: "No budget lines with values yet.", es: "Sin líneas de presupuesto con valores aún." },

  // ── Budget ──
  budget_title_suffix: { en: "— Budget",           es: "— Presupuesto" },
  budget_lines_count:  { en: "lines with values",  es: "líneas con valores" },
  budget_of:           { en: "of",                 es: "de" },

  // ── Payments / Expenses ──
  pay_title:           { en: "Payments",            es: "Pagos" },
  pay_count:           { en: "payments",            es: "pagos" },
  pay_add:             { en: "+ Add Payment",       es: "+ Agregar Pago" },
  pay_no_data:         { en: "No payments recorded yet.", es: "Sin pagos registrados aún." },
  pay_col_desc:        { en: "Description",         es: "Descripción" },
  pay_col_vendor:      { en: "Vendor",              es: "Proveedor" },
  pay_col_category:    { en: "Category",            es: "Categoría" },
  pay_col_amount:      { en: "Payment",             es: "Monto" },
  pay_col_date:        { en: "Date",                es: "Fecha" },
  pay_form_line:       { en: "Budget Line",         es: "Línea de Presupuesto" },
  pay_form_select:     { en: "Select a line…",      es: "Selecciona una línea…" },
  pay_form_vendor:     { en: "Vendor",              es: "Proveedor" },
  pay_form_desc:       { en: "Description",         es: "Descripción" },
  pay_form_amount:     { en: "Amount",              es: "Monto" },
  pay_form_date:       { en: "Date",                es: "Fecha" },
  pay_btn_save:        { en: "Save Payment",        es: "Guardar Pago" },
  pay_btn_saving:      { en: "Saving…",             es: "Guardando…" },
  pay_confirm_del:     { en: "Delete this payment?", es: "¿Eliminar este pago?" },

  // ── Vendors ──
  ven_title:           { en: "Vendors",             es: "Proveedores" },
  ven_count:           { en: "vendors registered",  es: "proveedores registrados" },
  ven_add:             { en: "+ Add Vendor",         es: "+ Agregar Proveedor" },
  ven_no_data:         { en: "No vendors registered yet.", es: "Sin proveedores registrados aún." },
  ven_col_company:     { en: "Company",             es: "Empresa" },
  ven_col_contact:     { en: "Contact",             es: "Contacto" },
  ven_col_trade:       { en: "Trade",               es: "Especialidad" },
  ven_col_phone:       { en: "Phone",               es: "Teléfono" },
  ven_col_status:      { en: "Status",              es: "Estado" },
  ven_form_company:    { en: "Company Name",        es: "Nombre de Empresa" },
  ven_form_contact:    { en: "Contact Name",        es: "Nombre de Contacto" },
  ven_form_phone:      { en: "Phone",               es: "Teléfono" },
  ven_form_email:      { en: "Email",               es: "Correo" },
  ven_form_trade:      { en: "Trade / Specialty",   es: "Especialidad / Oficio" },
  ven_form_nit:        { en: "NIT / Tax ID",        es: "NIT / ID Fiscal" },
  ven_form_notes:      { en: "Notes",               es: "Notas" },
  ven_btn_save:        { en: "Save Vendor",         es: "Guardar Proveedor" },
  ven_btn_saving:      { en: "Saving…",             es: "Guardando…" },
  ven_status_pending:  { en: "Pending",             es: "Pendiente" },
  ven_status_active:   { en: "Active",              es: "Activo" },
  ven_status_inactive: { en: "Inactive",            es: "Inactivo" },
  ven_confirm_del:     { en: "Delete this vendor?", es: "¿Eliminar este proveedor?" },

  // ── Versioning / Trazabilidad ──
  traz_title:          { en: "Budget Versioning",   es: "Trazabilidad de Presupuesto" },
  traz_count:          { en: "versions recorded",   es: "versiones registradas" },
  traz_version:        { en: "version",             es: "versión" },
  traz_no_data:        { en: "No budget versions have been created yet.", es: "No se han creado versiones de presupuesto aún." },
  traz_no_data_hint:   { en: "Versions are created when a budget snapshot is saved from the Budget page.", es: "Las versiones se crean al guardar un snapshot desde la página de Presupuesto." },
  traz_col_version:    { en: "Version",             es: "Versión" },
  traz_col_budget:     { en: "Budget",              es: "Presupuesto" },
  traz_col_desc:       { en: "Description",         es: "Descripción" },
  traz_col_type:       { en: "Type",                es: "Tipo" },
  traz_col_date:       { en: "Date",                es: "Fecha" },
  traz_created_by:     { en: "Created by",          es: "Creado por" },
  traz_status:         { en: "Status",              es: "Estado" },

  // ── Import ──
  imp_title:           { en: "Import from CSV",     es: "Importar desde CSV" },
  imp_subtitle:        { en: "Upload a CSV file to create budget lines. Required columns:", es: "Sube un archivo CSV para crear líneas de presupuesto. Columnas requeridas:" },
  imp_click:           { en: "Click to select a CSV file", es: "Haz clic para seleccionar un archivo CSV" },
  imp_csv_only:        { en: "CSV files only",      es: "Solo archivos CSV" },
  imp_no_rows:         { en: "No valid rows found. Verify CSV format.", es: "No se encontraron filas válidas. Verifica el formato del CSV." },
  imp_success:         { en: "Import complete",     es: "Importación completa" },
  imp_result:          { en: "lines imported",      es: "líneas importadas" },
  imp_skipped:         { en: "skipped (invalid category or amount)", es: "omitidas (categoría o monto inválido)" },
  imp_preview:         { en: "rows parsed — preview", es: "filas leídas — vista previa" },
  imp_btn:             { en: "Import",              es: "Importar" },
  imp_btn_loading:     { en: "Importing…",          es: "Importando…" },
  imp_col_code:        { en: "Category Code",       es: "Código de Categoría" },
  imp_col_desc:        { en: "Description",         es: "Descripción" },
  imp_col_amount:      { en: "Amount",              es: "Monto" },
  imp_fail:            { en: "Import failed.",      es: "La importación falló." },

  // ── Account ──
  acc_title:           { en: "Account",             es: "Cuenta" },
  acc_section:         { en: "Change Password",     es: "Cambiar Contraseña" },
  acc_current:         { en: "Current Password",    es: "Contraseña Actual" },
  acc_new:             { en: "New Password",        es: "Nueva Contraseña" },
  acc_confirm:         { en: "Confirm New Password", es: "Confirmar Nueva Contraseña" },
  acc_btn:             { en: "Update Password",     es: "Actualizar Contraseña" },
  acc_btn_saving:      { en: "Saving…",             es: "Guardando…" },
  acc_mismatch:        { en: "Passwords do not match.", es: "Las contraseñas no coinciden." },
  acc_too_short:       { en: "New password must be at least 8 characters.", es: "La nueva contraseña debe tener al menos 8 caracteres." },
  acc_success:         { en: "Password changed successfully.", es: "Contraseña actualizada correctamente." },

  // ── Profile ──
  prof_title:          { en: "Extended Profile",    es: "Perfil Extendido" },
  prof_first:          { en: "First Name",          es: "Nombre" },
  prof_middle:         { en: "Middle Name",         es: "Segundo Nombre" },
  prof_last:           { en: "Last Name",           es: "Apellido" },
  prof_phone:          { en: "Phone",               es: "Teléfono" },
  prof_company:        { en: "Company Name",        es: "Nombre de Empresa" },
  prof_email:          { en: "Contact Email",       es: "Correo de Contacto" },
  prof_category:       { en: "Category",            es: "Categoría" },
  prof_select:         { en: "Select…",             es: "Selecciona…" },
  prof_btn:            { en: "Save Profile",        es: "Guardar Perfil" },
  prof_btn_saving:     { en: "Saving…",             es: "Guardando…" },
  prof_saved:          { en: "Profile saved.",      es: "Perfil guardado." },
  prof_fail:           { en: "Failed to save profile.", es: "Error al guardar el perfil." },

  // ── Admin ──
  adm_title:           { en: "Admin Panel",         es: "Panel de Administración" },
  adm_count:           { en: "registered users",    es: "usuarios registrados" },
  adm_col_user:        { en: "User",                es: "Usuario" },
  adm_col_username:    { en: "Username",            es: "Usuario" },
  adm_col_role:        { en: "Role",                es: "Rol" },
  adm_col_joined:      { en: "Joined",              es: "Registro" },
  adm_no_access:       { en: "Admin access required.", es: "Se requiere acceso de administrador." },
} as const;

export type TKey = keyof typeof T;

export function t(key: TKey, lang: Lang): string {
  return T[key][lang];
}

// ─── Client helpers ───────────────────────────────────────────────────────────

export function getLang(): Lang {
  if (typeof window === "undefined") return "en";
  return (localStorage.getItem(STORAGE_KEY) as Lang) ?? "en";
}

export function setLang(lang: Lang) {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, lang);
  document.cookie = `${COOKIE_KEY}=${lang}; path=/; max-age=31536000; SameSite=Lax`;
}
