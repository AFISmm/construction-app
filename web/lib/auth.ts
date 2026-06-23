import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";
import { prisma } from "./db";
import bcrypt from "bcryptjs";

const SECRET = new TextEncoder().encode(process.env.JWT_SECRET!);
const COOKIE = "session";

export interface SessionUser {
  id: number;
  email: string;
}

export async function signIn(email: string, password: string): Promise<SessionUser | null> {
  const user = await prisma.users.findUnique({
    where: { email: email.toLowerCase() },
    include: { user_passwords: true },
  });
  const hash = user?.user_passwords?.password_hash;
  if (!hash) return null;
  const ok = await bcrypt.compare(password, hash);
  if (!ok) return null;
  return { id: user!.id, email: user!.email };
}

export async function createSession(user: SessionUser): Promise<string> {
  return new SignJWT({ id: user.id, email: user.email })
    .setProtectedHeader({ alg: "HS256" })
    .setExpirationTime("7d")
    .sign(SECRET);
}

export async function getSession(): Promise<SessionUser | null> {
  const store = await cookies();
  const token = store.get(COOKIE)?.value;
  if (!token) return null;
  try {
    const { payload } = await jwtVerify(token, SECRET);
    return { id: payload.id as number, email: payload.email as string };
  } catch {
    return null;
  }
}

export async function clearSession() {
  const store = await cookies();
  store.delete(COOKIE);
}

export { COOKIE };
