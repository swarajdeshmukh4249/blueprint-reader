# Render deployment

This project can run the backend on Render as a Docker web service.

## Backend setup

1. Connect the GitHub repo to Render.
2. Create a **Web Service** using the repo root `render.yaml`, or point Render at `backend/Dockerfile`.
3. Use these environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `GOOGLE_API_KEY`
   - `GEMINI_MODEL`
   - `MAX_UPLOAD_MB` (optional, defaults to 150)

The backend container already reads Render's `$PORT`, so no extra port config is needed.

## Service settings

- **Runtime**: Docker
- **Plan**: Free
- **Health check path**: `/health`
- **Auto deploy**: On

## Frontend config

Set the frontend API base URL to your Render service URL:

```env
VITE_API_URL=https://your-render-service.onrender.com/api/v1
VITE_API_BASE_URL=https://your-render-service.onrender.com/api/v1
```

## Notes

- Render free web services can sleep when idle.
- If you move the frontend too, deploy it separately after the backend URL is known.
