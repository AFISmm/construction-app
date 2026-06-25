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
  if (!["admin", "superadmin"].includes(perm?.role ?? "")) {
    return NextResponse.json({ error: "Forbidden" }, { status: 403 });
  }

  const { id } = await params;
  const targetId = parseInt(id);
  const body = await req.json();
  const now = new Date();

  // Update username if provided
  if (body.username !== undefined) {
    const trimmed = (body.username as string).trim();
    if (trimmed) {
      // check uniqueness
      const conflict = await prisma.users.findFirst({
        where: { username: trimmed, id: { not: targetId } },
      });
      if (conflict) {
        return NextResponse.json({ error: "Username already taken" }, { status: 409 });
      }
      await prisma.users.update({
        where: { id: targetId },
        data: { username: trimmed },
      });
    }
  }

  // Update permissions if role/pages/approver provided
  if (body.role !== undefined || body.allowed_pages !== undefined || body.is_budget_approver !== undefined || body.allowed_project_ids !== undefined) {
    const pagesValue = body.allowed_pages === null
      ? null
      : body.allowed_pages !== undefined ? JSON.stringify(body.allowed_pages) : undefined;

    const projectsValue = body.allowed_project_ids === null
      ? null
      : body.allowed_project_ids !== undefined ? JSON.stringify(body.allowed_project_ids) : undefined;

    const existing = await prisma.user_permissions.findUnique({ where: { user_id: targetId } });
    if (existing) {
      await prisma.user_permissions.update({
        where: { user_id: targetId },
        data: {
          ...(body.role !== undefined            && { role: body.role }),
          ...(body.is_budget_approver !== undefined && { is_budget_approver: body.is_budget_approver }),
          ...(pagesValue    !== undefined        && { allowed_pages: pagesValue }),
          ...(projectsValue !== undefined        && { allowed_project_ids: projectsValue }),
          updated_at: now,
        },
      });
    } else {
      await prisma.user_permissions.create({
        data: {
          user_id:            targetId,
          role:               body.role ?? "standard",
          is_budget_approver: body.is_budget_approver ?? false,
          allowed_pages:      pagesValue ?? null,
          allowed_project_ids: projectsValue ?? null,
          created_at: now,
          updated_at: now,
        },
      });
    }
  }

  return NextResponse.json({ ok: true });
}
