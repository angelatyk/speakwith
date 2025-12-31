#!/bin/bash
# Backend deployment script for Google Cloud Run
# Project ID: talkwith-482914

set -e

PROJECT_ID="talkwith-482914"
REGION="us-central1"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    # Export variables from .env, handling quoted and unquoted values
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

echo "Deploying TalkWith Backend to Google Cloud Run"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check for required environment variables
if [ -z "$MONGO_URI" ]; then
    echo "⚠️  MONGO_URI not set. Please set it:"
    echo "   export MONGO_URI='your-mongodb-connection-string'"
    echo ""
    read -p "Enter MONGO_URI now (or press Enter to skip): " MONGO_URI_INPUT
    if [ -n "$MONGO_URI_INPUT" ]; then
        export MONGO_URI="$MONGO_URI_INPUT"
    else
        echo "Error: MONGO_URI is required"
        exit 1
    fi
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  GEMINI_API_KEY not set. Please set it:"
    echo "   export GEMINI_API_KEY='your-gemini-api-key'"
    echo ""
    read -p "Enter GEMINI_API_KEY now (or press Enter to skip): " GEMINI_KEY_INPUT
    if [ -n "$GEMINI_KEY_INPUT" ]; then
        export GEMINI_API_KEY="$GEMINI_KEY_INPUT"
    else
        echo "Error: GEMINI_API_KEY is required"
        exit 1
    fi
fi

if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "⚠️  ELEVENLABS_API_KEY not set. Please set it:"
    echo "   export ELEVENLABS_API_KEY='your-elevenlabs-api-key'"
    echo ""
    read -p "Enter ELEVENLABS_API_KEY now (or press Enter to skip): " ELEVENLABS_KEY_INPUT
    if [ -n "$ELEVENLABS_KEY_INPUT" ]; then
        export ELEVENLABS_API_KEY="$ELEVENLABS_KEY_INPUT"
    else
        echo "Error: ELEVENLABS_API_KEY is required"
        exit 1
    fi
fi

DATABASE_NAME=${DATABASE_NAME:-talkwith}

echo ""
echo "Configuration:"
echo "  MONGO_URI: ${MONGO_URI:0:20}..."
echo "  DATABASE_NAME: $DATABASE_NAME"
echo "  GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."
echo "  ELEVENLABS_API_KEY: ${ELEVENLABS_API_KEY:0:10}..."
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo ""
echo "Building and deploying backend..."
echo "This may take a few minutes..."
echo ""

# Deploy backend using Cloud Build
gcloud builds submit --config=cloudbuild-backend.yaml \
    --substitutions=_MONGO_URI="$MONGO_URI",_DATABASE_NAME="$DATABASE_NAME",_GEMINI_API_KEY="$GEMINI_API_KEY",_ELEVENLABS_API_KEY="$ELEVENLABS_API_KEY",_CORS_ORIGINS="" \
    --project=$PROJECT_ID

# Get backend URL
echo ""
echo "Getting backend URL..."
BACKEND_URL=$(gcloud run services describe talkwith-backend --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)
echo ""
echo "✅ Backend deployed successfully!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Backend URL: $BACKEND_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "1. Test the backend: curl $BACKEND_URL/health"
echo "2. Deploy the frontend with this backend URL:"
echo "   ./deploy-frontend-now.sh $BACKEND_URL"
echo ""

