// app/tag-service/tags/route.ts
import { NextResponse } from "next/server";

// Normalize helpers
const uniq = <T,>(arr: T[]) => Array.from(new Set(arr.filter(Boolean as any))) as T[];
const noTrailSlash = (s: string) => (s.endsWith("/") ? s.slice(0, -1) : s);

// Build a smart list of ORIGIN candidates that commonly show up in local/dev/docker setups
const ORIGIN_CANDIDATES = uniq<string>([
  process.env.TAG_SERVICE_ORIGIN || "",
  process.env.BACKEND_ORIGIN || "",
  "http://localhost:5007",
  "http://127.0.0.1:5007",
  "http://localhost",          // nginx or local gateway
  "http://127.0.0.1",
  "http://nginx",              // docker service name patterns
  "http://backend",
  "http://tag-service:5007",
  "http://tag-service",
]).map(noTrailSlash);

// Some setups mount the service at root (/tags), others keep the service name in the path.
const PREFIX_CANDIDATES = ["", "/tag-service"] as const;

// We expect the upstream to expose /tags (optionally prefixed)
const TAGS_PATH = "/tags";

/** Try every (origin, prefix) combo until we get 2xx JSON back */
async function tryGetJSON() {
  const attempts: string[] = [];

  for (const origin of ORIGIN_CANDIDATES) {
    for (const prefix of PREFIX_CANDIDATES) {
      const url = `${origin}${prefix}${TAGS_PATH}`;
      try {
        const res = await fetch(url, { cache: "no-store" });
        const ct = res.headers.get("content-type") || "";
        if (res.ok && ct.includes("application/json")) {
          return res; // success
        }
        const short = (await res.text().catch(() => "")).slice(0, 160);
        attempts.push(`${url} -> ${res.status} ct=${ct} body=${short}`);
      } catch (e: any) {
        attempts.push(`${url} -> ERR ${String(e)}`);
      }
    }
  }

  throw new Error(
    "Could not reach a JSON Tag service.\n" + attempts.map((a, i) => `${i + 1}. ${a}`).join("\n")
  );
}

export async function GET() {
  try {
    const res = await tryGetJSON();
    const body = await res.text();
    return new NextResponse(body, {
      status: 200,
      headers: { "content-type": res.headers.get("content-type") || "application/json" },
    });
  } catch (e: any) {
    return new NextResponse(e?.message || "Upstream error", {
      status: 502,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }
}

export async function POST(req: Request) {
  const bodyText = await req.text();
  const contentType = req.headers.get("content-type") || "application/json";

  const attempts: string[] = [];
  for (const origin of ORIGIN_CANDIDATES) {
    for (const prefix of PREFIX_CANDIDATES) {
      const url = `${origin}${prefix}${TAGS_PATH}`;
      try {
        const res = await fetch(url, {
          method: "POST",
          headers: { "content-type": contentType },
          body: bodyText,
        });
        const ct = res.headers.get("content-type") || "";
        if (ct.includes("application/json")) {
          const text = await res.text();
          return new NextResponse(text, {
            status: res.status,
            headers: { "content-type": ct },
          });
        }
        const short = (await res.text().catch(() => "")).slice(0, 160);
        attempts.push(`${url} -> ${res.status} ct=${ct} body=${short}`);
      } catch (e: any) {
        attempts.push(`${url} -> ERR ${String(e)}`);
      }
    }
  }

  return new NextResponse(
    "Could not POST to Tag service.\n" + attempts.map((a, i) => `${i + 1}. ${a}`).join("\n"),
    { status: 502, headers: { "content-type": "text/plain; charset=utf-8" } }
  );
}
