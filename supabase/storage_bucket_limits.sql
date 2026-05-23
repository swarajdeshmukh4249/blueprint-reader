-- Run once in Supabase SQL Editor (Dashboard → SQL → New query)
-- Raises per-bucket upload limit above the default 50 MB global cap.
--
-- Also set: Dashboard → Storage → Settings → Global file size limit → 150 MB (or higher)

UPDATE storage.buckets
SET file_size_limit = 157286400  -- 150 MB in bytes
WHERE id = 'blueprints';

-- If the bucket row does not exist yet:
INSERT INTO storage.buckets (id, name, public, file_size_limit)
VALUES ('blueprints', 'blueprints', false, 157286400)
ON CONFLICT (id) DO UPDATE SET file_size_limit = EXCLUDED.file_size_limit;
