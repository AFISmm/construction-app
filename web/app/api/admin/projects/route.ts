import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET() {
  const user = await getSession();
  if (!user) return NextResponse.json([], { status: 401 });

  const perm = await prisma.user_permissions.findUnique({ where: { user_id: user.id } });
  if (!["admin", "superadmin"].includes(perm?.role ?? "")) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const projects = await prisma.projects.findMany({
    where: { group_name: { not: null } },
    select: { id: true, name: true, group_name: true },
    orderBy: [{ group_name: "asc" }, { name: "asc" }],
  });
  return NextResponse.json(projects);
}
