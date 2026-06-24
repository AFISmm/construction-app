import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";
import { getSession } from "@/lib/auth";

export async function GET(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json([], { status: 401 });
  const pid = req.nextUrl.searchParams.get("pid");
  if (!pid) return NextResponse.json([], { status: 400 });

  const vendors = await prisma.vendors.findMany({
    where: { project_id: parseInt(pid) },
    orderBy: { company_name: "asc" },
  });
  return NextResponse.json(vendors);
}

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { project_id, company_name, contact_name, phone, email, trade, nit, notes } = await req.json();
  if (!project_id || !company_name) {
    return NextResponse.json({ error: "project_id and company_name required" }, { status: 400 });
  }

  const vendor = await prisma.vendors.create({
    data: {
      project_id,
      company_name: company_name.trim(),
      contact_name: contact_name || null,
      phone: phone || null,
      email: email || null,
      trade: trade || null,
      nit: nit || null,
      notes: notes || null,
      status: "pending",
    },
  });
  return NextResponse.json(vendor, { status: 201 });
}
