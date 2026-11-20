import { getHealth } from "@/lib/api";

// Render on every request, so the status is live rather than baked in at build time.
export const dynamic = "force-dynamic";

export default async function Status() {
  const health = await getHealth();

  const pgvector = !health.apiReachable
    ? "unknown"
    : health.pgvector
      ? "installed"
      : health.database === "up"
        ? "not enabled (run the migration)"
        : "unknown";

  return (
    <main>
      <h1 style={{ fontSize: "1.25rem" }}>System check</h1>
      <ul>
        <li>API: {health.apiReachable ? "reachable" : "unreachable"}</li>
        <li>Database: {health.database ?? "unknown"}</li>
        <li>pgvector: {pgvector}</li>
        <li>Overall: {health.ready ? "ready" : "not ready"}</li>
      </ul>
    </main>
  );
}
