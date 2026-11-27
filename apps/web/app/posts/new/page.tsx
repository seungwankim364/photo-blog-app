import PostEditor from "@/components/PostEditor";
import { listPhotos } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function NewPost() {
  const photos = await listPhotos();
  return (
    <main>
      <h1 style={{ fontSize: "1.25rem" }}>New post</h1>
      <PostEditor photos={photos} />
    </main>
  );
}
