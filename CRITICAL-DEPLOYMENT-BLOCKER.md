# 🚨🚨 CRITICAL DEPLOYMENT BLOCKER - TEAM BETA ACTION REQUIRED NOW! 🚨🚨

## STATUS: PRODUCTION IS DOWN!
The Cloud Run deployment at https://reframe-edge-21239963940.europe-west1.run.app is **COMPLETELY BROKEN** and serving static files instead of the API.

## ROOT CAUSE
- Docker image is ARM64 (built on Mac) but Cloud Run requires AMD64
- The deployment is live but non-functional

## IMMEDIATE ACTIONS FOR TEAM BETA

### Option 1: Use GitHub Actions (FASTEST)
Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Cloud Run
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Auth GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
      
      - name: Configure Docker
        run: gcloud auth configure-docker europe-west1-docker.pkg.dev
      
      - name: Build and Push
        run: |
          docker build -t europe-west1-docker.pkg.dev/macayaven/reframe-edge/reframe-orchestrator:latest .
          docker push europe-west1-docker.pkg.dev/macayaven/reframe-edge/reframe-orchestrator:latest
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy reframe-edge \
            --image europe-west1-docker.pkg.dev/macayaven/reframe-edge/reframe-orchestrator:latest \
            --region europe-west1 \
            --platform managed \
            --allow-unauthenticated \
            --port 8080
```

### Option 2: Use Cloud Build (REQUIRES API ENABLE)
1. Enable Cloud Build API: https://console.developers.google.com/apis/api/cloudbuild.googleapis.com/overview?project=macayaven
2. Run: `gcloud builds submit --config=cloudbuild.yaml --project=macayaven`

### Option 3: Build on Linux/Cloud Shell
```bash
# On a Linux machine or Google Cloud Shell:
docker build -t reframe-orchestrator:amd64 .
docker tag reframe-orchestrator:amd64 europe-west1-docker.pkg.dev/macayaven/reframe-edge/reframe-orchestrator:latest
docker push europe-west1-docker.pkg.dev/macayaven/reframe-edge/reframe-orchestrator:latest
gcloud run deploy reframe-edge --image europe-west1-docker.pkg.dev/macayaven/reframe-edge/reframe-orchestrator:latest --region europe-west1
```

## VERIFICATION
After deployment, this MUST return `{"status":"ok"}`:
```bash
curl https://reframe-edge-21239963940.europe-west1.run.app/health
```

## TIMELINE
- **NOW**: Production is broken
- **ASAP**: Deploy AMD64 image
- **Sprint ends**: In less than 2 hours

## THIS IS BLOCKING EVERYTHING!
- Integration testing cannot proceed
- Sprint deliverables are incomplete
- The orchestrator MVP is unusable

**TEAM BETA: FIX THIS NOW! DO NOT WAIT!**

---
*Issue opened: NOW*
*Expected resolution: Within 30 minutes*
*Severity: CRITICAL BLOCKER*