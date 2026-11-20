import Link from "next/link";
import { notFound } from "next/navigation";

import { getPhoto, photoSrc } from "@/lib/api";
import {
  formatAperture,
  formatCamera,
  formatFocal,
  formatShutter,
  formatSize,
  formatTakenAt,
} from "@/lib/format";

import DeleteButton from "./DeleteButton";

export const dynamic = "force-dynamic";

export default async function PhotoPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const photo = await getPhoto(id);
  if (!photo) notFound();

  // Only rows with a value are shown, so a photo without EXIF gets a short card.
  const rows: [string, string | null][] = [
    ["Camera", formatCamera(photo.camera_make, photo.camera_model)],
    ["Lens", photo.lens_model],
    ["Focal length", formatFocal(photo.focal_length_mm, photo.focal_35mm)],
    ["Aperture", formatAperture(photo.aperture)],
    ["Shutter", formatShutter(photo.shutter)],
    ["ISO", photo.iso == null ? null : String(photo.iso)],
    ["Taken", formatTakenAt(photo.taken_at)],
  ];
  const shown = rows.filter((row): row is [string, string] => row[1] != null);

  return (
    <main>
      <p>
        <Link href="/" className="muted">
          ← All photos
        </Link>
      </p>
      <div className="photo-page">
        {/* eslint-disable-next-line @next/next/no-img-element -- the API already serves sized JPEGs */}
        <img
          src={photoSrc(photo.id, "display")}
          alt={formatCamera(photo.camera_make, photo.camera_model) ?? photo.original_filename}
          width={photo.width ?? undefined}
          height={photo.height ?? undefined}
        />
        <aside className="exif-card">
          <h2>Details</h2>
          {shown.length > 0 ? (
            <dl>
              {shown.map(([label, value]) => (
                <div key={label} style={{ display: "contents" }}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="muted">No EXIF data in this photo.</p>
          )}
          <p className="muted" style={{ fontSize: "0.8rem", marginTop: 16 }}>
            {photo.width && photo.height ? `${photo.width} × ${photo.height}, ` : ""}
            {formatSize(photo.size_bytes)}
          </p>
          <div className="exif-actions">
            <a href={photoSrc(photo.id, "original")} target="_blank" rel="noreferrer">
              Original
            </a>
            <DeleteButton id={photo.id} />
          </div>
        </aside>
      </div>
    </main>
  );
}
