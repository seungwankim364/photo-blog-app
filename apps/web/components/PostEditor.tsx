"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { photoSrc, type Photo, type PostDetail } from "@/lib/api";

type Selected = { photo_id: string; caption: string };

type Props = {
  photos: Photo[]; // every uploaded photo, to choose from
  post?: PostDetail; // set when editing
};

export default function PostEditor({ photos, post }: Props) {
  const router = useRouter();
  const [title, setTitle] = useState(post?.title ?? "");
  const [slug, setSlug] = useState(post?.slug ?? "");
  const [body, setBody] = useState(post?.body ?? "");
  const [published, setPublished] = useState(post?.published ?? false);
  const [selected, setSelected] = useState<Selected[]>(
    post?.photos.map((p) => ({ photo_id: p.photo.id, caption: p.caption ?? "" })) ?? [],
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const byId = new Map(photos.map((p) => [p.id, p]));
  const order = new Map(selected.map((s, i) => [s.photo_id, i + 1]));

  function toggle(id: string) {
    setSelected((prev) =>
      prev.some((s) => s.photo_id === id)
        ? prev.filter((s) => s.photo_id !== id)
        : [...prev, { photo_id: id, caption: "" }],
    );
  }

  function move(index: number, by: -1 | 1) {
    setSelected((prev) => {
      const next = [...prev];
      const target = index + by;
      if (target < 0 || target >= next.length) return prev;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  function setCaption(index: number, caption: string) {
    setSelected((prev) => prev.map((s, i) => (i === index ? { ...s, caption } : s)));
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);

    const payload = {
      title,
      body,
      published,
      photos: selected.map((s) => ({ photo_id: s.photo_id, caption: s.caption || null })),
      // Empty slug on a new post: the API makes one from the title.
      ...(slug.trim() ? { slug: slug.trim() } : {}),
    };

    const res = await fetch(post ? `/api/posts/${post.id}` : "/api/posts", {
      method: post ? "PATCH" : "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
    }).catch(() => null);

    if (!res) {
      setError("Network error");
      setBusy(false);
      return;
    }
    const json = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(errorText(res.status, json));
      setBusy(false);
      return;
    }
    router.push(`/posts/${json.slug}`);
    router.refresh();
  }

  async function onDelete() {
    if (!post || !confirm("Delete this post? The photos stay.")) return;
    setBusy(true);
    const res = await fetch(`/api/posts/${post.id}`, { method: "DELETE" }).catch(() => null);
    if (res && (res.ok || res.status === 404)) {
      router.push("/posts");
      router.refresh();
    } else {
      setError(`Delete failed${res ? ` (${res.status})` : ""}`);
      setBusy(false);
    }
  }

  return (
    <form className="editor" onSubmit={onSubmit}>
      <label>
        Title
        <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} required maxLength={200} />
      </label>

      <label>
        URL name
        <input
          type="text"
          value={slug}
          onChange={(e) => setSlug(e.target.value.toLowerCase())}
          placeholder={post ? undefined : "made from the title if left empty, e.g. seongsu-walk"}
          pattern="[a-z0-9]+(-[a-z0-9]+)*"
          title="Lowercase letters, numbers and dashes"
          maxLength={80}
        />
      </label>

      <label>
        Text
        <textarea value={body} onChange={(e) => setBody(e.target.value)} placeholder="A blank line starts a new paragraph." />
      </label>

      <div>
        <div className="section-label" style={{ marginTop: 0 }}>
          Photos in this post ({selected.length})
        </div>
        {selected.length === 0 ? (
          <p className="muted">Choose photos below. They appear in this order.</p>
        ) : (
          <ol className="selected-list">
            {selected.map((s, i) => (
              <li key={s.photo_id}>
                {/* eslint-disable-next-line @next/next/no-img-element -- the API already serves sized JPEGs */}
                <img src={photoSrc(s.photo_id, "thumb")} alt="" />
                <input
                  type="text"
                  value={s.caption}
                  onChange={(e) => setCaption(i, e.target.value)}
                  placeholder={byId.get(s.photo_id)?.original_filename ?? "Caption"}
                  maxLength={500}
                  aria-label={`Caption for photo ${i + 1}`}
                />
                <div className="controls">
                  <button type="button" onClick={() => move(i, -1)} disabled={i === 0} aria-label="Move up">
                    ↑
                  </button>
                  <button type="button" onClick={() => move(i, 1)} disabled={i === selected.length - 1} aria-label="Move down">
                    ↓
                  </button>
                  <button type="button" onClick={() => toggle(s.photo_id)} aria-label="Remove">
                    ✕
                  </button>
                </div>
              </li>
            ))}
          </ol>
        )}
      </div>

      <div>
        <div className="section-label" style={{ marginTop: 0 }}>
          All photos
        </div>
        {photos.length === 0 ? (
          <p className="muted">No photos uploaded yet.</p>
        ) : (
          <div className="picker">
            {photos.map((p) => (
              <button
                key={p.id}
                type="button"
                aria-pressed={order.has(p.id)}
                onClick={() => toggle(p.id)}
                title={p.original_filename}
              >
                {/* eslint-disable-next-line @next/next/no-img-element -- the API already serves sized JPEGs */}
                <img src={photoSrc(p.id, "thumb")} alt={p.original_filename} loading="lazy" />
                {order.has(p.id) && <span className="order">{order.get(p.id)}</span>}
              </button>
            ))}
          </div>
        )}
      </div>

      <label className="check">
        <input type="checkbox" checked={published} onChange={(e) => setPublished(e.target.checked)} />
        Published
      </label>

      <div className="editor-actions">
        <button type="submit" disabled={busy}>
          {busy ? "Saving…" : post ? "Save" : "Create post"}
        </button>
        {post && (
          <button type="button" className="link" onClick={onDelete} disabled={busy}>
            Delete post
          </button>
        )}
        {error && <span className="status-error">{error}</span>}
      </div>
    </form>
  );
}

/** The API sends { detail: "..." }, or for 422 a list of field errors. */
function errorText(status: number, json: { detail?: unknown }): string {
  if (typeof json.detail === "string") return json.detail;
  if (Array.isArray(json.detail)) {
    return json.detail
      .map((d: { loc?: unknown[]; msg?: string }) => `${(d.loc ?? []).slice(1).join(".")}: ${d.msg}`)
      .join("; ");
  }
  return `Save failed (${status})`;
}
