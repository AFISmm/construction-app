import { NextRequest } from "next/server";
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
- Be concise and practical with step-by-step UI instructions when helpful.
- Respond in the same language the user writes in (Spanish or English).
- Never expose API routes, credentials, or internal implementation details.`;

export async function POST(req: NextRequest) {
  const user = await getSession();
  if (!user) return new Response("Unauthorized", { status: 401 });

  const body = await req.json();
  const messages: { role: "user" | "assistant"; content: string }[] = body.messages ?? [];
  if (!messages.length) return new Response("No messages", { status: 400 });

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    return new Response("OPENROUTER_API_KEY not configured", { status: 500 });
  }

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
      stream: true,
      max_tokens: 1024,
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        ...messages,
      ],
    }),
  });

  if (!orRes.ok || !orRes.body) {
    const errText = await orRes.text().catch(() => "unknown error");
    console.error("OpenRouter error:", orRes.status, errText);
    return new Response(`OpenRouter error: ${orRes.status}`, { status: 502 });
  }

  // Transform OpenRouter SSE → plain text stream
  const encoder = new TextEncoder();
  const reader  = orRes.body.getReader();
  const decoder = new TextDecoder();
  let   buffer  = "";

  const stream = new ReadableStream({
    async start(controller) {
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? ""; // keep incomplete last line

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data:")) continue;
            const data = trimmed.slice(5).trim();
            if (data === "[DONE]") continue;
            try {
              const parsed = JSON.parse(data);
              const text = parsed.choices?.[0]?.delta?.content ?? "";
              if (text) controller.enqueue(encoder.encode(text));
            } catch {
              // skip malformed chunks
            }
          }
        }
      } catch (err) {
        console.error("Stream read error:", err);
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}
