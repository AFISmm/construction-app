"use client";
import { useEffect, useState } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { t } from "@/lib/lang";

// ─── Constantes ───────────────────────────────────────────────────────────────

const MODULES = [
  { key: "dashboard",    en: "Dashboard",    es: "Dashboard" },
  { key: "budget",       en: "Presupuesto",  es: "Presupuesto" },
  { key: "expenses",     en: "Pagos",        es: "Pagos" },
  { key: "vendors",      en: "Proveedores",  es: "Proveedores" },
  { key: "trazabilidad", en: "Trazabilidad", es: "Trazabilidad" },
  { key: "import",       en: "Importar",     es: "Importar" },
  { key: "account",      en: "Cuenta",       es: "Cuenta" },
  { key: "profile",      en: "Perfil",       es: "Perfil" },
  { key: "admin",        en: "Admin",        es: "Admin" },
];

const ROLES = ["superadmin", "admin", "standard", "viewer", "approver"];

const ROLE_STYLE: Record<string, string> = {
  superadmin: "text-red-400    bg-red-400/10    border-red-400/40",
  admin:      "text-orange-400 bg-orange-400/10 border-orange-400/40",
  standard:   "text-blue-400   bg-blue-400/10   border-blue-400/40",
  viewer:     "text-gray-400   bg-gray-400/10   border-gray-400/40",
  approver:   "text-purple-400 bg-purple-400/10 border-purple-400/40",
};

// ─── Tipos ────────────────────────────────────────────────────────────────────

interface Project { id: number; name: string; group_name: string | null }

interface UserPerm {
  role: string;
  allowed_pages: string | null;
  allowed_project_ids: string | null;
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

type Draft = {
  role: string;
  is_budget_approver: boolean;
  allowed_pages: string[] | null;       // null = all modules
  allowed_project_ids: number[] | null; // null = all projects
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function parseJSON<T>(raw: string | null): T | null {
  if (raw === null) return null;
  try { return JSON.parse(raw) as T; } catch { return null; }
}

// ─── Componente ───────────────────────────────────────────────────────────────

export default function AdminPage() {
  const lang = useLanguage();

  const [users,    setUsers]    = useState<User[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);

  const [drafts, setDrafts] = useState<Record<number, Draft>>({});
  const [saving, setSaving] = useState<number | null>(null);
  const [saved,  setSaved]  = useState<number | null>(null);

  // Expanded edit section (username + projects)
  const [editOpen, setEditOpen]   = useState<number | null>(null);
  const [editUser, setEditUser]   = useState<Record<number, { username: string }>>({});
  const [savingEd, setSavingEd]   = useState<number | null>(null);
  const [savedEd,  setSavedEd]    = useState<number | null>(null);
  const [editErr,  setEditErr]    = useState<string | null>(null);

  // ── Load ──────────────────────────────────────────────────────────────────

  async function load() {
    const [usersRes, projRes] = await Promise.all([
      fetch("/api/admin/users"),
      fetch("/api/admin/projects"),
    ]);

    if (usersRes.status === 403) {
      setError(t("adm_no_access", lang));
      setLoading(false);
      return;
    }

    const usersData: User[] = await usersRes.json();
    const projData: Project[] = projRes.ok ? await projRes.json() : [];

    setUsers(usersData);
    setProjects(projData);

    const initDrafts: Record<number, Draft> = {};
    const initEdit:   Record<number, { username: string }> = {};
    for (const u of usersData) {
      initDrafts[u.id] = {
        role:                u.user_permissions?.role ?? "standard",
        is_budget_approver:  u.user_permissions?.is_budget_approver ?? false,
        allowed_pages:       parseJSON<string[]>(u.user_permissions?.allowed_pages ?? null),
        allowed_project_ids: parseJSON<number[]>(u.user_permissions?.allowed_project_ids ?? null),
      };
      initEdit[u.id] = { username: u.username ?? "" };
    }
    setDrafts(initDrafts);
    setEditUser(initEdit);
    setLoading(false);
  }

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Draft helpers ─────────────────────────────────────────────────────────

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

  function toggleProject(uid: number, pid: number) {
    const cur = drafts[uid]?.allowed_project_ids;
    if (cur === null) {
      patch(uid, { allowed_project_ids: projects.map(p => p.id).filter(i => i !== pid) });
    } else {
      const next = cur.includes(pid) ? cur.filter(i => i !== pid) : [...cur, pid];
      patch(uid, { allowed_project_ids: next.length === projects.length ? null : next });
    }
  }

  function isPageAllowed(uid: number, key: string) {
    const p = drafts[uid]?.allowed_pages;
    return p === null || p.includes(key);
  }

  function isProjectAllowed(uid: number, pid: number) {
    const p = drafts[uid]?.allowed_project_ids;
    return p === null || p.includes(pid);
  }

  // ── Save permissions ──────────────────────────────────────────────────────

  async function savePermissions(uid: number) {
    const d = drafts[uid];
    if (!d) return;
    setSaving(uid);
    await fetch(`/api/admin/users/${uid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        role:                d.role,
        is_budget_approver:  d.is_budget_approver,
        allowed_pages:       d.allowed_pages,
        allowed_project_ids: d.allowed_project_ids,
      }),
    });
    setSaving(null);
    setSaved(uid);
    setTimeout(() => setSaved(null), 2000);
    load();
  }

  // ── Save edit (username + projects via edit section) ──────────────────────

  async function saveEdit(uid: number) {
    setEditErr(null);
    setSavingEd(uid);
    const res = await fetch(`/api/admin/users/${uid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username:            editUser[uid]?.username,
        allowed_project_ids: drafts[uid]?.allowed_project_ids,
      }),
    });
    setSavingEd(null);
    if (!res.ok) {
      const body = await res.json();
      setEditErr(body.error ?? "Error");
    } else {
      setSavedEd(uid);
      setTimeout(() => setSavedEd(null), 2000);
      load();
    }
  }

  // ─────────────────────────────────────────────────────────────────────────

  if (loading) return <p className="text-gray-400">{t("lbl_loading", lang)}</p>;
  if (error)   return <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-6 text-red-400">{error}</div>;

  // Group projects by group_name for display
  const projectGroups: Record<string, Project[]> = {};
  for (const p of projects) {
    const g = p.group_name ?? "Sin grupo";
    projectGroups[g] = [...(projectGroups[g] ?? []), p];
  }

  return (
    <div>
      <div className="mb-5">
        <h1 className="text-2xl font-bold text-white">{t("adm_title", lang)}</h1>
        <p className="text-gray-400 text-sm mt-0.5">{users.length} {t("adm_count", lang)}</p>
      </div>

      <div className="space-y-2">
        {users.map((u, idx) => {
          const d      = drafts[u.id]  ?? { role: "standard", is_budget_approver: false, allowed_pages: null, allowed_project_ids: null };
          const eu     = editUser[u.id] ?? { username: u.username ?? "" };
          const isEdit = editOpen === u.id;
          const isEven = idx % 2 === 0;

          return (
            <div key={u.id} className={`rounded-xl border border-gray-800 overflow-hidden ${isEven ? "bg-gray-900" : "bg-gray-900/70"}`}>

              {/* ── Main row ── */}
              <div className="overflow-x-auto">
                <table className="w-full border-collapse" style={{ minWidth: "900px" }}>
                  {idx === 0 && (
                    <thead>
                      <tr className="border-b border-gray-800">
                        <th className="text-left px-3 py-2 text-xs text-gray-500 uppercase tracking-wider w-44">
                          {lang === "es" ? "Correo" : "Email"}
                        </th>
                        <th className="text-left px-3 py-2 text-xs text-gray-500 uppercase tracking-wider w-32">
                          {lang === "es" ? "Usuario" : "Username"}
                        </th>
                        <th className="text-left px-3 py-2 text-xs text-gray-500 uppercase tracking-wider w-28">
                          {lang === "es" ? "Rol" : "Role"}
                        </th>
                        {MODULES.map(m => (
                          <th key={m.key} className="px-1 py-2 w-10">
                            <div className="flex justify-center">
                              <span className="text-gray-500" style={{ writingMode: "vertical-rl", transform: "rotate(180deg)", fontSize: "10px", whiteSpace: "nowrap" }}>
                                {lang === "es" ? m.es : m.en}
                              </span>
                            </div>
                          </th>
                        ))}
                        <th className="px-1 py-2 w-10">
                          <div className="flex justify-center">
                            <span className="text-gray-500" style={{ writingMode: "vertical-rl", transform: "rotate(180deg)", fontSize: "10px", whiteSpace: "nowrap" }}>
                              {lang === "es" ? "Aprobador" : "Approver"}
                            </span>
                          </div>
                        </th>
                        <th className="px-3 py-2 w-20" />
                        <th className="px-3 py-2 w-20" />
                      </tr>
                    </thead>
                  )}
                  <tbody>
                    <tr className="hover:bg-white/5 transition-colors">
                      {/* Email */}
                      <td className="px-3 py-2.5">
                        <p className="text-gray-200 text-xs truncate max-w-[170px]" title={u.email}>{u.email}</p>
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
                        <td key={m.key} className="px-1 py-2.5 text-center">
                          <input type="checkbox" checked={isPageAllowed(u.id, m.key)}
                            onChange={() => togglePage(u.id, m.key)}
                            className="w-4 h-4 accent-orange-500 cursor-pointer" />
                        </td>
                      ))}

                      {/* Approver */}
                      <td className="px-1 py-2.5 text-center">
                        <input type="checkbox" checked={d.is_budget_approver}
                          onChange={e => patch(u.id, { is_budget_approver: e.target.checked })}
                          className="w-4 h-4 accent-orange-500 cursor-pointer" />
                      </td>

                      {/* Save permissions */}
                      <td className="px-3 py-2.5 text-center">
                        {saved === u.id ? (
                          <span className="text-green-400 text-xs font-bold">✓</span>
                        ) : (
                          <button onClick={() => savePermissions(u.id)} disabled={saving === u.id}
                            className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap">
                            {saving === u.id ? "…" : (lang === "es" ? "Guardar" : "Save")}
                          </button>
                        )}
                      </td>

                      {/* Edit button */}
                      <td className="px-3 py-2.5 text-center">
                        <button
                          onClick={() => { setEditOpen(isEdit ? null : u.id); setEditErr(null); }}
                          className={`text-xs px-3 py-1.5 rounded-lg border transition-colors whitespace-nowrap ${
                            isEdit
                              ? "border-orange-500 text-orange-400 bg-orange-500/10"
                              : "border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200"
                          }`}
                        >
                          {lang === "es" ? "Editar" : "Edit"} {isEdit ? "▲" : "▼"}
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* ── Edit panel: username + projects ── */}
              {isEdit && (
                <div className="border-t border-gray-800 bg-gray-800/20 px-4 py-4">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                    {/* Username edit */}
                    <div>
                      <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-3">
                        {lang === "es" ? "Editar nombre de usuario" : "Edit Username"}
                      </p>
                      <div className="flex gap-2 items-center">
                        <input
                          type="text"
                          value={eu.username}
                          onChange={e => setEditUser(prev => ({ ...prev, [u.id]: { username: e.target.value } }))}
                          placeholder={lang === "es" ? "Ej: FelipeSerna" : "e.g. FelipeSerna"}
                          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500"
                        />
                      </div>
                      {editErr && <p className="text-red-400 text-xs mt-1">{editErr}</p>}
                    </div>

                    {/* Project visibility */}
                    <div>
                      <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-3">
                        {lang === "es" ? "Proyectos visibles" : "Visible Projects"}
                        <span className="ml-2 text-gray-600 normal-case text-xs">
                          ({lang === "es" ? "desmarca para ocultar" : "uncheck to hide"})
                        </span>
                      </p>
                      {projects.length === 0 ? (
                        <p className="text-gray-600 text-xs">{lang === "es" ? "Sin proyectos" : "No projects"}</p>
                      ) : (
                        <div className="space-y-3">
                          {Object.entries(projectGroups).map(([group, groupProjs]) => (
                            <div key={group}>
                              <p className="text-xs text-gray-500 font-medium mb-1.5">{group}</p>
                              <div className="flex flex-wrap gap-2">
                                {groupProjs.map(p => {
                                  const allowed = isProjectAllowed(u.id, p.id);
                                  return (
                                    <label key={p.id}
                                      className={`flex items-center gap-1.5 cursor-pointer rounded-lg border px-3 py-1.5 text-xs transition-colors select-none ${
                                        allowed
                                          ? "border-orange-500/40 bg-orange-500/5 text-gray-200"
                                          : "border-gray-700 bg-gray-800/40 text-gray-500"
                                      }`}>
                                      <input type="checkbox" checked={allowed}
                                        onChange={() => toggleProject(u.id, p.id)}
                                        className="w-3.5 h-3.5 accent-orange-500 cursor-pointer flex-shrink-0" />
                                      <span className="font-medium">{p.name}</span>
                                    </label>
                                  );
                                })}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Save edit row */}
                  <div className="flex items-center gap-3 mt-4 pt-3 border-t border-gray-800">
                    <button onClick={() => saveEdit(u.id)} disabled={savingEd === u.id}
                      className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-sm font-semibold px-4 py-1.5 rounded-lg transition-colors">
                      {savingEd === u.id
                        ? (lang === "es" ? "Guardando…" : "Saving…")
                        : (lang === "es" ? "Guardar cambios" : "Save changes")}
                    </button>
                    {savedEd === u.id && (
                      <span className="text-green-400 text-sm">✓ {lang === "es" ? "Guardado" : "Saved"}</span>
                    )}
                    <button onClick={() => setEditOpen(null)}
                      className="ml-auto text-gray-500 hover:text-gray-300 text-sm">
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
