"use client";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState, useEffect } from "react";

const NAV = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/budget", label: "Budget" },
  { href: "/expenses", label: "Payments" },
  { href: "/vendors", label: "Vendors" },
];

interface Project { id: number; name: string; group_name: string | null }

export default function Sidebar({ userEmail }: { userEmail: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<number | null>(null);

  useEffect(() => {
    fetch("/api/projects").then(r => r.json()).then((data: Project[]) => {
      setProjects(data);
      const pidFromUrl = searchParams.get("pid");
      const stored = localStorage.getItem("projectId");
      const id = pidFromUrl
        ? parseInt(pidFromUrl)
        : stored
        ? parseInt(stored)
        : (data[0]?.id ?? null);
      if (id) {
        setProjectId(id);
        localStorage.setItem("projectId", String(id));
        if (!pidFromUrl) {
          router.replace(`${pathname}?pid=${id}`);
        }
      }
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleProject(id: number) {
    setProjectId(id);
    localStorage.setItem("projectId", String(id));
    router.push(`${pathname}?pid=${id}`);
  }

  async function handleLogout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
  }

  const groups = projects.reduce<Record<string, Project[]>>((acc, p) => {
    const g = p.group_name ?? "Projects";
    acc[g] = [...(acc[g] ?? []), p];
    return acc;
  }, {});

  function navHref(href: string) {
    return projectId ? `${href}?pid=${projectId}` : href;
  }

  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col flex-shrink-0">
      <div className="p-4 border-b border-gray-800">
        <h2 className="text-sm font-bold text-orange-400 uppercase tracking-wider">
          Construction Budget
        </h2>
      </div>

      {/* Project selector */}
      <div className="p-3 border-b border-gray-800 space-y-2">
        {Object.entries(groups).map(([group, list]) => (
          <div key={group}>
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">{group}</p>
            <select
              className="w-full bg-gray-800 border border-gray-700 text-white text-sm rounded px-2 py-1"
              value={list.some(p => p.id === projectId) ? (projectId ?? "") : ""}
              onChange={e => handleProject(Number(e.target.value))}
            >
              {list.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
        ))}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
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
        <p className="text-xs text-gray-500 truncate mb-2">{userEmail}</p>
        <button
          onClick={handleLogout}
          className="w-full text-left px-3 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
