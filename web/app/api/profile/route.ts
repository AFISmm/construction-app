import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET() {
  const user = await getSession();
  if (!user) return NextResponse.json(null, { status: 401 });
  const profile = await prisma.extended_profiles.findUnique({ where: { user_id: user.id } });
  return NextResponse.json(profile ?? null);
}

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  const data = await req.json();
  const now = new Date();
  const profile = await prisma.extended_profiles.upsert({
    where: { user_id: user.id },
    create: {
      user_id: user.id,
      company_name: data.company_name ?? "",
      first_name: data.first_name ?? "",
      middle_name: data.middle_name ?? null,
      last_name: data.last_name ?? "",
      phone: data.phone ?? null,
      contact_email: data.contact_email ?? user.email,
      category: data.category ?? "",
      submitted_at: now,
    },
    update: {
      company_name: data.company_name,
      first_name: data.first_name,
      middle_name: data.middle_name ?? null,
      last_name: data.last_name,
      phone: data.phone ?? null,
      contact_email: data.contact_email,
      category: data.category,
    },
  });
  return NextResponse.json(profile);
}
