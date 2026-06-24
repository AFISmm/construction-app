import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json([], { status: 401 });
  const pid = req.nextUrl.searchParams.get("pid");
  if (!pid) return NextResponse.json([], { status: 400 });

  const lines = await prisma.budget_lines.findMany({
    where: { project_id: parseInt(pid) },
    select: { id: true, category_code: true, description: true, budgeted_amount: true },
    orderBy: { category_code: "asc" },
  });
  return NextResponse.json(lines);
}
