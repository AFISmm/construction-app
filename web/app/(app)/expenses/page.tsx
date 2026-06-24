"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { fmtMoney } from "@/lib/format";
import { useLanguage } from "@/hooks/useLanguage";
import { t } from "@/lib/lang";

interface BudgetLine { id: number; category_code: string; description: string }
interface Expense {
  id: number;
  budget_line_id: number;
  vendor: string | null;
  description: string | null;
  amount: string;
  expense_date: string;
  budget_lines: { category_code: string; description: string | null };
}

export default function ExpensesPage() {
  const searchParams = useSearchParams();
  const pid = searchParams.get("pid");
  const lang = useLanguage();

  const [lines,    setLines]    = useState<BudgetLine[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [saving,   setSaving]   = useState(false);
  const [form, setForm] = useState({
    budget_line_id: "",
    vendor: "",
    description: "",
    amount: "",
    expense_date: new Date().toISOString().split("T")[0],
  });

  async function load() {
    if (!pid) return;
    const [linesRes, expRes] = await Promise.all([
      fetch(`/api/budget-lines?pid=${pid}`),
      fetch(`/api/expenses?pid=${pid}`),
    ]);
    setLines(await linesRes.json());
    setExpenses(await expRes.json());
    setLoading(false);
  }

  useEffect(() => { load(); }, [pid]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    await fetch("/api/expenses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_id: parseInt(pid!),
        budget_line_id: parseInt(form.budget_line_id),
        vendor: form.vendor || null,
        description: form.description || null,
        amount: parseFloat(form.amount),
        expense_date: form.expense_date,
      }),
    });
    setSaving(false);
    setShowForm(false);
    setForm({ budget_line_id: "", vendor: "", description: "", amount: "", expense_date: new Date().toISOString().split("T")[0] });
    load();
  }

  async function handleDelete(id: number) {
    if (!confirm(t("pay_confirm_del", lang))) return;
    await fetch(`/api/expenses/${id}`, { method: "DELETE" });
    load();
  }

  const grandTotal = expenses.reduce((s, e) => s + parseFloat(e.amount), 0);

  if (!pid)    return <p className="text-gray-400">{t("lbl_select_project", lang)}</p>;
  if (loading) return <p className="text-gray-400">{t("lbl_loading", lang)}</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">{t("pay_title", lang)}</h1>
          <p className="text-gray-400 text-sm mt-0.5">
            {expenses.length} {t("pay_count", lang)} · {t("lbl_total", lang)}: <span className="text-white font-semibold">{fmtMoney(grandTotal)}</span>
          </p>
        </div>
        <button onClick={() => setShowForm(v => !v)}
          className="bg-orange-600 hover:bg-orange-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors">
          {t("pay_add", lang)}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleAdd} className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6 grid grid-cols-2 gap-4">
          <div className="col-span-2">
            <label className="text-xs text-gray-400 mb-1 block">{t("pay_form_line", lang)} *</label>
            <select required value={form.budget_line_id}
              onChange={e => setForm(f => ({ ...f, budget_line_id: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500">
              <option value="">{t("pay_form_select", lang)}</option>
              {lines.map(l => (
                <option key={l.id} value={l.id}>{l.description || l.category_code}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">{t("pay_form_vendor", lang)}</label>
            <input type="text" value={form.vendor} onChange={e => setForm(f => ({ ...f, vendor: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">{t("pay_form_desc", lang)}</label>
            <input type="text" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">{t("pay_form_amount", lang)} *</label>
            <input type="number" required min={0.01} step={0.01} value={form.amount}
              onChange={e => setForm(f => ({ ...f, amount: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500"
              placeholder="0.00" />
          </div>
          <div>
            <label className="text-xs text-gray-400 mb-1 block">{t("pay_form_date", lang)} *</label>
            <input type="date" required value={form.expense_date}
              onChange={e => setForm(f => ({ ...f, expense_date: e.target.value }))}
              className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-orange-500" />
          </div>
          <div className="col-span-2 flex gap-3 justify-end">
            <button type="button" onClick={() => setShowForm(false)}
              className="text-sm text-gray-400 hover:text-white px-4 py-2 rounded-lg">{t("btn_cancel", lang)}</button>
            <button type="submit" disabled={saving}
              className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-lg">
              {saving ? t("pay_btn_saving", lang) : t("pay_btn_save", lang)}
            </button>
          </div>
        </form>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-[2fr_1.5fr_1.5fr_1fr_1fr_auto] gap-4 px-4 py-3 border-b border-gray-800 text-xs text-gray-400 uppercase tracking-wider">
          <span>{t("pay_col_desc",     lang)}</span>
          <span>{t("pay_col_vendor",   lang)}</span>
          <span>{t("pay_col_category", lang)}</span>
          <span className="text-right">{t("pay_col_amount", lang)}</span>
          <span className="text-right">{t("pay_col_date",   lang)}</span>
          <span className="w-8" />
        </div>

        {expenses.length === 0 ? (
          <p className="px-4 py-6 text-gray-500 text-sm">{t("pay_no_data", lang)}</p>
        ) : (
          expenses.map(exp => (
            <div key={exp.id}
              className="grid grid-cols-[2fr_1.5fr_1.5fr_1fr_1fr_auto] gap-4 px-4 py-2.5 border-t border-gray-800/50 text-sm items-center hover:bg-gray-800/20">
              <span className="text-gray-300 truncate">{exp.description ?? "—"}</span>
              <span className="text-gray-400 truncate">{exp.vendor ?? "—"}</span>
              <span className="text-gray-400 truncate">{exp.budget_lines.description ?? exp.budget_lines.category_code}</span>
              <span className="text-right text-gray-300">{fmtMoney(parseFloat(exp.amount))}</span>
              <span className="text-right text-gray-500 text-xs">{exp.expense_date.split("T")[0]}</span>
              <button onClick={() => handleDelete(exp.id)}
                className="text-gray-600 hover:text-red-400 transition-colors w-8 text-center">✕</button>
            </div>
          ))
        )}

        {expenses.length > 0 && (
          <div className="grid grid-cols-[2fr_1.5fr_1.5fr_1fr_1fr_auto] gap-4 px-4 py-3 border-t border-gray-700 font-bold text-sm bg-gray-800/30">
            <span className="text-white">{t("lbl_total", lang)}</span>
            <span /><span />
            <span className="text-right text-white">{fmtMoney(grandTotal)}</span>
            <span /><span />
          </div>
        )}
      </div>
    </div>
  );
}
