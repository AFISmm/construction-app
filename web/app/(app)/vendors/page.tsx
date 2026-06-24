"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

interface Vendor {
  id: number;
  company_name: string;
  contact_name: string | null;
  phone: string | null;
  email: string | null;
  trade: string | null;
  nit: string | null;
  status: string;
  notes: string | null;
}

const STATUS_COLORS: Record<string, string> = {
  pending:  "text-yellow-400 bg-yellow-400/10",
  active:   "text-green-400 bg-green-400/10",
  inactive: "text-gray-400 bg-gray-400/10",
};

export default function VendorsPage() {
  const searchParams = useSearchParams();
  const pid = searchParams.get("pid");

  const [vendors,  setVendors]  = useState<Vendor[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving,   setSaving]   = useState(false);
  const [form, setForm] = useState({
    company_name: "", contact_name: "", phone: "", email: "", trade: "", nit: "", notes: "",
  });

  async function load() {
    if (!pid) return;
    const res = await fetch(`/api/vendors?pid=${pid}`);
    setVendors(await res.json());
    setLoading(false);
  }

  useEffect(() => { load(); }, [pid]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    await fetch("/api/vendors", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_id: parseInt(pid!), ...form }),
    });
    setSaving(false);
    setShowForm(false);
    setForm({ company_name: "", contact_name: "", phone: "", email: "", trade: "", nit: "", notes: "" });
    load();
  }

  async function handleDelete(id: number) {
    if (!confirm("¿Eliminar este proveedor?")) return;
    await fetch(`/api/vendors/${id}`, { method: "DELETE" });
    load();
  }

  async function handleStatus(id: number, status: string) {
    await fetch(`/api/vendors/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    load();
  }

  if (!pid)    return <p className="text-gray-400">Selecciona un proyecto.</p>;
  if (loading) return <p className="text-gray-400">Cargando…</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Vendors</h1>
          <p className="text-gray-400 text-sm mt-0.5">{vendors.length} vendors registered</p>
        </div>
        <button onClick={() => setShowForm(v => !v)}
          className="bg-orange-600 hover:bg-orange-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
          + Add Vendor
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAdd} className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6 grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="text-xs text-gray-400 mb-1 block">Company Name *</label>
            <input required type="text" value={form.company_name} placeholder="Company name"
              onChange={e => setForm(f => ({ ...f, company_name: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Contact Name</label>
            <input type="text" value={form.contact_name} placeholder="Contact person"
              onChange={e => setForm(f => ({ ...f, contact_name: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Phone</label>
            <input type="text" value={form.phone} placeholder="+1 555 0000"
              onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Email</label>
            <input type="email" value={form.email} placeholder="vendor@email.com"
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">Trade / Specialty</label>
            <input type="text" value={form.trade} placeholder="Plumbing, Electrical…"
              onChange={e => setForm(f => ({ ...f, trade: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">NIT / Tax ID</label>
            <input type="text" value={form.nit}
              onChange={e => setForm(f => ({ ...f, nit: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div className="col-span-2">
            <label className="text-xs text-gray-400 mb-1 block">Notes</label>
            <textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
              rows={2} placeholder="Additional notes"
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div className="col-span-2 flex gap-3 justify-end">
            <button type="button" onClick={() => setShowForm(false)} className="text-sm text-gray-400 hover:text-white px-4 py-2 rounded-lg">Cancel</button>
            <button type="submit" disabled={saving}
              className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg">
              {saving ? "Saving…" : "Save Vendor"}
            </button>
          </div>
        </form>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_auto] gap-4 px-4 py-3 border-b border-gray-800 text-xs text-gray-400 uppercase tracking-wider">
          <span>Company</span><span>Contact</span><span>Trade</span><span>Phone</span><span>Status</span><span className="w-8" />
        </div>

        {vendors.length === 0 ? (
          <p className="px-4 py-6 text-gray-500 text-sm">No vendors registered yet.</p>
        ) : (
          vendors.map(v => (
            <div key={v.id} className="grid grid-cols-[2fr_1.5fr_1fr_1fr_1fr_auto] gap-4 px-4 py-2.5 border-t border-gray-800/50 text-sm items-center hover:bg-gray-800/20">
              <div>
                <p className="text-gray-200 font-medium truncate">{v.company_name}</p>
                {v.email && <p className="text-gray-500 text-xs truncate">{v.email}</p>}
              </div>
              <span className="text-gray-400 truncate">{v.contact_name ?? "—"}</span>
              <span className="text-gray-400 truncate">{v.trade ?? "—"}</span>
              <span className="text-gray-400">{v.phone ?? "—"}</span>
              <select value={v.status} onChange={e => handleStatus(v.id, e.target.value)}
                className={`text-xs font-medium rounded px-2 py-0.5 border-0 bg-transparent cursor-pointer ${STATUS_COLORS[v.status] ?? ""}`}>
                <option value="pending">Pending</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
              <button onClick={() => handleDelete(v.id)} className="text-gray-600 hover:text-red-400 transition-colors w-8 text-center">✕</button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
