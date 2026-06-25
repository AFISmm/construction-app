"use client";
import { useEffect, useState, Fragment } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { t } from "@/lib/lang";

// ─── Config ───────────────────────────────────────────────────────────────────

const MODULES = [
  { key: "dashboard",    en: "Dashboard",    es: "Dashboard" },
  { key: "budget",       en: "Budget",       es: "Presupuesto" },
  { key: "expenses",     en: "Payments",     es: "Pagos" },
  { key: "vendors",      en: "Vendors",      es: "Proveedores" },
  { key: "trazabilidad", en: "Versioning",   es: "Trazabilidad" },
  { key: "import",       en: "Import",       es: "Importar" },
  { key: "account",      en: "Account",      es: "Cuenta" },
  { key: "profile",      en: "Profile",      es: "Perfil" },
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

// ─── Types ────────────────────────────────────────────────────────────────────

type ModuleAccess = "view" | "edit" | null;
// null overall = full access (superadmin)
// object per module: "edit" | "view" | null(no access)
type PagePerms = Record<string, ModuleAccess> | null;

interface Project { id: number; name: string; group_name: string | null }

interface UserPerm {
  role: string;
  allowed_pages: string | null;
  allowed_project_ids: string | null;
  is_budget_approver: boolean | null;
}
interface User {
  id: number; email: string; username: string | null;
  first_name: string | null; last_name: string | null;
  created_at: string; user_permissions: UserPerm | null;
}

type Draft = {
  role: string;
  is_budget_approver: boolean;
  page_perms: PagePerms;
  allowed_project_ids: number[] | null;
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function parseJSON<T>(raw: string | null): T | null {
  if (!raw) return null;
  try { return JSON.parse(raw) as T; } catch { return null; }
}

function parsePagePerms(raw: string | null): PagePerms {
  if (!raw) return null; // null = full access
  const parsed = parseJSON<unknown>(raw);
  if (!parsed) return null;
  // Legacy: was stored as string[] (array of accessible pages)
  if (Array.isArray(parsed)) {
    const obj: Record<string, ModuleAccess> = {};
    for (const k of parsed) obj[k as string] = "edit";
    return obj;
  }
  return parsed as PagePerms;
}

function canView(perms: PagePerms, key: string): boolean {
  if (perms === null) return true;
  return perms[key] === "view" || perms[key] === "edit";
}
function canEdit(perms: PagePerms, key: string): boolean {
  if (perms === null) return true;
  return perms[key] === "edit";
}

function setViewAccess(perms: PagePerms, key: string, value: boolean): PagePerms {
  // Expand null → all-edit object first
  const cur: Record<string, ModuleAccess> = perms === null
    ? Object.fromEntries(MODULES.map(m => [m.key, "edit" as ModuleAccess]))
    : { ...perms };

  if (!value) {
    cur[key] = null; // revoke all access
  } else {
    if (!cur[key]) cur[key] = "view"; // grant view if had none
  }
  // Collapse back to null if all are "edit"
  const allEdit = MODULES.every(m => cur[m.key] === "edit");
  return allEdit ? null : cur;
}

function setEditAccess(perms: PagePerms, key: string, value: boolean): PagePerms {
  const cur: Record<string, ModuleAccess> = perms === null
    ? Object.fromEntries(MODULES.map(m => [m.key, "edit" as ModuleAccess]))
    : { ...perms };

  if (value) {
    cur[key] = "edit";
  } else {
    cur[key] = cur[key] === "edit" ? "view" : cur[key]; // downgrade from edit to view
  }
  const allEdit = MODULES.every(m => cur[m.key] === "edit");
  return allEdit ? null : cur;
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function AdminPage() {
  const lang = useLanguage();

  const [users,    setUsers]    = useState<User[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState<string | null>(null);

  const [drafts,  setDrafts]  = useState<Record<number, Draft>>({});
  const [saving,  setSaving]  = useState<number | null>(null);
  const [saved,   setSaved]   = useState<number | null>(null);

  const [editOpen,  setEditOpen]  = useState<number | null>(null);
  const [editNames, setEditNames] = useState<Record<number, string>>({});
  const [savingEd,  setSavingEd]  = useState<number | null>(null);
  const [savedEd,   setSavedEd]   = useState<number | null>(null);
  const [editErr,   setEditErr]   = useState<string | null>(null);

  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const [deleting,      setDeleting]      = useState<number | null>(null);
  const [deleteErr,     setDeleteErr]     = useState<string | null>(null);

  // ── Load ──────────────────────────────────────────────────────────────────

  async function load() {
    const [uRes, pRes] = await Promise.all([
      fetch("/api/admin/users"),
      fetch("/api/admin/projects"),
    ]);
    if (uRes.status === 403) { setError(t("adm_no_access", lang)); setLoading(false); return; }

    const userData: User[]    = await uRes.json();
    const projData: Project[] = pRes.ok ? await pRes.json() : [];

    setUsers(userData);
    setProjects(projData);

    const initDrafts: Record<number, Draft> = {};
    const initNames:  Record<number, string> = {};
    for (const u of userData) {
      initDrafts[u.id] = {
        role:                u.user_permissions?.role ?? "standard",
        is_budget_approver:  u.user_permissions?.is_budget_approver ?? false,
        page_perms:          parsePagePerms(u.user_permissions?.allowed_pages ?? null),
        allowed_project_ids: parseJSON<number[]>(u.user_permissions?.allowed_project_ids ?? null),
      };
      initNames[u.id] = u.username ?? "";
    }
    setDrafts(initDrafts);
    setEditNames(initNames);
    setLoading(false);
  }

  useEffect(() => { load(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // ── Patch helpers ─────────────────────────────────────────────────────────

  function patchDraft(uid: number, p: Partial<Draft>) {
    setDrafts(prev => ({ ...prev, [uid]: { ...prev[uid], ...p } }));
  }

  function toggleProject(uid: number, pid: number) {
    const cur = drafts[uid]?.allowed_project_ids;
    if (cur === null) {
      patchDraft(uid, { allowed_project_ids: projects.map(p => p.id).filter(i => i !== pid) });
    } else {
      const next = cur.includes(pid) ? cur.filter(i => i !== pid) : [...cur, pid];
      patchDraft(uid, { allowed_project_ids: next.length === projects.length ? null : next });
    }
  }

  function isProjectAllowed(uid: number, pid: number) {
    const p = drafts[uid]?.allowed_project_ids;
    return p === null || p.includes(pid);
  }

  // ── Save ──────────────────────────────────────────────────────────────────

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
        allowed_pages:       d.page_perms,
        allowed_project_ids: d.allowed_project_ids,
      }),
    });
    setSaving(null);
    setSaved(uid);
    setTimeout(() => setSaved(null), 2500);
    load();
  }

  async function saveEdit(uid: number) {
    setEditErr(null);
    setSavingEd(uid);
    const res = await fetch(`/api/admin/users/${uid}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: editNames[uid] }),
    });
    setSavingEd(null);
    if (!res.ok) {
      const b = await res.json();
      setEditErr(b.error ?? "Error");
    } else {
      setSavedEd(uid);
      setTimeout(() => setSavedEd(null), 2500);
      load();
    }
  }

  async function deleteUser(uid: number) {
    setDeleteErr(null);
    setDeleting(uid);
    const res = await fetch(`/api/admin/users/${uid}`, { method: "DELETE" });
    setDeleting(null);
    if (!res.ok) {
      const b = await res.json();
      setDeleteErr(b.error ?? "Error");
    } else {
      setConfirmDelete(null);
      setEditOpen(null);
      load();
    }
  }

  // ─────────────────────────────────────────────────────────────────────────

  if (loading) return <p className="text-gray-400">{t("lbl_loading", lang)}</p>;
  if (error)   return <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-6 text-red-400">{error}</div>;

  const lv = lang === "es" ? "Ver" : "View";
  const le = lang === "es" ? "Edit" : "Edit";

  const projectGroups: Record<string, Project[]> = {};
  for (const p of projects) {
    const g = p.group_name ?? "—";
    projectGroups[g] = [...(projectGroups[g] ?? []), p];
  }

  return (
    <div>
      <div className="mb-5">
        <h1 className="text-2xl font-bold text-white">{t("adm_title", lang)}</h1>
        <p className="text-gray-400 text-sm mt-0.5">{users.length} {t("adm_count", lang)}</p>
      </div>

      {/* ── Main table ── */}
      <div className="rounded-xl border border-gray-800 overflow-hidden mb-4">
        <div className="overflow-x-auto">
          <table className="border-collapse text-sm" style={{ minWidth: "1100px", width: "100%" }}>
            <colgroup>
              <col style={{ width: "170px" }} />
              <col style={{ width: "120px" }} />
              <col style={{ width: "120px" }} />
              {MODULES.map(m => (
                <col key={m.key + "v"} style={{ width: "36px" }} />
              ))}
              {MODULES.map(m => (
                <col key={m.key + "e"} style={{ width: "36px" }} />
              ))}
              <col style={{ width: "60px" }} />
              <col style={{ width: "85px" }} />
              <col style={{ width: "75px" }} />
            </colgroup>

            <thead className="bg-gray-900 border-b border-gray-800">
              {/* Row 1: section headers */}
              <tr>
                <th rowSpan={2} className="px-3 py-2 text-left text-xs text-gray-400 uppercase tracking-wider border-r border-gray-800">
                  {lang === "es" ? "Correo" : "Email"}
                </th>
                <th rowSpan={2} className="px-3 py-2 text-left text-xs text-gray-400 uppercase tracking-wider border-r border-gray-800">
                  {lang === "es" ? "Usuario" : "Username"}
                </th>
                <th rowSpan={2} className="px-3 py-2 text-left text-xs text-gray-400 uppercase tracking-wider border-r border-gray-800">
                  {lang === "es" ? "Rol" : "Role"}
                </th>
                {/* Module group headers — each spans 2 cols (Ver + Edit) */}
                {MODULES.map((m, i) => (
                  <th key={m.key} colSpan={2}
                    className={`py-2 text-center text-xs font-semibold ${i % 2 === 0 ? "text-gray-300 bg-gray-800/60" : "text-gray-300 bg-gray-800/30"} border-l border-gray-800`}>
                    <span style={{ fontSize: "10px" }}>{lang === "es" ? m.es : m.en}</span>
                  </th>
                ))}
                <th rowSpan={2} className="px-1 py-2 text-center border-l border-gray-800">
                  <span className="text-gray-400" style={{ writingMode: "vertical-rl", transform: "rotate(180deg)", fontSize: "10px", whiteSpace: "nowrap" }}>
                    {lang === "es" ? "Aprobador" : "Approver"}
                  </span>
                </th>
                <th rowSpan={2} className="px-2 py-2 border-l border-gray-800" />
                <th rowSpan={2} className="px-2 py-2 border-l border-gray-800" />
              </tr>
              {/* Row 2: Ver / Edit sub-headers */}
              <tr>
                {MODULES.map((m, i) => (
                  <Fragment key={m.key}>
                    <th className={`py-1 text-center border-l border-gray-800 ${i % 2 === 0 ? "bg-gray-800/60" : "bg-gray-800/30"}`}>
                      <span className="text-gray-500" style={{ fontSize: "9px" }}>{lv}</span>
                    </th>
                    <th className={`py-1 text-center ${i % 2 === 0 ? "bg-gray-800/60" : "bg-gray-800/30"}`}>
                      <span className="text-gray-500" style={{ fontSize: "9px" }}>{le}</span>
                    </th>
                  </Fragment>
                ))}
              </tr>
            </thead>

            <tbody>
              {users.map((u, idx) => {
                const d      = drafts[u.id] ?? { role: "standard", is_budget_approver: false, page_perms: null, allowed_project_ids: null };
                const isEdit = editOpen === u.id;
                const stripe = idx % 2 === 0 ? "bg-gray-900" : "bg-gray-900/60";

                return (
                  <Fragment key={u.id}>
                    <tr className={`${stripe} hover:bg-white/5 transition-colors border-t border-gray-800/60`}>
                      {/* Email */}
                      <td className="px-3 py-2.5 border-r border-gray-800">
                        <span className="text-gray-200 text-xs truncate block max-w-[160px]" title={u.email}>{u.email}</span>
                      </td>
                      {/* Username */}
                      <td className="px-3 py-2.5 border-r border-gray-800">
                        <span className="text-gray-300 font-mono text-xs">{u.username ?? "—"}</span>
                      </td>
                      {/* Role */}
                      <td className="px-2 py-2.5 border-r border-gray-800">
                        <select value={d.role}
                          onChange={e => patchDraft(u.id, { role: e.target.value })}
                          className={`text-xs font-semibold rounded-lg px-2 py-1 border cursor-pointer focus:outline-none focus:border-orange-500 bg-transparent w-full ${ROLE_STYLE[d.role] ?? ROLE_STYLE.standard}`}>
                          {ROLES.map(r => (
                            <option key={r} value={r} className="bg-gray-900 text-white">{r}</option>
                          ))}
                        </select>
                      </td>

                      {/* Module checkboxes: Ver + Edit per module */}
                      {MODULES.map((m, i) => {
                        const view = canView(d.page_perms, m.key);
                        const edit = canEdit(d.page_perms, m.key);
                        const bg   = i % 2 === 0 ? "bg-gray-800/20" : "";
                        return (
                          <Fragment key={m.key}>
                            <td className={`text-center py-2 border-l border-gray-800/60 ${bg}`}>
                              <input type="checkbox" checked={view}
                                onChange={e => patchDraft(u.id, {
                                  page_perms: setViewAccess(d.page_perms, m.key, e.target.checked)
                                })}
                                className="w-3.5 h-3.5 accent-orange-500 cursor-pointer" />
                            </td>
                            <td className={`text-center py-2 ${bg}`}>
                              <input type="checkbox" checked={edit} disabled={!view}
                                onChange={e => patchDraft(u.id, {
                                  page_perms: setEditAccess(d.page_perms, m.key, e.target.checked)
                                })}
                                className="w-3.5 h-3.5 accent-orange-500 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed" />
                            </td>
                          </Fragment>
                        );
                      })}

                      {/* Approver */}
                      <td className="text-center py-2.5 border-l border-gray-800">
                        <input type="checkbox" checked={d.is_budget_approver}
                          onChange={e => patchDraft(u.id, { is_budget_approver: e.target.checked })}
                          className="w-3.5 h-3.5 accent-orange-500 cursor-pointer" />
                      </td>

                      {/* Save */}
                      <td className="px-2 py-2.5 text-center border-l border-gray-800">
                        {saved === u.id ? (
                          <span className="text-green-400 text-xs font-bold">✓</span>
                        ) : (
                          <button onClick={() => savePermissions(u.id)} disabled={saving === u.id}
                            className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-xs font-semibold px-2.5 py-1.5 rounded-lg transition-colors whitespace-nowrap">
                            {saving === u.id ? "…" : (lang === "es" ? "Guardar" : "Save")}
                          </button>
                        )}
                      </td>

                      {/* Edit expand */}
                      <td className="px-2 py-2.5 text-center border-l border-gray-800">
                        <button
                          onClick={() => { setEditOpen(isEdit ? null : u.id); setEditErr(null); }}
                          className={`text-xs px-2.5 py-1.5 rounded-lg border transition-colors whitespace-nowrap ${
                            isEdit
                              ? "border-orange-500 text-orange-400 bg-orange-500/10"
                              : "border-gray-700 text-gray-400 hover:border-gray-500 hover:text-gray-200"
                          }`}>
                          {lang === "es" ? "Editar" : "Edit"} {isEdit ? "▲" : "▼"}
                        </button>
                      </td>
                    </tr>

                    {/* ── Expanded edit panel ── */}
                    {isEdit && (
                      <tr className="bg-gray-800/20 border-t border-orange-500/20">
                        <td colSpan={3 + MODULES.length * 2 + 3} className="px-4 py-4">
                          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                            {/* Username edit */}
                            <div>
                              <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-2">
                                {lang === "es" ? "Editar nombre de usuario" : "Edit Username"}
                              </p>
                              <div className="flex gap-2">
                                <input type="text" value={editNames[u.id] ?? ""}
                                  onChange={e => setEditNames(prev => ({ ...prev, [u.id]: e.target.value }))}
                                  placeholder="e.g. FelipeSerna"
                                  className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
                                <button onClick={() => saveEdit(u.id)} disabled={savingEd === u.id}
                                  className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
                                  {savingEd === u.id ? "…" : (lang === "es" ? "Guardar" : "Save")}
                                </button>
                              </div>
                              {editErr  && <p className="text-red-400 text-xs mt-1">{editErr}</p>}
                              {savedEd === u.id && <p className="text-green-400 text-xs mt-1">✓ {lang === "es" ? "Guardado" : "Saved"}</p>}
                            </div>

                            {/* Project visibility */}
                            <div>
                              <p className="text-xs text-gray-400 uppercase tracking-wider font-semibold mb-2">
                                {lang === "es" ? "Proyectos visibles" : "Visible Projects"}
                              </p>
                              {projects.length === 0 ? (
                                <p className="text-gray-600 text-xs">{lang === "es" ? "Sin proyectos" : "No projects found"}</p>
                              ) : (
                                <div className="space-y-2">
                                  {Object.entries(projectGroups).map(([group, gp]) => (
                                    <div key={group}>
                                      <p className="text-xs text-gray-500 font-medium mb-1">{group}</p>
                                      <div className="flex flex-wrap gap-2">
                                        {gp.map(p => {
                                          const ok = isProjectAllowed(u.id, p.id);
                                          return (
                                            <label key={p.id}
                                              className={`flex items-center gap-1.5 cursor-pointer rounded-lg border px-3 py-1.5 text-xs select-none transition-colors ${
                                                ok ? "border-orange-500/40 bg-orange-500/5 text-gray-200" : "border-gray-700 bg-gray-800/40 text-gray-500"
                                              }`}>
                                              <input type="checkbox" checked={ok}
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

                          <div className="mt-3 pt-3 border-t border-gray-800 flex items-center justify-between">
                            {/* Delete zone */}
                            <div className="flex items-center gap-2">
                              {confirmDelete === u.id ? (
                                <>
                                  <span className="text-xs text-red-400 font-medium">
                                    {lang === "es" ? "¿Confirmar eliminación?" : "Confirm delete?"}
                                  </span>
                                  <button onClick={() => deleteUser(u.id)} disabled={deleting === u.id}
                                    className="bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors">
                                    {deleting === u.id ? "…" : (lang === "es" ? "Sí, eliminar" : "Yes, delete")}
                                  </button>
                                  <button onClick={() => { setConfirmDelete(null); setDeleteErr(null); }}
                                    className="text-gray-500 hover:text-gray-300 text-xs px-3 py-1.5 border border-gray-700 rounded-lg">
                                    {lang === "es" ? "Cancelar" : "Cancel"}
                                  </button>
                                  {deleteErr && <span className="text-red-400 text-xs">{deleteErr}</span>}
                                </>
                              ) : (
                                <button onClick={() => { setConfirmDelete(u.id); setDeleteErr(null); }}
                                  className="text-red-500 hover:text-red-400 hover:bg-red-500/10 border border-red-500/30 hover:border-red-500/60 text-xs px-3 py-1.5 rounded-lg transition-colors">
                                  {lang === "es" ? "Eliminar usuario" : "Delete user"}
                                </button>
                              )}
                            </div>

                            <button onClick={() => { setEditOpen(null); setConfirmDelete(null); }}
                              className="text-gray-500 hover:text-gray-300 text-xs">
                              {lang === "es" ? "Cerrar" : "Close"} ▲
                            </button>
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legend */}
      <div className="flex gap-4 text-xs text-gray-600">
        <span>● <span className="text-gray-500">{lang === "es" ? "Ver" : "View"}</span> = {lang === "es" ? "puede ver el módulo" : "can view module"}</span>
        <span>● <span className="text-gray-500">{lang === "es" ? "Edit" : "Edit"}</span> = {lang === "es" ? "puede crear / modificar / eliminar" : "can create / modify / delete"}</span>
        <span>● <span className="text-gray-500">{lang === "es" ? "Aprobador" : "Approver"}</span> = {lang === "es" ? "puede aprobar presupuestos" : "can approve budgets"}</span>
      </div>
    </div>
  );
}
