import { prisma } from "@/lib/db";
import { fmtMoney, toNum } from "@/lib/format";
import ProjectGate from "@/components/ProjectGate";
import BudgetTable from "@/components/BudgetTable";

export default async function BudgetPage({
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

  const lines = await prisma.budget_lines.findMany({
    where: { project_id: projectId },
    orderBy: { category_code: "asc" },
    select: {
      id: true,
      category_code: true,
      description: true,
      budgeted_amount: true,
      change_order_amount: true,
    },
  });

  const serialized = lines.map(l => ({
    id: l.id,
    category_code: l.category_code,
    description: l.description ?? l.category_code,
    budgeted_amount: toNum(l.budgeted_amount),
    change_order_amount: toNum(l.change_order_amount),
  }));

  const totalBudget = serialized.reduce((s, l) => s + l.budgeted_amount, 0);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">{project?.name ?? "Project"} — Budget</h1>
          <p className="text-gray-400 text-sm mt-0.5">
            {serialized.filter(l => l.budgeted_amount > 0).length} of {serialized.length} lines with values
            · Total: <span className="text-white font-semibold">{fmtMoney(totalBudget)}</span>
          </p>
        </div>
      </div>
      <BudgetTable lines={serialized} projectId={projectId} />
    </div>
  );
}
