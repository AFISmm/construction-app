import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET() {
  const user = await getSession();
  if (!user) return NextResponse.json([], { status: 401 });

  const projects = await prisma.projects.findMany({
    select: { id: true, name: true, group_name: true },
    orderBy: [{ group_name: "asc" }, { name: "asc" }],
  });

  return NextResponse.json(projects);
}
