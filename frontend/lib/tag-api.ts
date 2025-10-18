// frontend/lib/tag-api.ts
// Always hits /tag-service/... at same origin. No env edits required.

const RAW_BASE = process.env.NEXT_PUBLIC_TAG_BASE_PATH ?? "/tag-service";
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

function hashPath(s: string): number {
  // simple stable 32-bit hash for synthetic IDs
  let h = 2166136261 >>> 0;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return (h || 1) as number;
}

// Parse backend dictionary: { Primary: { Secondary: [Tertiary...] } }
function parseLegacyHierarchy(obj: Record<string, unknown>): TagNode[] {
  const makeNode = (name: string, parentPath: string | null): TagNode => {
    const path = parentPath ? `${parentPath}/${name}` : name;
    return {
      id: hashPath(path),
      tag_name: name,
      parent_id: parentPath ? hashPath(parentPath) : null,
      children: [],
    };
  };

  const primaries: TagNode[] = [];

  for (const [primaryName, secondaryVal] of Object.entries(obj)) {
    const primaryNode = makeNode(primaryName, null);

    if (secondaryVal && typeof secondaryVal === "object" && !Array.isArray(secondaryVal)) {
      for (const [secondaryName, tertiaryVal] of Object.entries(
        secondaryVal as Record<string, unknown>
      )) {
        const secondaryNode = makeNode(secondaryName, primaryName);

        if (Array.isArray(tertiaryVal)) {
          secondaryNode.children = (tertiaryVal as unknown[])
            .filter((x): x is string => typeof x === "string" && x.length > 0)
            .map((t) => makeNode(t, `${primaryName}/${secondaryName}`));
        } else if (tertiaryVal && typeof tertiaryVal === "object") {
          secondaryNode.children = Object.keys(tertiaryVal as Record<string, unknown>).map((t) =>
            makeNode(t, `${primaryName}/${secondaryName}`)
          );
        } else {
          secondaryNode.children = [];
        }

        primaryNode.children!.push(secondaryNode);
      }
    } else if (Array.isArray(secondaryVal)) {
      primaryNode.children = (secondaryVal as unknown[])
        .filter((x): x is string => typeof x === "string" && x.length > 0)
        .map((t) => makeNode(t, primaryName));
    } else {
      primaryNode.children = [];
    }

    primaries.push(primaryNode);
  }

  return primaries;
}

function normalizeToArray(payload: unknown): TagNode[] {
  if (Array.isArray(payload)) return payload as TagNode[];
  if (payload && typeof payload === "object") {
    const obj = payload as Record<string, unknown>;
    if (Array.isArray(obj.hierarchy)) return obj.hierarchy as TagNode[];
    if (Array.isArray(obj.data)) return obj.data as TagNode[];
    if (Array.isArray(obj.tags)) return obj.tags as TagNode[];
    if (Array.isArray(obj.results)) return obj.results as TagNode[];
    if (obj.root && Array.isArray(obj.root)) return obj.root as TagNode[];
    if (obj.tree && Array.isArray(obj.tree)) return obj.tree as TagNode[];
    const looksLikeDict = Object.values(obj).every((v) => typeof v === "object" || Array.isArray(v));
    if (looksLikeDict) return parseLegacyHierarchy(obj);
    if ("id" in obj && "tag_name" in obj) return [obj as TagNode];
  }
  return [];
}

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
  return normalizeToArray(payload);
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
  const res = await fetch(join(TAG_BASE_PATH, `/tags/${id}`), { method: "DELETE" });

  if (!res.ok) {
    await throwFromResponse(res, "Delete tag failed");
  }

  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    return res.json();
  }
  return { ok: true };
}
