import { NextResponse } from "next/server";
import fs from "node:fs/promises";
import path from "node:path";
import { apiClient } from '@/lib/api';

const FALLBACK_PATH = path.join(process.cwd(), "public", "hierarchy.json");

async function readFallback() {
  const txt = await fs.readFile(FALLBACK_PATH, "utf8");
  return JSON.parse(txt);
}

async function writeFallback(data: any) {
  await fs.writeFile(FALLBACK_PATH, JSON.stringify(data, null, 2), "utf8");
}


// GET: try apiClient, else fallback file
export async function GET() {
  try {
    const data = await apiClient.getTagHierarchy();
    return NextResponse.json(data);
  } catch {
    const data = await readFallback();
    return NextResponse.json(data);
  }
}


// POST: add a tag (primary/secondary/tertiary)
export async function POST(req: Request) {
  const body = await req.json().catch(() => ({}));
  const { layer, name, parentPrimary, parentSecondary } = body || {};

  // Validation
  if (!layer || !name) {
    return NextResponse.json({ error: "layer and name are required" }, { status: 400 });
  }
  if (layer === "secondary" && !parentPrimary) {
    return NextResponse.json({ error: "parentPrimary required for secondary layer" }, { status: 400 });
  }
  if (layer === "tertiary" && (!parentPrimary || !parentSecondary)) {
    return NextResponse.json({ error: "parentPrimary and parentSecondary required for tertiary layer" }, { status: 400 });
  }

  try {
    const result = await apiClient.addTag(body);
    return NextResponse.json({ ok: true, id: result.id, message: result.message });
  } catch {
    const data = await readFallback();

    if (layer === "primary") {
      if (!data[name]) data[name] = {};
    } else if (layer === "secondary") {
      data[parentPrimary] = data[parentPrimary] || {};
      data[parentPrimary][name] = data[parentPrimary][name] || [];
    } else if (layer === "tertiary") {
      data[parentPrimary] = data[parentPrimary] || {};
      data[parentPrimary][parentSecondary] = data[parentPrimary][parentSecondary] || [];
      if (!data[parentPrimary][parentSecondary].includes(name)) {
        data[parentPrimary][parentSecondary].push(name);
      }
    } else {
      return NextResponse.json({ error: "invalid layer" }, { status: 400 });
    }

    await writeFallback(data);
    return NextResponse.json({ ok: true, fallback: true });
  }
}


// PATCH: rename a tag
export async function PATCH(req: Request) {
  const body = await req.json().catch(() => ({}));
  const { layer, oldName, newName, parentPrimary, parentSecondary } = body || {};

  // Validation
  if (!layer || !oldName || !newName) {
    return NextResponse.json({ error: "layer, oldName and newName are required" }, { status: 400 });
  }
  if (layer === "secondary" && !parentPrimary) {
    return NextResponse.json({ error: "parentPrimary required for secondary layer" }, { status: 400 });
  }
  if (layer === "tertiary" && (!parentPrimary || !parentSecondary)) {
    return NextResponse.json({ error: "parentPrimary and parentSecondary required for tertiary layer" }, { status: 400 });
  }

  try {
    const result = await apiClient.editTag(body);
    return NextResponse.json({ ok: true, message: result.message });
  } catch {
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
      const arr: string[] = data[parentPrimary]?.[parentSecondary] || [];
      const idx = arr.findIndex((t) => t === oldName);
      if (idx === -1) return NextResponse.json({ error: "tertiary not found" }, { status: 404 });
      arr[idx] = newName;
      data[parentPrimary][parentSecondary] = arr;
    } else {
      return NextResponse.json({ error: "invalid layer" }, { status: 400 });
    }

    await writeFallback(data);
    return NextResponse.json({ ok: true, fallback: true });
  }
}
