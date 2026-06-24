import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json([], { status: 401 });
  const pid = req.nextUrl.searchParams.get("pid");
  if (!pid) return NextResponse.json([], { status: 400 });

  const expenses = await prisma.expenses.findMany({
    where: { project_id: parseInt(pid) },
    include: { budget_lines: { select: { category_code: true, description: true } } },
    orderBy: { expense_date: "desc" },
  });
  return NextResponse.json(expenses);
}

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { project_id, budget_line_id, vendor, description, amount, expense_date } = await req.json();
  if (!project_id || !budget_line_id || !amount) {
    return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
  }

  const expense = await prisma.expenses.create({
    data: {
      project_id,
      budget_line_id,
      vendor: vendor || null,
      description: description || null,
      amount,
      expense_date: new Date(expense_date ?? Date.now()),
      created_at: new Date(),
      updated_at: new Date(),
      created_by: user.id,
    },
  });
  return NextResponse.json(expense, { status: 201 });
}
