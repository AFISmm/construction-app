import { NextRequest, NextResponse } from "next/server";
import { getSession } from "@/lib/auth";

const SYSTEM_PROMPT = `You are CK Assistant, an expert AI embedded inside the Chicken Kitchen Construction Budget App. You help users navigate, understand, and get the most out of the app.

## App Modules
- Dashboard: budget vs. actual spend overview, charts
- Budget (Presupuesto): budget lines per category, inline editing
- Payments (Pagos): record actual expenses, link to budget line and vendor
- Vendors (Proveedores): manage contractors/suppliers, track status
- Versioning (Trazabilidad): save budget snapshots, compare versions
- Import (Importar): upload CSV to bulk-import budget lines
- Account (Cuenta): change password
- Profile (Perfil): company info, contact details
- Admin: manage users, roles, module permissions, project visibility

## Roles: superadmin, admin, standard, viewer, approver

## Guidelines
- Be concise and practical. Give step-by-step UI instructions when helpful.
- Respond in the same language the user writes in (Spanish or English).
- Never expose API routes, credentials, or internal implementation details.`;

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const body = await req.json();
  const messages: { role: "user" | "assistant"; content: string }[] = body.messages ?? [];
  if (!messages.length) return NextResponse.json({ error: "No messages" }, { status: 400 });

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: "OPENROUTER_API_KEY not set" }, { status: 500 });
  }

  try {
    const orRes = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://construction-app-weld.vercel.app",
        "X-Title": "CK Construction Budget App",
      },
      body: JSON.stringify({
        model: "meta-llama/llama-3.1-8b-instruct:free",
        stream: false,
        max_tokens: 1024,
        messages: [
          { role: "system", content: SYSTEM_PROMPT },
          ...messages,
        ],
      }),
    });

    const data = await orRes.json();

    if (!orRes.ok) {
      console.error("OpenRouter error:", orRes.status, JSON.stringify(data));
      return NextResponse.json(
        { error: `OpenRouter ${orRes.status}: ${data?.error?.message ?? JSON.stringify(data)}` },
        { status: 502 }
      );
    }

    const text: string = data.choices?.[0]?.message?.content ?? "";
    return NextResponse.json({ text });

  } catch (err) {
    console.error("Chat fetch error:", err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
