# Google Cloud Deployment Guide

This guide explains how to host the Blueprint Reader application on Google Cloud Platform.

## Architecture Overview

- **Backend**: Google Cloud Run (containerized Python API)
- **Frontend**: Firebase Hosting (static React app)
- **Database**: Supabase (already hosted)
- **Storage**: Supabase Storage (already hosted)

## Prerequisites

1. Google Cloud account with billing enabled
2. Google Cloud SDK installed (`gcloud`)
3. Firebase CLI installed (`firebase-tools`)
4. Docker installed locally

## Step 1: Set up Google Cloud Project

```bash
# Create a new Google Cloud project
gcloud projects create blueprint-reader-prod

# Set as active project
gcloud config set project blueprint-reader-prod

# Enable required APIs
gcloud services enable \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com
```

## Step 2: Deploy Backend to Cloud Run

### 2.1 Build and Push Docker Image

```bash
cd backend

# Configure Docker authentication for Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build the image
docker build -t us-central1-docker.pkg.dev/blueprint-reader-prod/blueprint-reader/backend:latest .

# Push to Google Artifact Registry
docker push us-central1-docker.pkg.dev/blueprint-reader-prod/blueprint-reader/backend:latest
```

### 2.2 Create Artifact Registry Repository

```bash
# Create repository
gcloud artifacts repositories create blueprint-reader \
  --repository-format=docker \
  --location=us-central1 \
  --description="Blueprint Reader Docker images"
```

### 2.3 Deploy to Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy blueprint-reader-backend \
  --image=us-central1-docker.pkg.dev/blueprint-reader-prod/blueprint-reader/backend:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=1 \
  --timeout=3600 \
  --set-env-vars=SUPABASE_URL=your_supabase_url \
  --set-env-vars=SUPABASE_SERVICE_ROLE_KEY=your_service_role_key \
  --set-env-vars=GOOGLE_API_KEY=your_google_api_key \
  --set-env-vars=GEMINI_MODEL=gemini-1.5-flash
```

The backend container is built to read Cloud Run's `$PORT` at runtime, so no extra port flag is needed.

### 2.4 Get Backend URL

```bash
# Get the service URL
gcloud run services describe blueprint-reader-backend \
  --platform=managed \
  --region=us-central1 \
  --format='value(status.url)'
```

Save this URL - you'll need it for the frontend configuration.

## Step 3: Deploy Frontend to Firebase Hosting

### 3.1 Set up Firebase Project

```bash
# Install Firebase CLI if not already installed
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase in frontend directory
cd frontend
firebase init

# Select options:
# - Hosting: Configure files for Firebase Hosting
# - Use existing project: blueprint-reader-prod
# - Public directory: dist
# - Configure as single-page app: Yes
# - Set up automatic builds: No (we'll build manually)
```

### 3.2 Build Frontend

```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build
```

### 3.3 Configure Firebase Hosting

Create or update `firebase.json` in the frontend directory:

```json
{
  "hosting": {
    "public": "dist",
    "ignore": [
      "firebase.json",
      "**/.*",
      "**/node_modules/**"
    ],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      }
    ]
  }
}
```

### 3.4 Deploy to Firebase

```bash
cd frontend

# Deploy to Firebase
firebase deploy
```

Your frontend will be available at: `https://blueprint-reader-prod.web.app`

## Step 4: Update Frontend Environment Variables

Create `frontend/.env.production` (this file is gitignored):

```env
VITE_API_URL=https://blueprint-reader-backend-xxxxx.run.app/api/v1
VITE_API_BASE_URL=https://blueprint-reader-backend-xxxxx.run.app/api/v1
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

**Required Variables:**
- `VITE_API_URL`: Your Cloud Run backend API base URL (from Step 2.4)
- `VITE_API_BASE_URL`: Keep this aligned with `VITE_API_URL` for pages that read the newer env name
- `VITE_SUPABASE_URL`: Your Supabase project URL
- `VITE_SUPABASE_ANON_KEY`: Your Supabase anonymous/public key
- `VITE_CLERK_PUBLISHABLE_KEY`: Your Clerk publishable key

Rebuild and redeploy frontend after updating:

```bash
cd frontend
npm run build
firebase deploy
```

## Step 5: Set up Cloud Build (Optional - CI/CD)

Create `cloudbuild.yaml` for automated builds:

```yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/blueprint-reader/backend:$COMMIT_SHA', '-t', 'us-central1-docker.pkg.dev/$PROJECT_ID/blueprint-reader/backend:latest', '.']
    dir: 'backend'
  
  # Push to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/blueprint-reader/backend:$COMMIT_SHA']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'us-central1-docker.pkg.dev/$PROJECT_ID/blueprint-reader/backend:latest']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'blueprint-reader-backend'
      - '--image=us-central1-docker.pkg.dev/$PROJECT_ID/blueprint-reader/backend:$COMMIT_SHA'
      - '--platform=managed'
      - '--region=us-central1'
      - '--allow-unauthenticated'
      - '--memory=2Gi'
      - '--cpu=1'
      - '--timeout=3600'
```

## Step 6: Set up Monitoring and Logging

### Cloud Run Logs

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision" \
  --resource=blueprint-reader-backend \
  --limit=50
```

### Firebase Analytics

Firebase provides built-in analytics for your frontend hosting.

## Cost Estimates

- **Cloud Run**: $0.40 per million requests + $0.000025/GB-second + $0.10/GB network egress
- **Firebase Hosting**: Free tier includes 10GB/month, then $0.026/GB
- **Artifact Registry**: $0.10/GB/month storage

Estimated monthly cost for low traffic: ~$10-20
Estimated monthly cost for moderate traffic: ~$50-100

## Troubleshooting

### Backend Issues

```bash
# Check Cloud Run service status
gcloud run services describe blueprint-reader-backend --region=us-central1

# View recent logs
gcloud run logs read blueprint-reader-backend --region=us-central1 --limit=100
```

### Frontend Issues

```bash
# Check Firebase deployment status
firebase hosting:status

# View Firebase logs
firebase functions:log
```

### Common Issues

1. **Tesseract OCR**: Cloud Run includes Tesseract in the Dockerfile, ensure it's working
2. **Memory Limits**: If processing large files, increase Cloud Run memory to 4Gi or 8Gi
3. **Timeout**: Large blueprint processing may need longer timeouts (up to 3600s)
4. **CORS**: Ensure backend allows requests from Firebase domain

## Security Considerations

1. **Environment Variables**: Never commit `.env` files. Use Google Secret Manager for sensitive data
2. **API Keys**: Restrict Google API keys to specific domains
3. **Supabase**: Use service role key only on backend, anon key on frontend
4. **Clerk**: Verify webhook signatures in production

## Migration from Railway

If migrating from Railway:

1. Export Railway environment variables
2. Update Supabase webhook URLs to new Cloud Run endpoint
3. Update Clerk dashboard with new frontend URL
4. Test all integrations before switching DNS
