"""Unit tests for GCS upload function."""

import os
import pytest

from app.assistants.functions.gcs_upload import gcs_upload


@pytest.mark.asyncio
async def test_gcs_upload_offline_mode():
    """Test GCS upload returns mock response in offline mode."""
    # Ensure we're in offline mode
    os.environ["OFFLINE"] = "1"
    
    # Test data
    pdf_base64 = "dGVzdCBwZGYgY29udGVudA=="  # "test pdf content" in base64
    filename = "test_report.pdf"
    
    # Call function
    result = await gcs_upload(pdf_base64, filename)
    
    # Verify mock response
    assert result["success"] is True
    assert "public_url" in result
    assert "reframe-apd-pdf" in result["public_url"]
    assert filename in result["public_url"]
    assert result["public_url"] == "https://storage.googleapis.com/reframe-apd-pdf/test_report.pdf"


@pytest.mark.asyncio
async def test_gcs_upload_with_public_url_param():
    """Test that public_url parameter is ignored (for schema compatibility)."""
    os.environ["OFFLINE"] = "1"
    
    result = await gcs_upload(
        pdf_base64="dGVzdA==",
        filename="test.pdf",
        public_url="ignored_url"
    )
    
    assert result["success"] is True
    assert result["public_url"] != "ignored_url"


@pytest.mark.asyncio 
async def test_gcs_upload_error_handling():
    """Test error handling with invalid base64."""
    os.environ["OFFLINE"] = "0"  # Force online mode
    
    # Invalid base64
    result = await gcs_upload(
        pdf_base64="invalid-base64!@#",
        filename="test.pdf"
    )
    
    # Should fail gracefully
    assert result["success"] is False
    assert "error" in result
    assert result["public_url"] == ""
    
    # Reset to offline mode
    os.environ["OFFLINE"] = "1"