"use client";
import { useState, useTransition } from "react";
import { fmtMoney } from "@/lib/format";
import { updateBudgetLine } from "@/app/actions/budget";
import type { BudgetLine } from "@/app/(app)/budget/page";

export default function BudgetTable({
  lines,
  projectId,
  catNames,
}: {
  lines: BudgetLine[];
  projectId: number;
  catNames: Record<string, string>;
}) {
  const [amounts, setAmounts] = useState<Record<number, number>>(() =>
    Object.fromEntries(lines.map(l => [l.id, l.budgeted_amount]))
  );
  const [saving, setSaving] = useState<number | null>(null);
  const [, startTransition] = useTransition();

  const groups: Record<string, BudgetLine[]> = {};
  for (const l of lines) {
    const top = l.category_code.split(".")[0];
    groups[top] = [...(groups[top] ?? []), l];
  }

  async function save(lineId: number) {
    setSaving(lineId);
    await updateBudgetLine(lineId, projectId, amounts[lineId]);
    setSaving(null);
  }

  const totalBudget = Object.entries(amounts).reduce((s, [id, v]) => {
    const line = lines.find(l => l.id === Number(id));
    return line ? s + v : s;
  }, 0);

  const totalAdj = lines.reduce((s, l) => {
    const adj = l.change_order_amount > 0 ? l.change_order_amount : (amounts[l.id] ?? l.budgeted_amount);
    return s + adj;
  }, 0);

  const totalPaid   = lines.reduce((s, l) => s + l.paid, 0);
  const totalBal    = totalAdj - totalPaid;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_auto] gap-4 px-4 py-3 border-b border-gray-800 text-xs text-gray-400 uppercase tracking-wider">
        <span>Category</span>
        <span className="text-right">Estimated Budget</span>
        <span className="text-right">Adjusted Budget</span>
        <span className="text-right">Payments to Date</span>
        <span className="text-right">Balance</span>
        <span className="w-16" />
      </div>

      {Object.entries(groups).sort().map(([top, groupLines]) => (
        <div key={top}>
          <div className="px-4 py-2 bg-gray-800/50 text-sm font-semibold text-gray-300">
            {top}{catNames[top] ? ` — ${catNames[top]}` : ""}
          </div>
          {groupLines.map(l => {
            const amt       = amounts[l.id] ?? l.budgeted_amount;
            const adjusted  = l.change_order_amount > 0 ? l.change_order_amount : amt;
            const balance   = adjusted - l.paid;
            const changed   = amt !== l.budgeted_amount;
            return (
              <div
                key={l.id}
                className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_auto] gap-4 px-4 py-2 border-t border-gray-800/50 items-center hover:bg-gray-800/20"
              >
                <span className={`text-sm pl-3 truncate ${amt > 0 ? "text-gray-200" : "text-gray-500"}`} title={l.description}>
                  {l.description}
                </span>
                {/* Estimated Budget — editable */}
                <div className="flex justify-end">
                  <input
                    type="number"
                    min={0}
                    step={1000}
                    value={amt}
                    onChange={e => setAmounts(prev => ({ ...prev, [l.id]: parseFloat(e.target.value) || 0 }))}
                    className="w-32 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-right text-sm text-white focus:outline-none focus:border-orange-500"
                  />
                </div>
                {/* Adjusted Budget — read only */}
                <span className="text-right text-sm text-gray-300">{fmtMoney(adjusted)}</span>
                {/* Payments to Date — read only */}
                <span className="text-right text-sm text-gray-300">{fmtMoney(l.paid)}</span>
                {/* Balance */}
                <span className={`text-right text-sm font-medium ${balance < 0 ? "text-red-400" : "text-gray-300"}`}>
                  {fmtMoney(balance)}
                </span>
                {/* Save button */}
                <div className="flex justify-end w-16">
                  {changed && (
                    <button
                      onClick={() => startTransition(() => { save(l.id); })}
                      disabled={saving === l.id}
                      className="text-xs bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white px-3 py-1 rounded transition-colors"
                    >
                      {saving === l.id ? "…" : "Save"}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ))}

      {/* Totals */}
      <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr_auto] gap-4 px-4 py-3 border-t border-gray-700 font-bold text-sm bg-gray-800/30">
        <span className="text-white">Total</span>
        <span className="text-right text-white">{fmtMoney(totalBudget)}</span>
        <span className="text-right text-white">{fmtMoney(totalAdj)}</span>
        <span className="text-right text-white">{fmtMoney(totalPaid)}</span>
        <span className={`text-right ${totalBal < 0 ? "text-red-400" : "text-green-400"}`}>{fmtMoney(totalBal)}</span>
        <span className="w-16" />
      </div>
    </div>
  );
}
