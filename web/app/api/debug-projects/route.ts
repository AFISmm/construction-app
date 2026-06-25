import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET() {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: "not logged in" }, { status: 401 });

  const count = await prisma.projects.count();
  const sample = await prisma.projects.findMany({
    take: 5,
    select: { id: true, name: true, group_name: true, user_id: true },
  });

  return NextResponse.json({ total: count, sample });
}
