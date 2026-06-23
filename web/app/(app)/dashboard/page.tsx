import { prisma } from "@/lib/db";
import { fmtMoney, toNum } from "@/lib/format";
import ProjectGate from "@/components/ProjectGate";

interface DashLine {
  id: number;
  description: string;
  category_code: string;
  budgeted: number;
  adjusted: number;
  paid: number;
}

interface Metric {
  label: string;
  value: number;
  colored?: boolean;
}

async function getDashboardData(projectId: number): Promise<DashLine[]> {
  const lines = await prisma.budget_lines.findMany({
    where: { project_id: projectId, budgeted_amount: { gt: 0 } },
    include: { expenses: true },
    orderBy: { category_code: "asc" },
  });

  return lines.map(l => ({
    id: l.id,
    description: l.description ?? l.category_code,
    category_code: l.category_code,
    budgeted: toNum(l.budgeted_amount),
    adjusted: toNum(l.change_order_amount) > 0
      ? toNum(l.change_order_amount)
      : toNum(l.budgeted_amount),
    paid: l.expenses.reduce((s: number, e) => s + toNum(e.amount), 0),
  }));
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ pid?: string }>;
}) {
  const params = await searchParams;
  const projectId = params.pid ? parseInt(params.pid) : null;
  if (!projectId) return <ProjectGate />;

  const project = await prisma.projects.findUnique({
    where: { id: projectId },
    select: { name: true },
  });

  const lines = await getDashboardData(projectId);
  const totalBudget = lines.reduce((s: number, l: DashLine) => s + l.budgeted, 0);
  const totalAdj    = lines.reduce((s: number, l: DashLine) => s + l.adjusted, 0);
  const totalPaid   = lines.reduce((s: number, l: DashLine) => s + l.paid, 0);
  const balance = totalAdj - totalPaid;

  const groups: Record<string, DashLine[]> = {};
  for (const l of lines) {
    const top = l.category_code.split(".")[0];
    groups[top] = [...(groups[top] ?? []), l];
  }

  const metrics: Metric[] = [
    { label: "Estimated Budget", value: totalBudget },
    { label: "Adjusted Budget",  value: totalAdj },
    { label: "Payments to Date", value: totalPaid },
    { label: "Balance",          value: balance, colored: true },
  ];

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-1">{project?.name ?? "Project"}</h1>
      <p className="text-gray-400 text-sm mb-6">Budget Dashboard</p>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {metrics.map((m: Metric) => (
          <div key={m.label} className="bg-gray-900 border border-gray-800 rounded-xl p-4">
            <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">{m.label}</p>
            <p className={`text-xl font-bold ${m.colored ? (balance < 0 ? "text-red-400" : "text-green-400") : "text-white"}`}>
              {fmtMoney(m.value)}
            </p>
          </div>
        ))}
      </div>

      {lines.length === 0 ? (
        <p className="text-gray-500 text-sm">No budget lines with values yet.</p>
      ) : (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr] gap-4 px-4 py-3 border-b border-gray-800 text-xs text-gray-400 uppercase tracking-wider">
            <span>Category</span>
            <span className="text-right">Budget</span>
            <span className="text-right">Adjusted</span>
            <span className="text-right">Paid</span>
            <span className="text-right">Balance</span>
          </div>

          {Object.entries(groups).sort().map(([top, groupLines]: [string, DashLine[]]) => (
            <div key={top}>
              <div className="px-4 py-2 bg-gray-800/50 text-sm font-semibold text-gray-300">
                {top}
              </div>
              {groupLines.map((l: DashLine) => {
                const bal = l.adjusted - l.paid;
                return (
                  <div
                    key={l.id}
                    className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr] gap-4 px-4 py-2.5 border-t border-gray-800/50 text-sm hover:bg-gray-800/30 transition-colors"
                  >
                    <span className="text-gray-300 pl-3 truncate" title={l.description}>
                      {l.description}
                    </span>
                    <span className="text-right text-gray-300">{fmtMoney(l.budgeted)}</span>
                    <span className="text-right text-gray-300">{fmtMoney(l.adjusted)}</span>
                    <span className="text-right text-gray-300">{fmtMoney(l.paid)}</span>
                    <span className={`text-right font-medium ${bal < 0 ? "text-red-400" : "text-gray-300"}`}>
                      {fmtMoney(bal)}
                    </span>
                  </div>
                );
              })}
            </div>
          ))}

          <div className="grid grid-cols-[2fr_1fr_1fr_1fr_1fr] gap-4 px-4 py-3 border-t border-gray-700 font-bold text-sm bg-gray-800/30">
            <span className="text-white">Total</span>
            <span className="text-right text-white">{fmtMoney(totalBudget)}</span>
            <span className="text-right text-white">{fmtMoney(totalAdj)}</span>
            <span className="text-right text-white">{fmtMoney(totalPaid)}</span>
            <span className={`text-right ${balance < 0 ? "text-red-400" : "text-green-400"}`}>
              {fmtMoney(balance)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
