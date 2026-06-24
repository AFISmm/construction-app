import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET() {
  const user = await getSession();
  if (!user) return NextResponse.json([], { status: 401 });

  const cats = await prisma.categories.findMany({
    select: { code: true, name: true, level: true, parent_code: true },
    orderBy: { code: "asc" },
  });

  return NextResponse.json(cats);
}
