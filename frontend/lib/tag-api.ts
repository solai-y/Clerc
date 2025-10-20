// frontend/lib/tag-api.ts
// Always hits /tag-service/... at same origin. No env edits required.

const RAW_BASE = "/tag-service";
const TAG_BASE_PATH = RAW_BASE.startsWith("/") ? RAW_BASE : `/${RAW_BASE}`;

function join(base: string, path: string) {
  const right = path.startsWith("/") ? path : `/${path}`;
  return `${base}${right}`;
}

export type TagNode = {
  id: number;
  tag_name: string;
  parent_id: number | null;
  tier?: "primary" | "secondary" | "tertiary";
  children?: TagNode[];
};

/* ---------------- utils ---------------- */

// Do NOT read body here — only check header and throw.
function assertJsonContent(res: Response) {
  const ct = res.headers.get("content-type") || "";
  if (!ct.includes("application/json")) {
    throw new Error(`Unexpected content-type: ${ct || "unknown"}`);
  }
}

// Read the body exactly once and try to extract a message
async function throwFromResponse(res: Response, fallbackMsg: string) {
  const text = await res.text(); // single read
  try {
    const j = JSON.parse(text);
    const msg =
      j?.message || j?.detail || j?.error || j?.errors?.[0] || JSON.stringify(j);
    throw new Error(msg || `${fallbackMsg}: ${res.status}`);
  } catch {
    throw new Error(text || `${fallbackMsg}: ${res.status}`);
  }
}

/* --------------- API calls --------------- */

export async function getTags(): Promise<TagNode[]> {
  const res = await fetch(join(TAG_BASE_PATH, "/tags"), { cache: "no-store" });
  if (!res.ok) {
    await throwFromResponse(res, "Failed to load tags");
  }
  assertJsonContent(res);
  const payload = await res.json();
  // return normalizeToArray(payload);
  return payload as TagNode[];
}

export async function createTag(input: { tag_name: string; parent_id?: number | null }) {
  const res = await fetch(join(TAG_BASE_PATH, "/tags"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });

  if (!res.ok) {
    await throwFromResponse(res, "Create tag failed");
  }

  // If backend returns JSON, parse it; otherwise return a trivial success
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return res.json();
  }
  return { ok: true };
}

export async function updateTag(input: { id: number; tag_name: string; parent_id: number | null }) {
  const res = await fetch(join(TAG_BASE_PATH, `/tags/${input.id}`), {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ tag_name: input.tag_name, parent_id: input.parent_id }),
  });

  if (!res.ok) {
    await throwFromResponse(res, "Update tag failed");
  }

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return res.json();
  }
  return { ok: true };
}


export async function deleteTag(id: number) {
  const res = await fetch(`${TAG_BASE_PATH}/tags/${id}`, { method: "DELETE" });
  if (!res.ok) {
    await throwFromResponse(res, "Delete tag failed");
  }

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return res.json();
  }
  return { ok: true };
}
