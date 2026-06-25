"use client";
import { useEffect, useState } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { t } from "@/lib/lang";

interface Profile {
  company_name: string;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  phone: string | null;
  contact_email: string;
  category: string;
}

const CATEGORIES: { key: string; en: string; es: string }[] = [
  { key: "General Contractor", en: "General Contractor", es: "Contratista General" },
  { key: "Subcontractor",      en: "Subcontractor",      es: "Subcontratista" },
  { key: "Owner",              en: "Owner",              es: "Propietario" },
  { key: "Architect",          en: "Architect",          es: "Arquitecto" },
  { key: "Engineer",           en: "Engineer",           es: "Ingeniero" },
  { key: "Project Manager",    en: "Project Manager",    es: "Gerente de Proyecto" },
  { key: "Consultant",         en: "Consultant",         es: "Consultor" },
  { key: "Supplier",           en: "Supplier",           es: "Proveedor" },
  { key: "Other",              en: "Other",              es: "Otro" },
];

const EMPTY: Profile = {
  company_name: "", first_name: "", middle_name: "", last_name: "",
  phone: "", contact_email: "", category: "",
};

export default function ProfilePage() {
  const lang = useLanguage();
  const [form,   setForm]   = useState<Profile>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [msg,    setMsg]    = useState<{ ok: boolean; text: string } | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetch("/api/profile").then(r => r.json()).then(d => {
      if (d) setForm({
        company_name:  d.company_name ?? "",
        first_name:    d.first_name ?? "",
        middle_name:   d.middle_name ?? "",
        last_name:     d.last_name ?? "",
        phone:         d.phone ?? "",
        contact_email: d.contact_email ?? "",
        category:      d.category ?? "",
      });
      setLoaded(true);
    });
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    const res = await fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setSaving(false);
    setMsg(res.ok
      ? { ok: true,  text: t("prof_saved", lang) }
      : { ok: false, text: t("prof_fail",  lang) });
  }

  function f(k: keyof Profile, val: string) { setForm(p => ({ ...p, [k]: val })); }

  if (!loaded) return <p className="text-gray-400">{t("lbl_loading", lang)}</p>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-white mb-6">{t("prof_title", lang)}</h1>
      <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-gray-400 mb-1 block">{t("prof_first", lang)} *</label>
            <input required type="text" value={form.first_name} onChange={e => f("first_name", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">{t("prof_middle", lang)}</label>
            <input type="text" value={form.middle_name ?? ""} onChange={e => f("middle_name", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">{t("prof_last", lang)} *</label>
            <input required type="text" value={form.last_name} onChange={e => f("last_name", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">{t("prof_phone", lang)}</label>
            <input type="tel" value={form.phone ?? ""} onChange={e => f("phone", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div className="col-span-2">
            <label className="text-xs text-gray-400 mb-1 block">{t("prof_company", lang)} *</label>
            <input required type="text" value={form.company_name} onChange={e => f("company_name", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">{t("prof_email", lang)} *</label>
            <input required type="email" value={form.contact_email} onChange={e => f("contact_email", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">{t("prof_category", lang)} *</label>
            <select required value={form.category} onChange={e => f("category", e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500">
              <option value="">{t("prof_select", lang)}</option>
              {CATEGORIES.map(c => <option key={c.key} value={c.key}>{lang === "es" ? c.es : c.en}</option>)}
            </select>
          </div>
        </div>
        {msg && <p className={`text-sm ${msg.ok ? "text-green-400" : "text-red-400"}`}>{msg.text}</p>}
        <button type="submit" disabled={saving}
          className="w-full bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-sm font-semibold py-2 rounded-lg transition-colors">
          {saving ? t("prof_btn_saving", lang) : t("prof_btn", lang)}
        </button>
      </form>
    </div>
  );
}
