// Server-side calls go straight to the API.
// Locally this is http://localhost:8000, on EKS it will be the in-cluster service URL.
const API_INTERNAL_URL = process.env.API_INTERNAL_URL ?? "http://localhost:8000";

export type Health = {
  // Did the API answer at all? Kept separate from readiness, so a missing
  // database doesn't look like the API itself is down.
  apiReachable: boolean;
  ready: boolean;
  database?: string;
  pgvector?: boolean;
};

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
