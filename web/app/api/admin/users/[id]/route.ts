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
  const { role, is_budget_approver, allowed_pages } = await req.json();
  const targetId = parseInt(id);
  const now = new Date();

  // allowed_pages: null means all access; array means restricted
  const pagesValue = allowed_pages === null
    ? null
    : JSON.stringify(allowed_pages);

  const existing = await prisma.user_permissions.findUnique({ where: { user_id: targetId } });
  if (existing) {
    await prisma.user_permissions.update({
      where: { user_id: targetId },
      data: {
        role,
        is_budget_approver: is_budget_approver ?? false,
        allowed_pages: pagesValue,
        updated_at: now,
      },
    });
  } else {
    await prisma.user_permissions.create({
      data: {
        user_id: targetId,
        role,
        is_budget_approver: is_budget_approver ?? false,
        allowed_pages: pagesValue,
        created_at: now,
        updated_at: now,
      },
    });
  }
  return NextResponse.json({ ok: true });
}
