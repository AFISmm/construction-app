import { NextRequest, NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { prisma } from "@/lib/db";
import { createSession, COOKIE } from "@/lib/auth";

function toUsername(first: string, last: string): string {
  const cap = (s: string) => s.trim().charAt(0).toUpperCase() + s.trim().slice(1).toLowerCase();
  return cap(first) + cap(last);
}

export async function POST(req: NextRequest) {
  const { firstName, lastName, email, password } = await req.json();

  if (!firstName || !lastName || !email || !password || password.length < 6) {
    return NextResponse.json(
      { error: "Todos los campos son obligatorios y la contraseña debe tener al menos 6 caracteres" },
      { status: 400 }
    );
  }

  try {
    const normalizedEmail = email.toLowerCase().trim();
    const username = toUsername(firstName, lastName);

    // Check username uniqueness
    const existingUsername = await prisma.users.findUnique({ where: { username } });
    if (existingUsername) {
      return NextResponse.json(
        {
          error: `El usuario "${username}" ya está en uso. Prueba usando tu segundo nombre o segundo apellido para diferenciarte (ej: FelipeAndrés Serna → FelipeAndresSerna).`,
        },
        { status: 409 }
      );
    }

    // Find or create user
    let user = await prisma.users.findUnique({ where: { email: normalizedEmail } });
    if (!user) {
      user = await prisma.users.create({
        data: {
          email: normalizedEmail,
          username,
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          created_at: new Date(),
        },
      });
    } else {
      // Update names/username if not set yet
      await prisma.users.update({
        where: { id: user.id },
        data: {
          username: user.username ?? username,
          first_name: user.first_name ?? firstName.trim(),
          last_name: user.last_name ?? lastName.trim(),
        },
      });
      user = await prisma.users.findUnique({ where: { id: user.id } }) ?? user;
    }

    // Check if password already set
    const existing = await prisma.user_passwords.findUnique({ where: { user_id: user.id } });
    if (existing) {
      return NextResponse.json(
        { error: "Esta cuenta ya existe. Inicia sesión." },
        { status: 409 }
      );
    }

    const hash = await bcrypt.hash(password, 12);
    await prisma.user_passwords.create({
      data: { user_id: user.id, password_hash: hash, updated_at: new Date() },
    });

    const token = await createSession({
      id: user.id,
      email: user.email,
      username: user.username ?? undefined,
    });
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
