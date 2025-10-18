// app/tag-service/tags/[id]/route.ts
import { NextResponse } from "next/server";

const uniq = <T,>(arr: T[]) => Array.from(new Set(arr.filter(Boolean as any))) as T[];
const noTrailSlash = (s: string) => (s.endsWith("/") ? s.slice(0, -1) : s);

const ORIGIN_CANDIDATES = uniq<string>([
  process.env.TAG_SERVICE_ORIGIN || "",
  process.env.BACKEND_ORIGIN || "",
  "http://localhost:5007",
  "http://127.0.0.1:5007",
  "http://localhost",
  "http://127.0.0.1",
  "http://nginx",
  "http://backend",
  "http://tag-service:5007",
  "http://tag-service",
]).map(noTrailSlash);

const PREFIX_CANDIDATES = ["", "/tag-service"] as const;

export async function PATCH(req: Request, { params }: { params: { id: string } }) {
  const id = encodeURIComponent(params.id);
  const body = await req.text();
  const contentType = req.headers.get("content-type") || "application/json";

  const attempts: string[] = [];
  for (const origin of ORIGIN_CANDIDATES) {
    for (const prefix of PREFIX_CANDIDATES) {
      const url = `${origin}${prefix}/tags/${id}`;
      try {
        const res = await fetch(url, { method: "PATCH", headers: { "content-type": contentType }, body });
        const ct = res.headers.get("content-type") || "";
        if (ct.includes("application/json")) {
          const text = await res.text();
          return new NextResponse(text, { status: res.status, headers: { "content-type": ct } });
        }
        const short = (await res.text().catch(() => "")).slice(0, 160);
        attempts.push(`${url} -> ${res.status} ct=${ct} body=${short}`);
      } catch (e: any) {
        attempts.push(`${url} -> ERR ${String(e)}`);
      }
    }
  }

  return new NextResponse(
    "Could not PATCH Tag service.\n" + attempts.map((a, i) => `${i + 1}. ${a}`).join("\n"),
    { status: 502, headers: { "content-type": "text/plain; charset=utf-8" } }
  );
}
