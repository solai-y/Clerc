import { NextResponse } from "next/server";
import { apiClient } from '@/lib/api';

// GET: fetch tag hierarchy from apiClient
export async function GET() {
  try {
    console.log('entered the function');
    const data = await apiClient.getTagHierarchy();
    console.log(data)
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Error loading tag hierarchy:', error.message || error);
    if (error.stack) {
      console.error(error.stack);
    }
    return NextResponse.json({ error: "Failed to load tag hierarchy", details: error.message || String(error) }, { status: 500 });
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
  } catch (error) {
    return NextResponse.json({ error: "Failed to add tag" }, { status: 500 });
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
  } catch (error) {
    return NextResponse.json({ error: "Failed to rename tag" }, { status: 500 });
  }
}

