"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useLanguage } from "@/hooks/useLanguage";
import { t } from "@/lib/lang";

interface Version {
  id: number;
  version_label: string;
  change_type: string;
  change_description: string | null;
  status: string;
  created_at: string;
  budgets: { id: number; name: string };
  users: { id: number; username: string | null; email: string } | null;
  snapshot_json: string;
}

const TYPE_STYLE: Record<string, string> = {
  draft:    "text-yellow-400 bg-yellow-400/10",
  approved: "text-green-400 bg-green-400/10",
  revised:  "text-blue-400 bg-blue-400/10",
  voided:   "text-gray-500 bg-gray-500/10",
};

export default function TrazabilidadPage() {
  const searchParams = useSearchParams();
  const pid  = searchParams.get("pid");
  const lang = useLanguage();

  const [versions, setVersions] = useState<Version[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    if (!pid) return;
    fetch(`/api/trazabilidad?pid=${pid}`)
      .then(r => r.json())
      .then(d => { setVersions(d); setLoading(false); });
  }, [pid]);

  if (!pid)    return <p className="text-gray-400">{t("lbl_select_project", lang)}</p>;
  if (loading) return <p className="text-gray-400">{t("lbl_loading", lang)}</p>;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">{t("traz_title", lang)}</h1>
          <p className="text-gray-400 text-sm mt-0.5">
            {versions.length} {t("traz_count", lang)}
          </p>
        </div>
      </div>

      {versions.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 rounded-xl px-6 py-10 text-center">
          <p className="text-gray-500">{t("traz_no_data", lang)}</p>
          <p className="text-gray-600 text-sm mt-1">{t("traz_no_data_hint", lang)}</p>
        </div>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="grid grid-cols-[1fr_1fr_1.5fr_1fr_1fr_auto] gap-4 px-4 py-3 border-b border-gray-800 text-xs text-gray-400 uppercase tracking-wider">
            <span>{t("traz_col_version", lang)}</span>
            <span>{t("traz_col_budget",  lang)}</span>
            <span>{t("traz_col_desc",    lang)}</span>
            <span>{t("traz_col_type",    lang)}</span>
            <span>{t("traz_col_date",    lang)}</span>
            <span className="w-6" />
          </div>
          {versions.map(v => (
            <div key={v.id}>
              <div
                className="grid grid-cols-[1fr_1fr_1.5fr_1fr_1fr_auto] gap-4 px-4 py-2.5 border-t border-gray-800/50 text-sm items-center hover:bg-gray-800/20 cursor-pointer"
                onClick={() => setExpanded(expanded === v.id ? null : v.id)}
              >
                <span className="text-orange-400 font-mono font-semibold">{v.version_label}</span>
                <span className="text-gray-300 truncate">{v.budgets.name}</span>
                <span className="text-gray-400 truncate">{v.change_description ?? "—"}</span>
                <span className={`text-xs font-medium rounded px-2 py-0.5 w-fit ${TYPE_STYLE[v.change_type] ?? "text-gray-400 bg-gray-400/10"}`}>
                  {v.change_type}
                </span>
                <span className="text-gray-500 text-xs">{v.created_at.split("T")[0]}</span>
                <span className={`text-gray-500 text-xs transition-transform ${expanded === v.id ? "rotate-90" : ""}`}>▶</span>
              </div>
              {expanded === v.id && (
                <div className="px-4 py-3 bg-gray-800/30 border-t border-gray-800/50">
                  <p className="text-xs text-gray-500 mb-2">
                    {t("traz_created_by", lang)}: <span className="text-gray-400">{v.users?.username ?? v.users?.email ?? "unknown"}</span>
                    {" · "}{t("traz_status", lang)}: <span className="text-gray-400">{v.status}</span>
                  </p>
                  <pre className="text-xs text-gray-400 bg-gray-900 rounded p-3 overflow-x-auto max-h-60 whitespace-pre-wrap">
                    {JSON.stringify(JSON.parse(v.snapshot_json), null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
