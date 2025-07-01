"""generate_pdf – Build PDF and upload to Google Cloud Storage.

This wrapper re-uses the legacy `build_pdf_bytes` helper so we keep the PDF
layout identical to the ADK implementation.
"""
from __future__ import annotations

from datetime import datetime
import json
import os
from typing import Any

from app.tools.pdf_generator import build_pdf_bytes

try:
    from google.cloud import secretmanager, storage
    from google.oauth2 import service_account
except ImportError:  # pragma: no cover
    storage = None  # type: ignore
    service_account = None  # type: ignore
    secretmanager = None  # type: ignore


BUCKET_NAME = os.environ.get("GCS_BUCKET_NAME", "reframe-apd-pdf")
PROJECT_ID = os.environ.get("GCS_PROJECT_ID", "macayaven")
SECRET_NAME = os.environ.get("GCS_SERVICE_ACCOUNT_SECRET", "reframe-edge-sa-key")


def _get_gcs_client():  # pragma: no cover – GCS client setup
    if storage is None or service_account is None or secretmanager is None:
        raise RuntimeError("google-cloud-storage library not available")

    # Try to get service account from Secret Manager
    try:
        secret_client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
        response = secret_client.access_secret_version(request={"name": secret_path})
        secret_value = response.payload.data.decode("UTF-8")

        # Parse the service account JSON
        sa_info = json.loads(secret_value)
        credentials = service_account.Credentials.from_service_account_info(sa_info)

        return storage.Client(project=PROJECT_ID, credentials=credentials)
    except Exception:
        # Fallback to default credentials (for local development)
        return storage.Client(project=PROJECT_ID)


def generate_pdf_legacy(session_dict: dict[str, Any]) -> dict[str, str]:
    """Create the PDF, upload, and return a signed public URL (legacy interface).

    Parameters
    ----------
    session_dict
        Dict containing at least ``intake_data`` and ``analysis_output``.
    """

    pdf_bytes = build_pdf_bytes(
        intake_data=session_dict.get("intake_data", {}),
        analysis_output=session_dict.get("analysis_output", ""),
    )

    # Upload to Google Cloud Storage (or gracefully fall back to data URL)
    public_url: str
    if storage and PROJECT_ID and BUCKET_NAME:
        try:
            client = _get_gcs_client()
            bucket = client.bucket(BUCKET_NAME)

            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"reports/report-{timestamp}-{os.urandom(4).hex()}.pdf"

            # Upload the PDF
            blob = bucket.blob(filename)
            blob.upload_from_string(pdf_bytes, content_type="application/pdf")

            # Generate a signed URL valid for 7 days
            from datetime import timedelta
            expiration = timedelta(days=7)
            public_url = blob.generate_signed_url(expiration=expiration, version="v4")

        except Exception as e:
            # On any failure fallback to inline data URI
            import base64
            print(f"GCS upload failed: {e}, falling back to data URI")
            public_url = f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}"
    else:
        # Offline mode or GCS not configured
        import base64
        public_url = f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}"

    return {"pdf_url": public_url}


async def generate_pdf(context: dict[str, Any], analysis: dict[str, Any]) -> dict[str, str]:
    """Generate PDF for the orchestrator (returns base64 and filename).
    
    This is the new interface expected by the orchestrator.
    
    Args:
        context: User context from collect_context
        analysis: Analysis results from analyse_and_reframe
        
    Returns:
        Dictionary with pdf_base64 and filename
    """
    import base64
    
    # Build the PDF using the existing function
    session_dict = {
        "intake_data": context,
        "analysis_output": analysis.get("analysis", "")
    }
    
    pdf_bytes = build_pdf_bytes(
        intake_data=context,
        analysis_output=analysis.get("analysis", ""),
    )
    
    # Generate filename
    name = context.get("name", "usuario").lower().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"resumen_{name}_{timestamp}.pdf"
    
    # Return base64 encoded PDF
    return {
        "pdf_base64": base64.b64encode(pdf_bytes).decode(),
        "filename": filename
    }
