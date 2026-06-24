"use client";
import { useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { fmtMoney } from "@/lib/format";

interface ParsedRow { category_code: string; description: string; amount: number }

function parseCSV(text: string): ParsedRow[] {
  const lines = text.split(/\r?\n/).filter(l => l.trim());
  if (lines.length === 0) return [];
  const header = lines[0].split(",").map(h => h.trim().toLowerCase());
  const colCode = header.indexOf("category_code");
  const colDesc = header.indexOf("description");
  const colAmt  = header.indexOf("amount");
  if (colCode === -1 || colAmt === -1) return [];
  return lines.slice(1).map(line => {
    const cols = line.split(",");
    return {
      category_code: (cols[colCode] ?? "").trim(),
      description:   (cols[colDesc] ?? "").trim(),
      amount:        parseFloat((cols[colAmt] ?? "0").trim()) || 0,
    };
  }).filter(r => r.category_code);
}

export default function ImportPage() {
  const searchParams = useSearchParams();
  const pid = searchParams.get("pid");
  const inputRef = useRef<HTMLInputElement>(null);

  const [rows,      setRows]      = useState<ParsedRow[]>([]);
  const [fileName,  setFileName]  = useState("");
  const [importing, setImporting] = useState(false);
  const [result,    setResult]    = useState<{ imported: number; skipped: number } | null>(null);
  const [error,     setError]     = useState<string | null>(null);

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setResult(null);
    setError(null);
    const reader = new FileReader();
    reader.onload = ev => {
      const text = ev.target?.result as string;
      const parsed = parseCSV(text);
      setRows(parsed);
      if (parsed.length === 0) setError("No valid rows found. Verify CSV format.");
    };
    reader.readAsText(file);
  }

  async function handleImport() {
    if (!pid || rows.length === 0) return;
    setImporting(true);
    setError(null);
    const res = await fetch("/api/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_id: parseInt(pid), rows }),
    });
    setImporting(false);
    if (res.ok) {
      const data = await res.json();
      setResult(data);
      setRows([]);
      setFileName("");
    } else {
      const body = await res.json();
      setError(body.error ?? "Import failed.");
    }
  }

  if (!pid) return <p className="text-gray-400">Selecciona un proyecto.</p>;

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-2">Import from CSV</h1>
      <p className="text-gray-400 text-sm mb-6">
        Upload a CSV file to create budget lines. Required columns: <span className="font-mono text-orange-400">category_code</span>,{" "}
        <span className="font-mono text-orange-400">description</span>,{" "}
        <span className="font-mono text-orange-400">amount</span>.
      </p>

      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 mb-6">
        <div
          className="border-2 border-dashed border-gray-700 hover:border-orange-500 rounded-lg p-8 text-center cursor-pointer transition-colors"
          onClick={() => inputRef.current?.click()}
        >
          <input ref={inputRef} type="file" accept=".csv" className="hidden" onChange={handleFile} />
          <p className="text-gray-400 text-sm">
            {fileName ? (
              <span className="text-orange-400 font-medium">{fileName}</span>
            ) : (
              <>Click to select a CSV file</>
            )}
          </p>
          <p className="text-gray-600 text-xs mt-1">CSV files only</p>
        </div>

        {error && <p className="text-red-400 text-sm mt-3">{error}</p>}

        {result && (
          <div className="mt-4 p-3 bg-green-900/20 border border-green-700/40 rounded-lg">
            <p className="text-green-400 text-sm font-medium">Import complete</p>
            <p className="text-green-300 text-xs mt-0.5">
              {result.imported} lines imported · {result.skipped} skipped (invalid category or amount)
            </p>
          </div>
        )}
      </div>

      {rows.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden mb-4">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
            <p className="text-sm text-gray-300 font-medium">{rows.length} rows parsed — preview</p>
            <button onClick={handleImport} disabled={importing}
              className="bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white text-sm font-semibold px-4 py-1.5 rounded-lg">
              {importing ? "Importing…" : "Import"}
            </button>
          </div>
          <div className="grid grid-cols-[1fr_2fr_1fr] gap-4 px-4 py-2 border-b border-gray-800 text-xs text-gray-400 uppercase tracking-wider">
            <span>Category Code</span><span>Description</span><span className="text-right">Amount</span>
          </div>
          <div className="max-h-80 overflow-y-auto">
            {rows.map((r, i) => (
              <div key={i} className="grid grid-cols-[1fr_2fr_1fr] gap-4 px-4 py-2 border-t border-gray-800/50 text-sm">
                <span className="font-mono text-orange-300">{r.category_code}</span>
                <span className="text-gray-300">{r.description || "—"}</span>
                <span className="text-right text-gray-300">{fmtMoney(r.amount)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
