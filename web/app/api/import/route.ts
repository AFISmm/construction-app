import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

interface ImportRow {
  category_code: string;
  description: string;
  amount: number;
}

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { project_id, rows } = await req.json() as { project_id: number; rows: ImportRow[] };
  if (!project_id || !Array.isArray(rows) || rows.length === 0) {
    return NextResponse.json({ error: "project_id and rows required" }, { status: 400 });
  }

  const validCodes = (await prisma.categories.findMany({ select: { code: true } }))
    .map(c => c.code);

  const goodRows = rows.filter(r => validCodes.includes(r.category_code) && r.amount > 0);
  const badRows  = rows.filter(r => !validCodes.includes(r.category_code) || r.amount <= 0);

  const now = new Date();
  if (goodRows.length > 0) {
    await prisma.budget_lines.createMany({
      data: goodRows.map(r => ({
        project_id,
        category_code: r.category_code,
        description: r.description || null,
        budgeted_amount: r.amount,
        created_at: now,
        updated_at: now,
      })),
      skipDuplicates: false,
    });
  }

  return NextResponse.json({ imported: goodRows.length, skipped: badRows.length });
}
