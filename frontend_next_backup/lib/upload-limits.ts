/** Must match Supabase Storage global file size limit (Dashboard → Storage → Settings). */
export const MAX_UPLOAD_BYTES = 150 * 1024 * 1024; // 150 MB
export const MAX_UPLOAD_LABEL = '150MB';

export function formatMaxUpload(): string {
  return MAX_UPLOAD_LABEL;
}

export function validateUploadSize(file: File): string | null {
  if (file.size > MAX_UPLOAD_BYTES) {
    return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is ${MAX_UPLOAD_LABEL}.`;
  }
  return null;
}
