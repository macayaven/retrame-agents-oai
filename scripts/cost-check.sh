#!/bin/bash
# Cost Check Script - Shows current GCP resources and estimated costs
# Run this before shutdown to see what's running

PROJECT_ID="macayaven"
REGION="europe-west1"

echo "=== GCP Resource Cost Check ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Date: $(date)"
echo ""

echo "1. Cloud Run Services:"
gcloud run services list --region=$REGION --format="table(SERVICE,LAST_DEPLOYED_BY,LAST_DEPLOYED_AT)" 2>/dev/null || echo "None found"
echo "   Estimated cost: $0.00 (only charged per request)"
echo ""

echo "2. Artifact Registry:"
gcloud artifacts repositories list --location=$REGION --format="table(REPOSITORY,FORMAT,SIZE_BYTES)" 2>/dev/null || echo "None found"
echo "   Estimated cost: ~$0.10/GB/month for storage"
echo ""

echo "3. Cloud Storage Buckets:"
gsutil ls -L -b gs://reframe-apd-pdf 2>/dev/null | grep "Storage class\|Total size" || echo "Bucket not found"
echo "   Estimated cost: $0.02/GB/month (Standard storage)"
echo ""

echo "4. Active Service Account Keys:"
gcloud iam service-accounts keys list \
  --iam-account=reframe-edge-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --format="table(KEY_ID,CREATED_AT,EXPIRES_AT)" 2>/dev/null || echo "None found"
echo "   Cost: $0"
echo ""

echo "5. Secret Manager:"
gcloud secrets list --format="table(NAME,CREATED)" 2>/dev/null | grep reframe || echo "None found"
echo "   Cost: $0.06/secret/month + $0.03/10k access operations"
echo ""

echo "=== ESTIMATED MONTHLY COSTS ==="
echo "Cloud Run: $0 (no traffic = no cost)"
echo "Artifact Registry: < $1 (depends on image sizes)"
echo "Cloud Storage: < $1 (minimal PDFs)"
echo "Secrets: < $1"
echo "TOTAL: < $3/month if left running"
echo ""
echo "To shutdown all resources, run:"
echo "./scripts/emergency-shutdown.sh"