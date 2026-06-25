"use client";
import { useEffect, useState } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { t } from "@/lib/lang";

const MODULES = [
  { key: "dashboard",    en: "Dashboard",     es: "Dashboard" },
  { key: "budget",       en: "Presupuesto",   es: "Presupuesto" },
  { key: "expenses",     en: "Pagos",         es: "Pagos" },
  { key: "vendors",      en: "Proveedores",   es: "Proveedores" },
  { key: "trazabilidad", en: "Trazabilidad",  es: "Trazabilidad" },
  { key: "import",       en: "Importar",      es: "Importar" },
  { key: "account",      en: "Cuenta",        es: "Cuenta" },
  { key: "profile",      en: "Perfil",        es: "Perfil" },
  { key: "admin",        en: "Admin",         es: "Admin" },
];

const ROLES = ["superadmin", "admin", "standard", "viewer", "approver"];

const ROLE_STYLE: Record<string, string> = {
  superadmin: "text-red-400   bg-red-400/10   border-red-400/40",
  admin:      "text-orange-400 bg-orange-400/10 border-orange-400/40",
  standard:   "text-blue-400  bg-blue-400/10  border-blue-400/40",
  viewer:     "text-gray-400  bg-gray-400/10  border-gray-400/40",
  approver:   "text-purple-400 bg-purple-400/10 border-purple-400/40",
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

function parsePagesFromDB(raw: string | null): string[] | null {
  if (raw === null) return null;
  try { return JSON.parse(raw) as string[]; } catch { return null; }
}

type Draft = { role: string; is_budget_approver: boolean; allowed_pages: string[] | null };

export default function AdminPage() {
  const lang = useLanguage();

  const [users,   setUsers]   = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);
  const [drafts,  setDrafts]  = useState<Record<number, Draft>>({});
  const [saving,  setSaving]  = useState<number | null>(null);
  const [saved,   setSaved]   = useState<number | null>(null);

  async function load() {
    const res = await fetch("/api/admin/users");
    if (res.status === 403) { setError(t("adm_no_access", lang)); setLoading(false); return; }
    const data: User[] = await res.json();
    setUsers(data);
    const init: Record<number, Draft> = {};
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

  function patch(uid: number, p: Partial<Draft>) {
    setDrafts(prev => ({ ...prev, [uid]: { ...prev[uid], ...p } }));
  }

  function togglePage(uid: number, key: string) {
    const cur = drafts[uid]?.allowed_pages;
    if (cur === null) {
      patch(uid, { allowed_pages: MODULES.map(m => m.key).filter(k => k !== key) });
    } else {
      const next = cur.includes(key) ? cur.filter(k => k !== key) : [...cur, key];
      patch(uid, { allowed_pages: next.length === MODULES.length ? null : next });
    }
  }

  function isAllowed(uid: number, key: string) {
    const p = drafts[uid]?.allowed_pages;
    return p === null || p.includes(key);
  }

  async function save(uid: number) {
    const d = drafts[uid];
    if (!d) return;
    setSaving(uid);
    await fetch(`/api/admin/users/${uid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: d.role, is_budget_approver: d.is_budget_approver, allowed_pages: d.allowed_pages }),
    });
    setSaving(null);
    setSaved(uid);
    setTimeout(() => setSaved(null), 2000);
    load();
  }

  if (loading) return <p className="text-gray-400">{t("lbl_loading", lang)}</p>;
  if (error)   return <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-6 text-red-400">{error}</div>;

  return (
    <div>
      <div className="mb-5">
        <h1 className="text-2xl font-bold text-white">{t("adm_title", lang)}</h1>
        <p className="text-gray-400 text-sm mt-0.5">{users.length} {t("adm_count", lang)}</p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-sm border-collapse" style={{ minWidth: "1000px" }}>
          {/* Header */}
          <thead>
            <tr className="bg-gray-900 border-b border-gray-800">
              <th className="text-left px-3 py-3 text-xs text-gray-400 uppercase tracking-wider font-semibold w-48">
                {lang === "es" ? "Correo" : "Email"}
              </th>
              <th className="text-left px-3 py-3 text-xs text-gray-400 uppercase tracking-wider font-semibold w-32">
                {lang === "es" ? "Usuario" : "Username"}
              </th>
              <th className="text-left px-3 py-3 text-xs text-gray-400 uppercase tracking-wider font-semibold w-32">
                {lang === "es" ? "Rol" : "Role"}
              </th>
              {MODULES.map(m => (
                <th key={m.key} className="text-center px-2 py-3 text-xs text-gray-400 uppercase tracking-wider font-semibold">
                  <div className="flex flex-col items-center gap-0.5">
                    <span style={{ writingMode: "vertical-rl", transform: "rotate(180deg)", whiteSpace: "nowrap", fontSize: "10px" }}>
                      {lang === "es" ? m.es : m.en}
                    </span>
                  </div>
                </th>
              ))}
              <th className="text-center px-2 py-3 text-xs text-gray-400 uppercase tracking-wider font-semibold">
                <div style={{ writingMode: "vertical-rl", transform: "rotate(180deg)", whiteSpace: "nowrap", fontSize: "10px" }}>
                  {lang === "es" ? "Aprobador" : "Approver"}
                </div>
              </th>
              <th className="px-3 py-3 w-24" />
            </tr>
          </thead>

          {/* Rows */}
          <tbody>
            {users.map((u, idx) => {
              const d = drafts[u.id] ?? { role: "standard", is_budget_approver: false, allowed_pages: null };
              const isEven = idx % 2 === 0;
              return (
                <tr
                  key={u.id}
                  className={`border-b border-gray-800/60 transition-colors hover:bg-gray-800/30 ${isEven ? "bg-gray-900" : "bg-gray-900/60"}`}
                >
                  {/* Email */}
                  <td className="px-3 py-2.5">
                    <p className="text-gray-200 text-xs truncate max-w-[180px]" title={u.email}>{u.email}</p>
                  </td>

                  {/* Username */}
                  <td className="px-3 py-2.5">
                    <span className="text-gray-300 font-mono text-xs">{u.username ?? "—"}</span>
                  </td>

                  {/* Role */}
                  <td className="px-3 py-2.5">
                    <select
                      value={d.role}
                      onChange={e => patch(u.id, { role: e.target.value })}
                      className={`text-xs font-semibold rounded-lg px-2 py-1 border cursor-pointer focus:outline-none focus:border-orange-500 bg-transparent w-full ${ROLE_STYLE[d.role] ?? ROLE_STYLE.standard}`}
                    >
                      {ROLES.map(r => (
                        <option key={r} value={r} className="bg-gray-900 text-white">{r}</option>
                      ))}
                    </select>
                  </td>

                  {/* Module checkboxes */}
                  {MODULES.map(m => (
                    <td key={m.key} className="px-2 py-2.5 text-center">
                      <input
                        type="checkbox"
                        checked={isAllowed(u.id, m.key)}
                        onChange={() => togglePage(u.id, m.key)}
                        className="w-4 h-4 accent-orange-500 cursor-pointer"
                      />
                    </td>
                  ))}

                  {/* Approver checkbox */}
                  <td className="px-2 py-2.5 text-center">
                    <input
                      type="checkbox"
                      checked={d.is_budget_approver}
                      onChange={e => patch(u.id, { is_budget_approver: e.target.checked })}
                      className="w-4 h-4 accent-orange-500 cursor-pointer"
                    />
                  </td>

                  {/* Save */}
                  <td className="px-3 py-2.5 text-center">
                    {saved === u.id ? (
                      <span className="text-green-400 text-xs font-semibold">✓</span>
                    ) : (
                      <button
                        onClick={() => save(u.id)}
                        disabled={saving === u.id}
                        className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap"
                      >
                        {saving === u.id
                          ? "…"
                          : (lang === "es" ? "Guardar" : "Save")}
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
