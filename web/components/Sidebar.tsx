"use client";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";
import { t, getLang, setLang, Lang } from "@/lib/lang";

interface Project { id: number; name: string; group_name: string | null }

export default function Sidebar({ userDisplay }: { userDisplay: string }) {
  const pathname    = usePathname();
  const router      = useRouter();
  const searchParams = useSearchParams();

  const [lang,          setLangState]    = useState<Lang>("en");
  const [projects,      setProjects]     = useState<Project[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>("");
  const [projectId,     setProjectId]    = useState<number | null>(null);

  useEffect(() => {
    setLangState(getLang());
    fetch("/api/projects").then(r => r.json()).then((data: Project[]) => {
      setProjects(data);
      const pidFromUrl = searchParams.get("pid");
      const stored     = localStorage.getItem("projectId");
      const id = pidFromUrl ? parseInt(pidFromUrl) : stored ? parseInt(stored) : (data[0]?.id ?? null);
      if (id && data.length > 0) {
        const match = data.find(p => p.id === id) ?? data[0];
        setProjectId(match.id);
        setSelectedGroup(groupOf(match));
        localStorage.setItem("projectId", String(match.id));
        if (!pidFromUrl) router.replace(`${pathname}?pid=${match.id}`);
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Use project name as group label when group_name is null
  function groupOf(p: Project): string {
    return p.group_name ?? p.name;
  }

  function groupList(list: Project[]): string[] {
    return [...new Set(list.map(groupOf))].sort();
  }

  function projectsInGroup(group: string): Project[] {
    return projects.filter(p => groupOf(p) === group);
  }

  function handleGroupChange(group: string) {
    setSelectedGroup(group);
    const first = projectsInGroup(group)[0];
    if (first) handleProject(first.id);
  }

  function handleProject(id: number) {
    setProjectId(id);
    localStorage.setItem("projectId", String(id));
    router.push(`${pathname}?pid=${id}`);
  }

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
  }

  function toggleLang() {
    const next: Lang = lang === "en" ? "es" : "en";
    setLang(next); // updates localStorage + cookie
    setLangState(next);
    // notify other client components on the same page
    window.dispatchEvent(new StorageEvent("storage", { key: "ck_lang", newValue: next }));
    // re-render server components (Dashboard, Budget)
    router.refresh();
  }

  function navHref(href: string) {
    return projectId ? `${href}?pid=${projectId}` : href;
  }

  const NAV = [
    { href: "/dashboard",    label: t("nav_dashboard",  lang) },
    { href: "/budget",       label: t("nav_budget",     lang) },
    { href: "/expenses",     label: t("nav_payments",   lang) },
    { href: "/vendors",      label: t("nav_vendors",    lang) },
    { href: "/trazabilidad", label: t("nav_versioning", lang) },
    { href: "/import",       label: t("nav_import",     lang) },
    { href: "/account",      label: t("nav_account",    lang) },
    { href: "/profile",      label: t("nav_profile",    lang) },
    { href: "/admin",        label: t("nav_admin",      lang) },
  ];

  const groups      = groupList(projects);
  const subprojects = selectedGroup ? projectsInGroup(selectedGroup) : [];

  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col flex-shrink-0">
      {/* Header */}
      <div className="p-4 border-b border-gray-800 flex items-center justify-between">
        <h2 className="text-sm font-bold text-orange-400 uppercase tracking-wider">
          {t("app_title", lang)}
        </h2>
        <button
          onClick={toggleLang}
          title={lang === "en" ? "Cambiar a Español" : "Switch to English"}
          className="text-xs text-gray-500 hover:text-orange-400 font-mono border border-gray-700 hover:border-orange-500 rounded px-1.5 py-0.5 transition-colors"
        >
          {lang === "en" ? "ES" : "EN"}
        </button>
      </div>

      {/* Project selector */}
      <div className="p-3 border-b border-gray-800 space-y-3">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">{t("lbl_projects", lang)}</p>

        <div>
          <label className="text-xs text-gray-500 mb-1 block">{t("lbl_client", lang)}</label>
          <select
            className="w-full bg-gray-800 border border-gray-700 text-white text-sm rounded px-2 py-1.5 focus:outline-none focus:border-orange-500"
            value={selectedGroup}
            onChange={e => handleGroupChange(e.target.value)}
          >
            {groups.length === 0 && <option value="">{t("lbl_no_projects", lang)}</option>}
            {groups.map(g => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>

        {subprojects.length > 0 && (
          <div>
            <label className="text-xs text-gray-500 mb-1 block">{t("lbl_subproject", lang)}</label>
            <select
              className="w-full bg-gray-800 border border-gray-700 text-white text-sm rounded px-2 py-1.5 focus:outline-none focus:border-orange-500"
              value={projectId ?? ""}
              onChange={e => handleProject(Number(e.target.value))}
            >
              {subprojects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
        {NAV.map(({ href, label }) => (
          <Link
            key={href}
            href={navHref(href)}
            className={`block px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              pathname === href
                ? "bg-orange-600 text-white"
                : "text-gray-400 hover:text-white hover:bg-gray-800"
            }`}
          >
            {label}
          </Link>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-gray-800">
        <p className="text-xs text-gray-400 font-medium truncate mb-2" title={userDisplay}>
          {userDisplay}
        </p>
        <button
          onClick={handleLogout}
          className="w-full text-left px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          {t("btn_sign_out", lang)}
        </button>
      </div>
    </aside>
  );
}
