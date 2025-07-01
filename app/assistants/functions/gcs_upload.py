"""gcs_upload - Upload PDF to Google Cloud Storage."""

from __future__ import annotations

import base64
import os
from datetime import datetime
from typing import Any

from google.cloud import storage
from google.oauth2 import service_account


# GCS Configuration from Team β
GCS_BUCKET_NAME = "reframe-apd-pdf"
GCS_PROJECT_ID = "macayaven"
GCS_SERVICE_ACCOUNT_EMAIL = "reframe-edge-sa@macayaven.iam.gserviceaccount.com"


async def gcs_upload(
    pdf_base64: str,
    filename: str,
    public_url: str | None = None,  # For schema compatibility
) -> dict[str, Any]:
    """Upload PDF to Google Cloud Storage.
    
    Args:
        pdf_base64: Base64 encoded PDF content
        filename: Filename for the uploaded PDF
        public_url: Ignored, included for schema compatibility
        
    Returns:
        Dictionary with:
            - public_url: Public URL of uploaded file
            - success: Whether upload succeeded
            - error: Error message if failed
    """
    try:
        # Check if running offline
        if os.getenv("OFFLINE", "1") == "1":
            # Return mock response in offline mode
            return {
                "public_url": f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{filename}",
                "success": True
            }
        
        # Decode base64 PDF
        pdf_bytes = base64.b64decode(pdf_base64)
        
        # Initialize GCS client
        # In production, credentials would be provided via environment
        # For now, we'll use default credentials
        client = storage.Client(project=GCS_PROJECT_ID)
        bucket = client.bucket(GCS_BUCKET_NAME)
        
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        
        # Create blob and upload
        blob = bucket.blob(unique_filename)
        blob.upload_from_string(pdf_bytes, content_type="application/pdf")
        
        # Make the blob publicly readable
        blob.make_public()
        
        # Return public URL
        public_url = blob.public_url
        
        return {
            "public_url": public_url,
            "success": True
        }
        
    except Exception as e:
        return {
            "public_url": "",
            "success": False,
            "error": str(e)
        }