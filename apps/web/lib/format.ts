// Times are stored in UTC and shown in this timezone.
const DISPLAY_TZ = process.env.DISPLAY_TZ ?? "Asia/Seoul";

export function formatTakenAt(iso: string | null): string | null {
  if (!iso) return null;
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: DISPLAY_TZ,
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(iso));
}

export function formatDate(iso: string | null): string | null {
  if (!iso) return null;
  return new Intl.DateTimeFormat("en-GB", {
    timeZone: DISPLAY_TZ,
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(iso));
}

/** "Apple" + "iPhone 16 Pro Max" -> "iPhone 16 Pro Max", "FUJIFILM" + "X-T5" -> "FUJIFILM X-T5". */
export function formatCamera(make: string | null, model: string | null): string | null {
  if (!model) return make;
  if (!make || model.toLowerCase().startsWith(make.toLowerCase())) return model;
  return make === "Apple" ? model : `${make} ${model}`;
}

/** "40mm (6.76mm)" when the 35mm equivalent differs, otherwise "23mm". */
export function formatFocal(mm: number | null, equiv35: number | null): string | null {
  if (mm == null && equiv35 == null) return null;
  if (equiv35 == null) return `${trim(mm!)}mm`;
  if (mm == null || Math.round(mm) === equiv35) return `${equiv35}mm`;
  return `${equiv35}mm (${trim(mm)}mm)`;
}

export function formatAperture(f: number | null): string | null {
  return f == null ? null : `f/${trim(f)}`;
}

/** API gives "1/695" or "2s". Shown as "1/695s" and "2s". */
export function formatShutter(s: string | null): string | null {
  if (!s) return null;
  return s.endsWith("s") ? s : `${s}s`;
}

export function formatSize(bytes: number): string {
  return bytes >= 1024 * 1024
    ? `${(bytes / 1024 / 1024).toFixed(1)} MB`
    : `${Math.round(bytes / 1024)} KB`;
}

function trim(n: number): string {
  return String(Number(n.toFixed(2)));
}
