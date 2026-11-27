import { notFound } from "next/navigation";

import PostEditor from "@/components/PostEditor";
import { getPost, listPhotos } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function EditPost({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const [post, photos] = await Promise.all([getPost(slug, { drafts: true }), listPhotos()]);
  if (!post) notFound();

  return (
    <main>
      <h1 style={{ fontSize: "1.25rem" }}>Edit post</h1>
      <PostEditor photos={photos} post={post} />
    </main>
  );
}
