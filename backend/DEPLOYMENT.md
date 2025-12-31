# Deployment Guide for Google Cloud Run

This guide explains how to deploy the TalkWith application to Google Cloud Run.

## Prerequisites

1. Google Cloud Project with billing enabled
2. Google Cloud SDK (`gcloud`) installed and configured
   - Install: `brew install --cask google-cloud-sdk` (macOS)
   - Or download from: https://cloud.google.com/sdk/docs/install
3. Docker installed (for local testing)
4. Environment variables set up (see MongoDB Setup section below)

## Setup

### 1. Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 2. Set Environment Variables

Set substitution variables for Cloud Build:

```bash
# Backend environment variables
gcloud builds submit --config=cloudbuild-backend.yaml \
  --substitutions=_MONGO_URI="your-mongodb-uri",_DATABASE_NAME="talkwith",_GEMINI_API_KEY="your-gemini-key",_ELEVENLABS_API_KEY="your-elevenlabs-key"

# Frontend environment variable (set after backend is deployed)
# Get your backend URL from Cloud Run console
gcloud builds submit --config=cloudbuild-frontend.yaml \
  --substitutions=_REACT_APP_API_URL="https://talkwith-backend-xxxxx.run.app"
```

Or set them as project-level substitutions:

```bash
gcloud config set builds/substitutions/_MONGO_URI "your-mongodb-uri"
gcloud config set builds/substitutions/_DATABASE_NAME "talkwith"
gcloud config set builds/substitutions/_GEMINI_API_KEY "your-gemini-key"
gcloud config set builds/substitutions/_ELEVENLABS_API_KEY "your-elevenlabs-key"
gcloud config set builds/substitutions/_REACT_APP_API_URL "https://talkwith-backend-xxxxx.run.app"
```

## Deployment Steps

### Step 1: Deploy Backend

1. Navigate to the project root:
```bash
cd /path/to/talkwith
```

2. Build and deploy the backend:
```bash
gcloud builds submit --config=cloudbuild-backend.yaml
```

Or deploy manually:
```bash
# Build the image
docker build -t gcr.io/YOUR_PROJECT_ID/talkwith-backend .

# Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/talkwith-backend

# Deploy to Cloud Run
gcloud run deploy talkwith-backend \
  --image gcr.io/YOUR_PROJECT_ID/talkwith-backend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars MONGO_URI="your-mongodb-uri",DATABASE_NAME="talkwith",GEMINI_API_KEY="your-key",ELEVENLABS_API_KEY="your-key"
```

3. Note the backend URL from the output (e.g., `https://talkwith-backend-xxxxx.run.app`)

### Step 2: Deploy Frontend

1. Update the frontend API URL in `cloudbuild-frontend.yaml` or set it as a substitution variable

2. Build and deploy the frontend:
```bash
gcloud builds submit --config=cloudbuild-frontend.yaml
```

Or deploy manually:
```bash
# Build the image
cd frontend
docker build -t gcr.io/YOUR_PROJECT_ID/talkwith-frontend .

# Push to Container Registry
docker push gcr.io/YOUR_PROJECT_ID/talkwith-frontend

# Deploy to Cloud Run
gcloud run deploy talkwith-frontend \
  --image gcr.io/YOUR_PROJECT_ID/talkwith-frontend \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --max-instances 10 \
  --set-env-vars REACT_APP_API_URL="https://talkwith-backend-xxxxx.run.app"
```

## MongoDB Setup

For production, you'll need a MongoDB instance. Options:

1. **MongoDB Atlas** (Recommended):
   - Create a free cluster at https://www.mongodb.com/cloud/atlas
   - Get the connection string
   - Add your Cloud Run IP to the whitelist (or use 0.0.0.0/0 for testing)

2. **Cloud SQL for MongoDB** (if available in your region)

3. **Self-hosted MongoDB** on Compute Engine

Update the `MONGO_URI` environment variable with your MongoDB connection string.

## Environment Variables

### Backend (Cloud Run)
- `MONGO_URI`: MongoDB connection string
- `DATABASE_NAME`: Database name (default: "talkwith")
- `GEMINI_API_KEY`: Google Gemini API key
- `ELEVENLABS_API_KEY`: ElevenLabs API key
- `PORT`: Automatically set by Cloud Run (8080)
- `FLASK_ENV`: Set to "production" for production mode

### Frontend (Cloud Run)
- `REACT_APP_API_URL`: Backend API URL (e.g., "https://talkwith-backend-xxxxx.run.app")

## Updating Deployments

To update either service:

```bash
# Backend
gcloud builds submit --config=cloudbuild-backend.yaml

# Frontend
gcloud builds submit --config=cloudbuild-frontend.yaml
```

Or use `gcloud run deploy` directly with the new image.

## Monitoring

- View logs: `gcloud run services logs read talkwith-backend --region us-central1`
- View metrics: Google Cloud Console > Cloud Run > talkwith-backend
- Set up alerts in Cloud Monitoring

## Troubleshooting

1. **Backend timeout**: Increase `--timeout` value (max 300s for Cloud Run)
2. **Memory issues**: Increase `--memory` allocation
3. **CORS errors**: Ensure frontend URL is allowed in backend CORS settings
4. **API connection**: Verify `REACT_APP_API_URL` matches your backend URL

## Cost Optimization

- Use Cloud Run's automatic scaling (scales to zero when not in use)
- Adjust `--max-instances` based on expected traffic
- Use appropriate memory/CPU settings for your workload
- Consider using Cloud Run's concurrency settings

## Security Notes

- Store sensitive keys in Secret Manager instead of environment variables
- Use IAM for authentication instead of `--allow-unauthenticated` in production
- Enable Cloud Armor for DDoS protection
- Use VPC connector for private MongoDB connections

