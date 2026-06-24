import { NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET() {
  const user = await getSession();
  if (!user) return NextResponse.json([], { status: 401 });

  const perm = await prisma.user_permissions.findUnique({ where: { user_id: user.id } });
  if (perm?.role !== "admin") return NextResponse.json({ error: "Forbidden" }, { status: 403 });

  const users = await prisma.users.findMany({
    select: {
      id: true,
      email: true,
      username: true,
      first_name: true,
      last_name: true,
      created_at: true,
      user_permissions: { select: { role: true } },
    },
    orderBy: { created_at: "asc" },
  });
  return NextResponse.json(users);
}
