// Server-side calls go straight to the API.
// Locally this is http://localhost:8000, on EKS it will be the in-cluster service URL.
export const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

export type Health = {
  // Did the API answer at all? Kept separate from readiness, so a missing
  // database doesn't look like the API itself is down.
  apiReachable: boolean;
  ready: boolean;
  database?: string;
  pgvector?: boolean;
};

export type Photo = {
  id: string;
  original_filename: string;
  content_type: string;
  size_bytes: number;
  width: number | null;
  height: number | null;
  taken_at: string | null;
  camera_make: string | null;
  camera_model: string | null;
  lens_model: string | null;
  focal_length_mm: number | null;
  focal_35mm: number | null;
  aperture: number | null;
  shutter: string | null;
  iso: number | null;
  created_at: string;
};

export type PhotoDetail = Photo & { exif_raw: Record<string, unknown> };

export type ImageSize = "thumb" | "display" | "original";

/** Image URL for the browser. It goes through this app's /api proxy, because the
 *  browser can't reach API_INTERNAL_URL once the API is inside the cluster. */
export function photoSrc(id: string, size: ImageSize): string {
  return `/api/photos/${id}/file?size=${size}`;
}

export async function getHealth(): Promise<Health> {
  try {
    // /health/ready answers 503 when not ready, and still sends a JSON body.
    const res = await fetch(`${API_INTERNAL_URL}/health/ready`, { cache: "no-store" });
    const body = (await res.json()) as { status: string; database?: string; pgvector?: boolean };
    return {
      apiReachable: true,
      ready: body.status === "ok",
      database: body.database,
      pgvector: body.pgvector,
    };
  } catch {
    return { apiReachable: false, ready: false };
  }
}

export async function listPhotos(limit = 200): Promise<Photo[]> {
  const res = await fetch(`${API_INTERNAL_URL}/photos?limit=${limit}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET /photos failed: ${res.status}`);
  return res.json();
}

/** null when the photo doesn't exist, so the page can show a 404. */
export async function getPhoto(id: string): Promise<PhotoDetail | null> {
  const res = await fetch(`${API_INTERNAL_URL}/photos/${encodeURIComponent(id)}`, {
    cache: "no-store",
  });
  // 422 means the id isn't a valid UUID, which is also "no such photo".
  if (res.status === 404 || res.status === 422) return null;
  if (!res.ok) throw new Error(`GET /photos/${id} failed: ${res.status}`);
  return res.json();
}
