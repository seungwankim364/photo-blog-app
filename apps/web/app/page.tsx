import Link from "next/link";

import { listPhotos, photoSrc, type Photo } from "@/lib/api";
import { formatCamera, formatDate } from "@/lib/format";

// Render on every request, so new uploads show up right away.
export const dynamic = "force-dynamic";

export default async function Gallery() {
  let photos: Photo[];
  try {
    photos = await listPhotos();
  } catch {
    return (
      <main>
        <p className="muted">
          Couldn&apos;t load photos. Check the API on the <Link href="/status">status page</Link>.
        </p>
      </main>
    );
  }

  if (photos.length === 0) {
    return (
      <main>
        <p className="muted">
          No photos yet. <Link href="/upload">Upload the first one</Link>.
        </p>
      </main>
    );
  }

  return (
    <main>
      <div className="gallery">
        {photos.map((photo) => {
          const caption = [formatDate(photo.taken_at), formatCamera(photo.camera_make, photo.camera_model)]
            .filter(Boolean)
            .join(", ");
          return (
            <Link key={photo.id} href={`/photos/${photo.id}`} className="tile">
              {/* eslint-disable-next-line @next/next/no-img-element -- the API already serves sized JPEGs */}
              <img src={photoSrc(photo.id, "thumb")} alt={caption || photo.original_filename} loading="lazy" />
              {caption && <div className="tile-caption">{caption}</div>}
            </Link>
          );
        })}
      </div>
    </main>
  );
}
