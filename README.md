# Blueprint Reader

AI-powered blueprint analysis and BOQ generation.

## Quick start (this workspace)

Synced from `~/Desktop/blueprint-reader` (source only; deps installed locally).

### Backend + worker

```bash
cd backend
cp .env.example .env   # or ensure .env has SUPABASE_* and GOOGLE_API_KEY
../venv/bin/python -m uvicorn main:app --reload --port 8000
# separate terminal:
../venv/bin/python supabase_worker.py
```

### Frontend

```bash
cd frontend
cp .env.example .env.local   # Clerk + Supabase public keys
npm run dev
```

Open http://localhost:3000

### System deps

- **Tesseract** — `brew install tesseract` (OCR)
- **Poppler** — `brew install poppler` (PDF → images for OCR)

### Reliability checks

```bash
cd backend && ../venv/bin/python -m unittest tests.test_blueprint_extraction -v
```

Set `GOOGLE_API_KEY` on Railway for scanned PDFs/JPGs when OCR finds no areas.

### Gemini 429 / quota errors

If Railway logs show `429 RESOURCE_EXHAUSTED` for `gemini-2.0-flash`:

1. In Railway variables set `GEMINI_MODEL=gemini-1.5-flash` (or remove `GEMINI_MODEL` to use default).
2. Enable billing in [Google AI Studio](https://aistudio.google.com/) → API keys → your project.
3. Or wait ~1 minute and re-upload (free tier rate limit).

DXF does not use Gemini; PDF/JPG scans depend on Vision when OCR alone is insufficient.

### Upload size (150 MB)

The app allows files up to **150 MB**. In Supabase Dashboard → **Storage** → **Settings**, set **Global file size limit** to at least **150 MB** (default is often 50 MB).

### Project layout

- `backend/blueprint_logic.py` — extraction pipeline (PDF, image, DXF)
- `backend/boq_engine.py` — Maharashtra PWD DSR BOQ (wire into worker next)
- `backend/supabase_worker.py` — async job processor
- `frontend/` — Next.js app (Clerk auth, Supabase jobs)
