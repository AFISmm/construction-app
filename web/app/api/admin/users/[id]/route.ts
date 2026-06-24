import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function PATCH(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const perm = await prisma.user_permissions.findUnique({ where: { user_id: user.id } });
  if (perm?.role !== "admin") return NextResponse.json({ error: "Forbidden" }, { status: 403 });

  const { id } = await params;
  const { role } = await req.json();
  const targetId = parseInt(id);

  const existing = await prisma.user_permissions.findUnique({ where: { user_id: targetId } });
  const now = new Date();
  if (existing) {
    await prisma.user_permissions.update({
      where: { user_id: targetId },
      data: { role, updated_at: now },
    });
  } else {
    await prisma.user_permissions.create({
      data: {
        user_id: targetId,
        role,
        created_at: now,
        updated_at: now,
      },
    });
  }
  return NextResponse.json({ ok: true });
}
