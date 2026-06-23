"use client";
import { useState, useTransition } from "react";
import { fmtMoney } from "@/lib/format";
import { updateBudgetLine } from "@/app/actions/budget";

interface Line {
  id: number;
  category_code: string;
  description: string;
  budgeted_amount: number;
  change_order_amount: number;
}

export default function BudgetTable({ lines, projectId }: { lines: Line[]; projectId: number }) {
  const [amounts, setAmounts] = useState<Record<number, number>>(() =>
    Object.fromEntries(lines.map(l => [l.id, l.budgeted_amount]))
  );
  const [saving, setSaving] = useState<number | null>(null);
  const [, startTransition] = useTransition();

  const groups: Record<string, Line[]> = {};
  for (const l of lines) {
    const top = l.category_code.split(".")[0];
    groups[top] = [...(groups[top] ?? []), l];
  }

  async function save(lineId: number) {
    setSaving(lineId);
    await updateBudgetLine(lineId, projectId, amounts[lineId]);
    setSaving(null);
  }

  const totalBudget = Object.values(amounts).reduce((s, v) => s + v, 0);
  const withValues = Object.values(amounts).filter(v => v > 0).length;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="grid grid-cols-[2fr_1fr_1fr] gap-4 px-4 py-3 border-b border-gray-800 text-xs text-gray-400 uppercase tracking-wider">
        <span>Category</span>
        <span className="text-right">Estimated Budget</span>
        <span className="text-right">Actions</span>
      </div>

      {Object.entries(groups).sort().map(([top, groupLines]) => (
        <div key={top}>
          <div className="px-4 py-2 bg-gray-800/50 text-sm font-semibold text-gray-300">
            {top}
          </div>
          {groupLines.map(l => (
            <div
              key={l.id}
              className="grid grid-cols-[2fr_1fr_1fr] gap-4 px-4 py-2 border-t border-gray-800/50 items-center hover:bg-gray-800/20"
            >
              <span
                className={`text-sm pl-3 truncate ${amounts[l.id] > 0 ? "text-gray-200" : "text-gray-500"}`}
                title={l.description}
              >
                {l.description}
              </span>
              <div className="flex justify-end">
                <input
                  type="number"
                  min={0}
                  step={1000}
                  value={amounts[l.id]}
                  onChange={e => setAmounts(prev => ({ ...prev, [l.id]: parseFloat(e.target.value) || 0 }))}
                  className="w-36 bg-gray-800 border border-gray-700 rounded px-2 py-1 text-right text-sm text-white focus:outline-none focus:border-orange-500"
                />
              </div>
              <div className="flex justify-end">
                {amounts[l.id] !== l.budgeted_amount && (
                  <button
                    onClick={() => startTransition(() => { save(l.id); })}
                    disabled={saving === l.id}
                    className="text-xs bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white px-3 py-1 rounded transition-colors"
                  >
                    {saving === l.id ? "Saving…" : "Save"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ))}

      {/* Totals */}
      <div className="grid grid-cols-[2fr_1fr_1fr] gap-4 px-4 py-3 border-t border-gray-700 font-bold text-sm bg-gray-800/30">
        <span className="text-white">
          Total ({withValues} lines with values)
        </span>
        <span className="text-right text-white">{fmtMoney(totalBudget)}</span>
        <span />
      </div>
    </div>
  );
}
