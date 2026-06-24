import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";
import bcrypt from "bcryptjs";

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { currentPassword, newPassword } = await req.json();
  if (!currentPassword || !newPassword) {
    return NextResponse.json({ error: "currentPassword and newPassword required" }, { status: 400 });
  }
  if (newPassword.length < 8) {
    return NextResponse.json({ error: "New password must be at least 8 characters" }, { status: 400 });
  }

  const record = await prisma.user_passwords.findUnique({ where: { user_id: user.id } });
  if (!record) return NextResponse.json({ error: "No password set" }, { status: 400 });

  const ok = await bcrypt.compare(currentPassword, record.password_hash);
  if (!ok) return NextResponse.json({ error: "Incorrect current password" }, { status: 401 });

  const hash = await bcrypt.hash(newPassword, 12);
  await prisma.user_passwords.update({
    where: { user_id: user.id },
    data: { password_hash: hash, updated_at: new Date() },
  });
  return NextResponse.json({ ok: true });
}
