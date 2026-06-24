import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/db";
import { createSession, COOKIE } from "@/lib/auth";

export async function POST(req: NextRequest) {
  const { email, password } = await req.json();

  if (!email || !password || password.length < 6) {
    return NextResponse.json(
      { error: "Email and password (min 6 chars) are required" },
      { status: 400 }
    );
  }

  try {
    const normalizedEmail = email.toLowerCase().trim();

    // Find or create user
    let user = await prisma.users.findUnique({ where: { email: normalizedEmail } });
    if (!user) {
      user = await prisma.users.create({
        data: { email: normalizedEmail, created_at: new Date() },
      });
    }

    // Check if password already set
    const existing = await prisma.user_passwords.findUnique({ where: { user_id: user.id } });
    if (existing) {
      return NextResponse.json(
        { error: "Account already exists. Use Sign in." },
        { status: 409 }
      );
    }

    // Hash and save password
    const hash = await bcrypt.hash(password, 12);
    await prisma.user_passwords.create({
      data: { user_id: user.id, password_hash: hash, updated_at: new Date() },
    });

    // Auto-login
    const token = await createSession({ id: user.id, email: user.email });
    const res = NextResponse.json({ ok: true });
    res.cookies.set(COOKIE, token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 7,
      path: "/",
    });
    return res;
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Error: ${msg}` }, { status: 500 });
  }
}
