"use client";
import { useState } from "react";

export default function AccountPage() {
  const [form, setForm] = useState({ currentPassword: "", newPassword: "", confirmPassword: "" });
  const [saving, setSaving]   = useState(false);
  const [msg,    setMsg]      = useState<{ ok: boolean; text: string } | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    if (form.newPassword !== form.confirmPassword) {
      setMsg({ ok: false, text: "Passwords do not match." });
      return;
    }
    if (form.newPassword.length < 8) {
      setMsg({ ok: false, text: "New password must be at least 8 characters." });
      return;
    }
    setSaving(true);
    const res = await fetch("/api/auth/change-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ currentPassword: form.currentPassword, newPassword: form.newPassword }),
    });
    setSaving(false);
    if (res.ok) {
      setMsg({ ok: true, text: "Password changed successfully." });
      setForm({ currentPassword: "", newPassword: "", confirmPassword: "" });
    } else {
      const body = await res.json();
      setMsg({ ok: false, text: body.error ?? "Something went wrong." });
    }
  }

  return (
    <div className="max-w-md">
      <h1 className="text-2xl font-bold text-white mb-6">Account</h1>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
        <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-4">Change Password</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Current Password</label>
            <input type="password" required value={form.currentPassword}
              onChange={e => setForm(f => ({ ...f, currentPassword: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">New Password</label>
            <input type="password" required value={form.newPassword}
              onChange={e => setForm(f => ({ ...f, newPassword: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Confirm New Password</label>
            <input type="password" required value={form.confirmPassword}
              onChange={e => setForm(f => ({ ...f, confirmPassword: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>

          {msg && (
            <p className={`text-sm ${msg.ok ? "text-green-400" : "text-red-400"}`}>{msg.text}</p>
          )}

          <button type="submit" disabled={saving}
            className="w-full bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-sm font-semibold py-2 rounded-lg transition-colors">
            {saving ? "Saving…" : "Update Password"}
          </button>
        </form>
      </div>
    </div>
  );
}
