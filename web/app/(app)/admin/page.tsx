"use client";
import { useEffect, useState } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { t } from "@/lib/lang";

const MODULES = [
  { key: "dashboard",    labelEn: "Dashboard",   labelEs: "Dashboard" },
  { key: "budget",       labelEn: "Budget",       labelEs: "Presupuesto" },
  { key: "expenses",     labelEn: "Payments",     labelEs: "Pagos" },
  { key: "vendors",      labelEn: "Vendors",      labelEs: "Proveedores" },
  { key: "trazabilidad", labelEn: "Versioning",   labelEs: "Trazabilidad" },
  { key: "import",       labelEn: "Import",       labelEs: "Importar" },
  { key: "account",      labelEn: "Account",      labelEs: "Cuenta" },
  { key: "profile",      labelEn: "Profile",      labelEs: "Perfil" },
  { key: "admin",        labelEn: "Admin",        labelEs: "Admin" },
];

const ROLES = ["standard", "admin", "viewer", "approver"];

const ROLE_STYLE: Record<string, string> = {
  admin:    "text-orange-400 bg-orange-400/10 border-orange-400/30",
  standard: "text-blue-400  bg-blue-400/10  border-blue-400/30",
  viewer:   "text-gray-400  bg-gray-400/10  border-gray-400/30",
  approver: "text-purple-400 bg-purple-400/10 border-purple-400/30",
};

interface UserPerm {
  role: string;
  allowed_pages: string | null;
  is_budget_approver: boolean | null;
}

interface User {
  id: number;
  email: string;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  created_at: string;
  user_permissions: UserPerm | null;
}

// null allowed_pages = full access
function parsePagesFromDB(raw: string | null): string[] | null {
  if (raw === null) return null;
  try { return JSON.parse(raw) as string[]; } catch { return null; }
}

export default function AdminPage() {
  const lang = useLanguage();

  const [users,    setUsers]    = useState<User[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);
  const [expanded, setExpanded] = useState<number | null>(null);

  // draft edits per user id
  const [drafts, setDrafts] = useState<Record<number, {
    role: string;
    is_budget_approver: boolean;
    allowed_pages: string[] | null; // null = all access
  }>>({});

  const [saving, setSaving] = useState<number | null>(null);
  const [saved,  setSaved]  = useState<number | null>(null);

  async function load() {
    const res = await fetch("/api/admin/users");
    if (res.status === 403) { setError(t("adm_no_access", lang)); setLoading(false); return; }
    const data: User[] = await res.json();
    setUsers(data);
    // initialise drafts
    const init: typeof drafts = {};
    for (const u of data) {
      init[u.id] = {
        role:               u.user_permissions?.role ?? "standard",
        is_budget_approver: u.user_permissions?.is_budget_approver ?? false,
        allowed_pages:      parsePagesFromDB(u.user_permissions?.allowed_pages ?? null),
      };
    }
    setDrafts(init);
    setLoading(false);
  }

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function updateDraft(userId: number, patch: Partial<typeof drafts[number]>) {
    setDrafts(prev => ({ ...prev, [userId]: { ...prev[userId], ...patch } }));
  }

  function togglePage(userId: number, pageKey: string) {
    const current = drafts[userId]?.allowed_pages;
    if (current === null) {
      // was full access → restrict to all except this one
      const allExcept = MODULES.map(m => m.key).filter(k => k !== pageKey);
      updateDraft(userId, { allowed_pages: allExcept });
    } else {
      const next = current.includes(pageKey)
        ? current.filter(k => k !== pageKey)
        : [...current, pageKey];
      // if all checked again → back to null (full access)
      updateDraft(userId, { allowed_pages: next.length === MODULES.length ? null : next });
    }
  }

  function isPageAllowed(userId: number, pageKey: string): boolean {
    const pages = drafts[userId]?.allowed_pages;
    return pages === null || pages.includes(pageKey);
  }

  async function handleSave(userId: number) {
    const d = drafts[userId];
    if (!d) return;
    setSaving(userId);
    await fetch(`/api/admin/users/${userId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role:               d.role,
        is_budget_approver: d.is_budget_approver,
        allowed_pages:      d.allowed_pages,
      }),
    });
    setSaving(null);
    setSaved(userId);
    setTimeout(() => setSaved(null), 2000);
    load();
  }

  if (loading) return <p className="text-gray-400">{t("lbl_loading", lang)}</p>;
  if (error)   return <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-6 text-red-400">{error}</div>;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">{t("adm_title", lang)}</h1>
        <p className="text-gray-400 text-sm mt-0.5">{users.length} {t("adm_count", lang)}</p>
      </div>

      <div className="space-y-2">
        {users.map(u => {
          const d = drafts[u.id] ?? { role: "standard", is_budget_approver: false, allowed_pages: null };
          const isOpen = expanded === u.id;
          const displayName = u.first_name && u.last_name
            ? `${u.first_name} ${u.last_name}`
            : u.username ?? u.email;

          return (
            <div key={u.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
              {/* Row */}
              <div className="grid grid-cols-[2fr_1.5fr_1fr_auto_auto] gap-4 px-4 py-3 items-center">
                {/* User info */}
                <div>
                  <p className="text-gray-100 font-medium text-sm">{displayName}</p>
                  <p className="text-gray-500 text-xs truncate">{u.email}</p>
                </div>

                {/* Username */}
                <span className="text-gray-400 text-sm font-mono">{u.username ?? "—"}</span>

                {/* Role dropdown */}
                <select
                  value={d.role}
                  onChange={e => updateDraft(u.id, { role: e.target.value })}
                  className={`text-xs font-semibold rounded-lg px-2 py-1.5 border cursor-pointer focus:outline-none focus:border-orange-500 bg-transparent ${ROLE_STYLE[d.role] ?? ""}`}
                >
                  {ROLES.map(r => <option key={r} value={r} className="bg-gray-900 text-white">{r}</option>)}
                </select>

                {/* Approver checkbox */}
                <label className="flex items-center gap-2 cursor-pointer select-none" title={lang === "es" ? "Aprobador de presupuesto" : "Budget approver"}>
                  <input
                    type="checkbox"
                    checked={d.is_budget_approver}
                    onChange={e => updateDraft(u.id, { is_budget_approver: e.target.checked })}
                    className="w-4 h-4 accent-orange-500 cursor-pointer"
                  />
                  <span className="text-xs text-gray-400 hidden lg:block">
                    {lang === "es" ? "Aprobador" : "Approver"}
                  </span>
                </label>

                {/* Expand button */}
                <button
                  onClick={() => setExpanded(isOpen ? null : u.id)}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition-colors ${
                    isOpen
                      ? "border-orange-500 text-orange-400 bg-orange-500/10"
                      : "border-gray-700 text-gray-400 hover:border-gray-500"
                  }`}
                >
                  {lang === "es" ? "Módulos" : "Modules"} {isOpen ? "▲" : "▼"}
                </button>
              </div>

              {/* Expanded: module permissions */}
              {isOpen && (
                <div className="border-t border-gray-800 px-4 py-4 bg-gray-800/20">
                  <p className="text-xs text-gray-400 uppercase tracking-wider mb-3">
                    {lang === "es" ? "Módulos permitidos" : "Allowed modules"}
                    <span className="ml-2 text-gray-600 normal-case">
                      ({lang === "es" ? "desmarca para restringir acceso" : "uncheck to restrict access"})
                    </span>
                  </p>

                  <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5 gap-3 mb-4">
                    {MODULES.map(m => {
                      const allowed = isPageAllowed(u.id, m.key);
                      return (
                        <label
                          key={m.key}
                          className={`flex items-center gap-2 cursor-pointer rounded-lg border px-3 py-2 transition-colors select-none ${
                            allowed
                              ? "border-orange-500/40 bg-orange-500/5 text-gray-200"
                              : "border-gray-700 bg-gray-800/40 text-gray-500"
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={allowed}
                            onChange={() => togglePage(u.id, m.key)}
                            className="w-3.5 h-3.5 accent-orange-500 cursor-pointer flex-shrink-0"
                          />
                          <span className="text-xs font-medium">
                            {lang === "es" ? m.labelEs : m.labelEn}
                          </span>
                        </label>
                      );
                    })}
                  </div>

                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => handleSave(u.id)}
                      disabled={saving === u.id}
                      className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-sm font-semibold px-4 py-1.5 rounded-lg transition-colors"
                    >
                      {saving === u.id
                        ? (lang === "es" ? "Guardando…" : "Saving…")
                        : (lang === "es" ? "Guardar cambios" : "Save changes")}
                    </button>
                    {saved === u.id && (
                      <span className="text-green-400 text-sm">
                        {lang === "es" ? "✓ Guardado" : "✓ Saved"}
                      </span>
                    )}
                    <button
                      onClick={() => setExpanded(null)}
                      className="text-gray-500 hover:text-gray-300 text-sm ml-auto"
                    >
                      {lang === "es" ? "Cerrar" : "Close"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
