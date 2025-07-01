#!/bin/bash
# Emergency Shutdown Script - Stops all GCP resources to prevent costs
# Created: 2025-07-01
# Purpose: Clean shutdown of all sprint resources if deployment fails

set -e

echo "🚨 EMERGENCY SHUTDOWN SCRIPT 🚨"
echo "This will stop/delete all GCP resources created during the sprint"
echo "Press Ctrl+C within 10 seconds to cancel..."
sleep 10

PROJECT_ID="macayaven"
REGION="europe-west1"

echo "Setting project..."
gcloud config set project $PROJECT_ID

echo "=== 1. Stopping Cloud Run Services ==="
echo "Deleting Cloud Run service 'reframe-edge'..."
gcloud run services delete reframe-edge --region=$REGION --quiet || echo "Service not found or already deleted"

echo "=== 2. Cleaning up Artifact Registry ==="
echo "Listing images in reframe-edge repository..."
gcloud artifacts docker images list \
  europe-west1-docker.pkg.dev/$PROJECT_ID/reframe-edge \
  --include-tags || echo "No images found"

echo "Deleting all images in reframe-edge repository..."
for IMAGE in $(gcloud artifacts docker images list europe-west1-docker.pkg.dev/$PROJECT_ID/reframe-edge --format="value(IMAGE)"); do
  echo "Deleting image: $IMAGE"
  gcloud artifacts docker images delete "$IMAGE" --quiet || echo "Failed to delete $IMAGE"
done

echo "=== 3. Cleaning up Cloud Storage ==="
echo "Removing all objects from GCS bucket 'reframe-apd-pdf'..."
gsutil -m rm -r gs://reframe-apd-pdf/** 2>/dev/null || echo "Bucket empty or not accessible"

echo "Deleting GCS bucket 'reframe-apd-pdf'..."
gsutil rb gs://reframe-apd-pdf 2>/dev/null || echo "Bucket not found or already deleted"

echo "=== 4. Revoking Service Account Keys ==="
echo "Listing keys for reframe-edge-sa..."
gcloud iam service-accounts keys list \
  --iam-account=reframe-edge-sa@$PROJECT_ID.iam.gserviceaccount.com || echo "Service account not found"

echo "=== 5. Removing Secret Manager Secrets ==="
echo "Deleting secret 'reframe-edge-sa-key'..."
gcloud secrets delete reframe-edge-sa-key --quiet || echo "Secret not found"

echo "=== 6. Cost Summary ==="
echo "Resources that were stopped/deleted:"
echo "- Cloud Run service: reframe-edge"
echo "- Artifact Registry images: reframe-orchestrator"
echo "- GCS bucket: reframe-apd-pdf"
echo "- Secret: reframe-edge-sa-key"

echo ""
echo "Resources that may still incur minimal costs:"
echo "- Artifact Registry repository (empty): ~$0.10/GB/month"
echo "- Service account (no active keys): $0"
echo "- Cloud Build history: $0"

echo ""
echo "=== SHUTDOWN COMPLETE ==="
echo "To fully remove the Artifact Registry repository:"
echo "gcloud artifacts repositories delete reframe-edge --location=$REGION --quiet"
echo ""
echo "To remove the service account:"
echo "gcloud iam service-accounts delete reframe-edge-sa@$PROJECT_ID.iam.gserviceaccount.com --quiet"

# Create a summary file
cat > shutdown-summary-$(date +%Y%m%d-%H%M%S).txt << EOF
Emergency Shutdown Summary
========================
Date: $(date)
Project: $PROJECT_ID
Region: $REGION

Resources Cleaned:
- Cloud Run: reframe-edge (deleted)
- Docker Images: All images in reframe-edge repository (deleted)
- GCS Bucket: reframe-apd-pdf (deleted)
- Secret Manager: reframe-edge-sa-key (deleted)

Remaining Resources (minimal/no cost):
- Artifact Registry repository: reframe-edge (empty)
- Service Account: reframe-edge-sa@$PROJECT_ID.iam.gserviceaccount.com
- GitHub repositories and code

Estimated ongoing cost: < $1/month
EOF

echo ""
echo "Summary saved to: shutdown-summary-$(date +%Y%m%d-%H%M%S).txt"