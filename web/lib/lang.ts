export type Lang = "en" | "es";

const T = {
  // Nav
  nav_dashboard:    { en: "Dashboard",  es: "Dashboard" },
  nav_budget:       { en: "Budget",     es: "Presupuesto" },
  nav_payments:     { en: "Payments",   es: "Pagos" },
  nav_vendors:      { en: "Vendors",    es: "Proveedores" },
  nav_versioning:   { en: "Versioning", es: "Trazabilidad" },
  nav_import:       { en: "Import",     es: "Importar" },
  nav_account:      { en: "Account",    es: "Cuenta" },
  nav_profile:      { en: "Profile",    es: "Perfil" },
  nav_admin:        { en: "Admin",      es: "Admin" },
  // Sidebar
  lbl_client:       { en: "Client",     es: "Cliente" },
  lbl_subproject:   { en: "Subproject", es: "Subproyecto" },
  lbl_no_projects:  { en: "No projects", es: "Sin proyectos" },
  btn_sign_out:     { en: "Sign out",   es: "Cerrar sesión" },
  // Common
  lbl_loading:      { en: "Loading…",   es: "Cargando…" },
  lbl_select_project: { en: "Select a project.", es: "Selecciona un proyecto." },
  btn_save:         { en: "Save",       es: "Guardar" },
  btn_cancel:       { en: "Cancel",     es: "Cancelar" },
  btn_add:          { en: "Add",        es: "Agregar" },
  btn_delete:       { en: "Delete",     es: "Eliminar" },
  // Dashboard / Budget
  col_category:     { en: "Category",   es: "Categoría" },
  col_estimated:    { en: "Estimated Budget",  es: "Presupuesto Estimado" },
  col_adjusted:     { en: "Adjusted Budget",   es: "Presupuesto Ajustado" },
  col_paid:         { en: "Payments to Date",  es: "Pagos a la Fecha" },
  col_balance:      { en: "Balance",    es: "Balance" },
} as const;

export type TKey = keyof typeof T;

export function t(key: TKey, lang: Lang): string {
  return T[key][lang];
}

export const STORAGE_KEY = "ck_lang";

export function getLang(): Lang {
  if (typeof window === "undefined") return "en";
  return (localStorage.getItem(STORAGE_KEY) as Lang) ?? "en";
}

export function setLang(lang: Lang) {
  if (typeof window !== "undefined") localStorage.setItem(STORAGE_KEY, lang);
}
