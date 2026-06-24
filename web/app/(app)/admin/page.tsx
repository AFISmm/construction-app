"use client";
import { useEffect, useState } from "react";

interface User {
  id: number;
  email: string;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  created_at: string;
  user_permissions: { role: string } | null;
}

const ROLES = ["standard", "admin", "viewer", "approver"];
const ROLE_STYLE: Record<string, string> = {
  admin:    "text-orange-400 bg-orange-400/10",
  standard: "text-blue-400 bg-blue-400/10",
  viewer:   "text-gray-400 bg-gray-400/10",
  approver: "text-purple-400 bg-purple-400/10",
};

export default function AdminPage() {
  const [users,   setUsers]   = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  async function load() {
    const res = await fetch("/api/admin/users");
    if (res.status === 403) { setError("Admin access required."); setLoading(false); return; }
    setUsers(await res.json());
    setLoading(false);
  }

  useEffect(() => { load(); }, []);

  async function handleRole(userId: number, role: string) {
    await fetch(`/api/admin/users/${userId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role }),
    });
    load();
  }

  if (loading) return <p className="text-gray-400">Cargando…</p>;
  if (error)   return <div className="bg-red-900/20 border border-red-700/40 rounded-xl p-6 text-red-400">{error}</div>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Admin Panel</h1>
          <p className="text-gray-400 text-sm mt-0.5">{users.length} registered users</p>
        </div>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-[2fr_1.5fr_1fr_1fr_auto] gap-4 px-4 py-3 border-b border-gray-800 text-xs text-gray-400 uppercase tracking-wider">
          <span>User</span><span>Username</span><span>Role</span><span>Joined</span><span className="w-32" />
        </div>
        {users.map(u => (
          <div key={u.id} className="grid grid-cols-[2fr_1.5fr_1fr_1fr_auto] gap-4 px-4 py-2.5 border-t border-gray-800/50 text-sm items-center hover:bg-gray-800/20">
            <div>
              <p className="text-gray-200">{u.first_name && u.last_name ? `${u.first_name} ${u.last_name}` : u.email}</p>
              <p className="text-gray-500 text-xs truncate">{u.email}</p>
            </div>
            <span className="text-gray-400 font-mono">{u.username ?? "—"}</span>
            <span className={`text-xs font-medium rounded px-2 py-0.5 w-fit ${ROLE_STYLE[u.user_permissions?.role ?? "standard"] ?? ""}`}>
              {u.user_permissions?.role ?? "standard"}
            </span>
            <span className="text-gray-600 text-xs">{u.created_at.split("T")[0]}</span>
            <select
              value={u.user_permissions?.role ?? "standard"}
              onChange={e => handleRole(u.id, e.target.value)}
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs text-gray-300 focus:outline-none focus:border-orange-500 w-32"
            >
              {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
          </div>
        ))}
      </div>
    </div>
  );
}
