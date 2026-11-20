"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function DeleteButton({ id }: { id: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onDelete() {
    if (!confirm("Delete this photo? This can't be undone.")) return;
    setBusy(true);
    setError(null);
    const res = await fetch(`/api/photos/${id}`, { method: "DELETE" });
    if (res.ok || res.status === 404) {
      router.push("/");
      router.refresh();
    } else {
      setError(`Delete failed (${res.status})`);
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className="link" onClick={onDelete} disabled={busy}>
        {busy ? "Deleting…" : "Delete"}
      </button>
      {error && <span className="status-error">{error}</span>}
    </>
  );
}
