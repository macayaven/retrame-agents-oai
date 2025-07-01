# Cloud Run Deployment Fix

The current deployment is serving a directory listing instead of the FastAPI app. Here's how to fix it:

## 1. Rebuild Docker Image
```bash
cd /Users/carlos/workspace/retrame-agents-oai
docker build -t reframe-orchestrator:latest .
```

## 2. Tag for Artifact Registry
```bash
docker tag reframe-orchestrator:latest \
  europe-west1-docker.pkg.dev/macayaven/reframe-edge/reframe-orchestrator:latest
```

## 3. Push Updated Image
```bash
docker push europe-west1-docker.pkg.dev/macayaven/reframe-edge/reframe-orchestrator:latest
```

## 4. Update Cloud Run Service
```bash
gcloud run deploy reframe-edge \
  --image europe-west1-docker.pkg.dev/macayaven/reframe-edge/reframe-orchestrator:latest \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "OPENAI_API_KEY=${OPENAI_API_KEY},GOOGLE_API_KEY=${GOOGLE_API_KEY},LANGFUSE_HOST=${LANGFUSE_HOST},LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY},LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}"
```

## 5. Test Updated Deployment
```bash
# Should return {"status":"ok"}
curl https://reframe-edge-21239963940.europe-west1.run.app/health
```

## What Was Fixed
- Changed from distroless to python:3.12-slim for better compatibility
- Fixed virtual environment handling with uv
- Corrected the Python path in ENTRYPOINT