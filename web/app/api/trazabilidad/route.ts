import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json([], { status: 401 });
  const pid = req.nextUrl.searchParams.get("pid");
  if (!pid) return NextResponse.json([], { status: 400 });

  const versions = await prisma.budget_versions.findMany({
    where: { budgets: { project_id: parseInt(pid) } },
    include: {
      budgets: { select: { id: true, name: true } },
      users: { select: { id: true, username: true, email: true } },
    },
    orderBy: { created_at: "desc" },
  });
  return NextResponse.json(versions);
}

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { budget_id, change_description, change_type } = await req.json();
  if (!budget_id) return NextResponse.json({ error: "budget_id required" }, { status: 400 });

  const budget = await prisma.budgets.findUnique({ where: { id: budget_id } });
  if (!budget) return NextResponse.json({ error: "Budget not found" }, { status: 404 });

  const budgetLines = await prisma.budget_lines.findMany({
    where: { project_id: budget.project_id },
    orderBy: { category_code: "asc" },
  });

  const lastVersion = await prisma.budget_versions.findFirst({
    where: { budget_id },
    orderBy: [{ version_major: "desc" }, { version_minor: "desc" }],
  });
  const newMinor = lastVersion ? lastVersion.version_minor + 1 : 0;
  const newMajor = lastVersion ? lastVersion.version_major : 1;

  const version = await prisma.budget_versions.create({
    data: {
      budget_id,
      version_major: newMajor,
      version_minor: newMinor,
      version_label: `v${newMajor}.${newMinor}`,
      change_type: change_type ?? "draft",
      change_description: change_description ?? null,
      status: "active",
      snapshot_json: JSON.stringify(budgetLines),
      created_at: new Date(),
      created_by: user.id,
    },
  });
  return NextResponse.json(version, { status: 201 });
}
