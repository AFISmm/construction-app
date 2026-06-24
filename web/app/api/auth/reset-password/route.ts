import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/db";

export async function POST(req: NextRequest) {
  const { email, password } = await req.json();

  if (!email || !password || password.length < 6) {
    return NextResponse.json(
      { error: "Email and password (min 6 chars) are required" },
      { status: 400 }
    );
  }

  try {
    const user = await prisma.users.findUnique({
      where: { email: email.toLowerCase().trim() },
    });

    if (!user) {
      return NextResponse.json(
        { error: "No account found with that email" },
        { status: 404 }
      );
    }

    const hash = await bcrypt.hash(password, 12);

    await prisma.user_passwords.upsert({
      where: { user_id: user.id },
      update: { password_hash: hash, updated_at: new Date() },
      create: { user_id: user.id, password_hash: hash, updated_at: new Date() },
    });

    return NextResponse.json({ ok: true });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Error: ${msg}` }, { status: 500 });
  }
}
