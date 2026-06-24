import { prisma } from "@/lib/db";
import { toNum } from "@/lib/format";
import ProjectGate from "@/components/ProjectGate";
import BudgetTable from "@/components/BudgetTable";

export interface BudgetLine {
  id: number;
  category_code: string;
  category_name: string;
  description: string;
  budgeted_amount: number;
  change_order_amount: number;
  paid: number;
}

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

  const [raw, categories] = await Promise.all([
    prisma.budget_lines.findMany({
      where: { project_id: projectId },
      orderBy: { category_code: "asc" },
      include: { expenses: { select: { amount: true } } },
    }),
    prisma.categories.findMany({ select: { code: true, name: true } }),
  ]);

  const catNames: Record<string, string> = {};
  for (const c of categories) catNames[c.code] = c.name;

  const lines: BudgetLine[] = raw.map((l: (typeof raw)[number]) => ({
    id: l.id,
    category_code: l.category_code,
    category_name: catNames[l.category_code] ?? l.category_code,
    description: l.description ?? catNames[l.category_code] ?? l.category_code,
    budgeted_amount: toNum(l.budgeted_amount),
    change_order_amount: toNum(l.change_order_amount),
    paid: l.expenses.reduce((s: number, e: { amount: unknown }) => s + toNum(e.amount), 0),
  }));

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">{project?.name ?? "Project"} — Budget</h1>
          <p className="text-gray-400 text-sm mt-0.5">
            {lines.filter(l => l.budgeted_amount > 0).length} of {lines.length} lines with values
          </p>
        </div>
      </div>
      <BudgetTable lines={lines} projectId={projectId} catNames={catNames} />
    </div>
  );
}
