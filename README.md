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

### Project layout

- `backend/blueprint_logic.py` — extraction pipeline (PDF, image, DXF)
- `backend/boq_engine.py` — Maharashtra PWD DSR BOQ (wire into worker next)
- `backend/supabase_worker.py` — async job processor
- `frontend/` — Next.js app (Clerk auth, Supabase jobs)
