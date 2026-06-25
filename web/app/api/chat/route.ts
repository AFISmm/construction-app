import { NextRequest } from "next/server";
import Anthropic from "@anthropic-ai/sdk";
import { getSession } from "@/lib/auth";

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const SYSTEM_PROMPT = `You are CK Assistant, an expert AI embedded inside the Chicken Kitchen Construction Budget App (ConstructionApp). You help users navigate, understand, and get the most out of the app.

## About the App
A web application for managing construction project budgets. Key modules:
- **Dashboard**: Overview of budget vs. actual spend per project, charts, summary cards
- **Budget (Presupuesto)**: Budget lines per category (labor, materials, etc.), inline editing, totals
- **Payments (Pagos/Expenses)**: Record actual expenses, link to budget line, vendor, attach notes
- **Vendors (Proveedores)**: Manage contractors and suppliers, track status (active/inactive/pending)
- **Versioning (Trazabilidad)**: Create snapshots of the budget at any point in time; compare versions
- **Import (Importar)**: Upload CSV files to bulk-import budget lines using category codes
- **Account (Cuenta)**: Change password
- **Profile (Perfil)**: Edit company name, contact info, role category
- **Admin**: Manage users — assign roles, set per-module view/edit permissions, project visibility, delete users

## Roles
- superadmin: full access, can delete users
- admin: manage users and all modules
- standard: normal user, access per permissions
- viewer: read-only access per permissions
- approver: can approve budget versions

## Tech Stack (for developers)
Next.js 16 App Router, Prisma ORM v7, Supabase PostgreSQL, JWT auth via jose, Tailwind CSS, Vercel deployment.

## Language
Respond in the same language the user writes in. The app supports English and Spanish.

## Guidelines
- Be concise and practical. Give step-by-step instructions when guiding users through the UI.
- If asked about something outside the app's scope, briefly acknowledge and redirect to what you can help with.
- Never expose internal API routes, database credentials, or sensitive implementation details.
- If a user reports a bug, acknowledge it and suggest they contact the admin or refresh/retry.`;

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return new Response("Unauthorized", { status: 401 });

  const body = await req.json();
  const messages: { role: "user" | "assistant"; content: string }[] = body.messages ?? [];

  if (!messages.length) return new Response("No messages", { status: 400 });

  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      try {
        const response = await client.messages.stream({
          model: "claude-haiku-4-5-20251001",
          max_tokens: 1024,
          system: SYSTEM_PROMPT,
          messages,
        });

        for await (const chunk of response) {
          if (
            chunk.type === "content_block_delta" &&
            chunk.delta.type === "text_delta"
          ) {
            controller.enqueue(encoder.encode(chunk.delta.text));
          }
        }
      } catch (err) {
        console.error("Chat stream error:", err);
        controller.enqueue(encoder.encode("\n[Error generating response]"));
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Transfer-Encoding": "chunked",
      "Cache-Control": "no-cache",
    },
  });
}
