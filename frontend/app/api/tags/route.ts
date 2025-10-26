import { NextResponse } from "next/server";
import fs from "node:fs/promises";
import path from "node:path";

const TAGS_ORIGIN = process.env.TAGS_ORIGIN || "http://localhost:5007";
const FALLBACK_PATH = path.join(process.cwd(), "public", "hierarchy.json");

async function readFallback() {
  const txt = await fs.readFile(FALLBACK_PATH, "utf8");
  return JSON.parse(txt);
}
async function writeFallback(data: any) {
  await fs.writeFile(FALLBACK_PATH, JSON.stringify(data, null, 2), "utf8");
}

// GET: try origin, else fallback file
export async function GET() {
  try {
    const r = await fetch(`${TAGS_ORIGIN}/tags`, { cache: "no-store" });
    if (r.ok) return NextResponse.json(await r.json());
    throw new Error(`origin GET ${r.status}`);
  } catch {
    const data = await readFallback();
    return NextResponse.json(data);
  }
}

// POST: add a tag (primary/secondary/tertiary)
export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  try {
    const r = await fetch(`${TAGS_ORIGIN}/tags`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (r.ok) return NextResponse.json(await r.json());
    throw new Error(`origin POST ${r.status}`);
  } catch {
    const { layer, name, parentPrimary, parentSecondary } = body || {};
    const data = await readFallback();

    if (layer === "primary") {
      if (!data[name]) data[name] = {};
    } else if (layer === "secondary") {
      if (!parentPrimary) return NextResponse.json({ error: "parentPrimary required" }, { status: 400 });
      data[parentPrimary] = data[parentPrimary] || {};
      data[parentPrimary][name] = data[parentPrimary][name] || [];
    } else if (layer === "tertiary") {
      if (!parentPrimary || !parentSecondary)
        return NextResponse.json({ error: "parentPrimary & parentSecondary required" }, { status: 400 });
      data[parentPrimary] = data[parentPrimary] || {};
      data[parentPrimary][parentSecondary] = data[parentPrimary][parentSecondary] || [];
      if (!data[parentPrimary][parentSecondary].includes(name)) {
        data[parentPrimary][parentSecondary].push(name);
      }
    } else {
      return NextResponse.json({ error: "invalid layer" }, { status: 400 });
    }

    await writeFallback(data);
    return NextResponse.json({ ok: true });
  }
}

// PATCH: rename a tag
export async function PATCH(req: Request) {
  const body = await req.json().catch(() => ({}));
  try {
    const r = await fetch(`${TAGS_ORIGIN}/tags`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (r.ok) return NextResponse.json(await r.json());
    throw new Error(`origin PATCH ${r.status}`);
  } catch {
    const { layer, oldName, newName, parentPrimary, parentSecondary } = body || {};
    const data = await readFallback();

    if (layer === "primary") {
      if (!data[oldName]) return NextResponse.json({ error: "primary not found" }, { status: 404 });
      data[newName] = data[oldName];
      delete data[oldName];
    } else if (layer === "secondary") {
      if (!parentPrimary || !data[parentPrimary]?.[oldName])
        return NextResponse.json({ error: "secondary not found" }, { status: 404 });
      data[parentPrimary][newName] = data[parentPrimary][oldName];
      delete data[parentPrimary][oldName];
    } else if (layer === "tertiary") {
      if (!parentPrimary || !parentSecondary)
        return NextResponse.json({ error: "parents required" }, { status: 400 });
      const arr: string[] = data[parentPrimary]?.[parentSecondary] || [];
      const idx = arr.findIndex((t) => t === oldName);
      if (idx === -1) return NextResponse.json({ error: "tertiary not found" }, { status: 404 });
      arr[idx] = newName;
      data[parentPrimary][parentSecondary] = arr;
    } else {
      return NextResponse.json({ error: "invalid layer" }, { status: 400 });
    }

    await writeFallback(data);
    return NextResponse.json({ ok: true });
  }
}
