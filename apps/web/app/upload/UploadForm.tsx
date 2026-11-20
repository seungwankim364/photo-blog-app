"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

type Item = {
  file: File;
  status: "waiting" | "uploading" | "done" | "error";
  photoId?: string;
  error?: string;
};

export default function UploadForm() {
  const router = useRouter();
  const [items, setItems] = useState<Item[]>([]);
  const [busy, setBusy] = useState(false);

  function update(index: number, patch: Partial<Item>) {
    setItems((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const input = e.currentTarget.elements.namedItem("files") as HTMLInputElement;
    const files = Array.from(input.files ?? []);
    if (files.length === 0) return;

    setItems(files.map((file) => ({ file, status: "waiting" })));
    setBusy(true);

    // One at a time: simpler errors, and the API isn't hit with many large bodies at once.
    for (const [i, file] of files.entries()) {
      update(i, { status: "uploading" });
      const body = new FormData();
      body.append("file", file);
      try {
        const res = await fetch("/api/photos", { method: "POST", body });
        const json = await res.json().catch(() => ({}));
        if (res.ok) update(i, { status: "done", photoId: json.id });
        else update(i, { status: "error", error: errorText(res.status, json) });
      } catch {
        update(i, { status: "error", error: "Network error" });
      }
    }

    setBusy(false);
    input.value = "";
    router.refresh();
  }

  return (
    <form className="upload-form" onSubmit={onSubmit}>
      <input
        type="file"
        name="files"
        multiple
        accept="image/jpeg,image/png,image/heic,image/heif,.heic,.heif"
        disabled={busy}
      />
      <div>
        <button type="submit" disabled={busy}>
          {busy ? "Uploading…" : "Upload"}
        </button>
      </div>

      {items.length > 0 && (
        <ul className="upload-list">
          {items.map((item, i) => (
            <li key={`${item.file.name}-${i}`}>
              <span>{item.file.name}</span>
              <span className={item.status === "error" ? "status-error" : "muted"}>
                {item.status === "done" && item.photoId ? (
                  <Link href={`/photos/${item.photoId}`}>View</Link>
                ) : item.status === "error" ? (
                  item.error
                ) : (
                  item.status
                )}
              </span>
            </li>
          ))}
        </ul>
      )}

      {!busy && items.some((item) => item.status === "done") && <Link href="/">Back to all photos</Link>}
    </form>
  );
}

/** The API sends { detail: "..." }, or a list of field errors for 422. */
function errorText(status: number, json: { detail?: unknown }): string {
  if (typeof json.detail === "string") return json.detail;
  if (status === 413) return "File too large";
  return `Upload failed (${status})`;
}
