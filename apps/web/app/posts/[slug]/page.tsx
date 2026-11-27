import Link from "next/link";
import { notFound } from "next/navigation";

import { getPost, photoSrc } from "@/lib/api";
import { formatDate, formatExifLine } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function PostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  // Drafts open too, so a draft can be previewed before publishing.
  const post = await getPost(slug, { drafts: true });
  if (!post) notFound();

  // A blank line in the text starts a new paragraph. Single line breaks are kept.
  const paragraphs = post.body.split(/\n\s*\n/).filter((p) => p.trim());

  return (
    <main>
      <article className="post">
        <p>
          <Link href="/posts" className="muted">
            ← All posts
          </Link>
        </p>
        <h1>
          {post.title}
          {!post.published && <span className="badge">Draft</span>}
        </h1>
        <div className="meta">
          {formatDate(post.published_at ?? post.created_at)}
          {", "}
          <Link href={`/posts/${post.slug}/edit`}>Edit</Link>
        </div>

        <div className="post-body">
          {paragraphs.map((text, i) => (
            <p key={i}>{text}</p>
          ))}
        </div>

        {post.photos.map(({ photo, caption }) => {
          const exif = formatExifLine(photo);
          return (
            <figure key={photo.id} className="post-photo">
              {/* eslint-disable-next-line @next/next/no-img-element -- the API already serves sized JPEGs */}
              <img
                src={photoSrc(photo.id, "display")}
                alt={caption ?? exif ?? ""}
                width={photo.width ?? undefined}
                height={photo.height ?? undefined}
                loading="lazy"
              />
              <figcaption>
                {caption}
                {exif && (
                  <div className="exif-line">
                    <Link href={`/photos/${photo.id}`}>{exif}</Link>
                  </div>
                )}
              </figcaption>
            </figure>
          );
        })}
      </article>
    </main>
  );
}
