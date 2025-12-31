#!/bin/bash
# Frontend deployment script for Google Cloud Run
# Project ID: talkwith-482914

set -e

PROJECT_ID="talkwith-482914"
REGION="us-central1"
BACKEND_URL=${1}

echo "Deploying TalkWith Frontend to Google Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

if [ -z "$BACKEND_URL" ]; then
    echo "Attempting to get backend URL from existing service..."
    BACKEND_URL=$(gcloud run services describe talkwith-backend --region=$REGION --format='value(status.url)' --project=$PROJECT_ID 2>/dev/null || echo "")
    
    if [ -z "$BACKEND_URL" ]; then
        echo ""
        echo "⚠️  Backend URL not found. Please provide it as an argument:"
        echo "   Usage: ./deploy-frontend-now.sh https://your-backend-url.run.app"
        echo ""
        read -p "Enter backend URL manually (or press Enter to skip): " MANUAL_URL
        if [ -n "$MANUAL_URL" ]; then
            BACKEND_URL="$MANUAL_URL"
        else
            echo "Error: Backend URL is required for frontend deployment"
            exit 1
        fi
    else
        echo "✅ Found backend URL: $BACKEND_URL"
    fi
else
    echo "Using provided backend URL: $BACKEND_URL"
fi

echo ""
echo "Building and deploying frontend..."
echo "This may take a few minutes..."
echo ""

# Deploy frontend using Cloud Build
gcloud builds submit --config=cloudbuild-frontend.yaml \
    --substitutions=_REACT_APP_API_URL="$BACKEND_URL" \
    --project=$PROJECT_ID

# Get frontend URL
echo ""
echo "Getting frontend URL..."
FRONTEND_URL=$(gcloud run services describe talkwith-frontend --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)
echo ""
echo "✅ Frontend deployed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL:  $BACKEND_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next step: Update backend CORS to allow frontend URL"
echo "Run this command:"
echo ""
echo "gcloud run services update talkwith-backend \\"
echo "  --region $REGION \\"
echo "  --set-env-vars CORS_ORIGINS=$FRONTEND_URL \\"
echo "  --project $PROJECT_ID"
echo ""

