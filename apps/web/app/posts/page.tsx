import Link from "next/link";

import { listPosts, photoSrc, type PostSummary } from "@/lib/api";
import { formatDate } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function Posts() {
  let posts: PostSummary[];
  try {
    posts = await listPosts({ drafts: true });
  } catch {
    return (
      <main>
        <p className="muted">
          Couldn&apos;t load posts. Check the API on the <Link href="/status">status page</Link>.
        </p>
      </main>
    );
  }

  const published = posts.filter((p) => p.published);
  // Shown here until login exists, so drafts can be found and finished.
  const drafts = posts.filter((p) => !p.published);

  return (
    <main>
      <div className="page-head">
        <h1>Posts</h1>
        <Link href="/posts/new" className="button">
          New post
        </Link>
      </div>

      {published.length === 0 ? (
        <p className="muted">Nothing published yet.</p>
      ) : (
        <PostList posts={published} />
      )}

      {drafts.length > 0 && (
        <>
          <h2 className="section-label">Drafts</h2>
          <PostList posts={drafts} />
        </>
      )}
    </main>
  );
}

function PostList({ posts }: { posts: PostSummary[] }) {
  return (
    <div className="post-list">
      {posts.map((post) => (
        <Link key={post.id} href={`/posts/${post.slug}`} className="post-card">
          {post.cover ? (
            // eslint-disable-next-line @next/next/no-img-element -- the API already serves sized JPEGs
            <img src={photoSrc(post.cover.id, "thumb")} alt="" loading="lazy" />
          ) : (
            <div className="no-cover" />
          )}
          <h2>
            {post.title}
            {!post.published && <span className="badge">Draft</span>}
          </h2>
          <div className="meta">
            {[formatDate(post.published_at ?? post.created_at), `${post.photo_count} photos`].join(", ")}
          </div>
        </Link>
      ))}
    </div>
  );
}
