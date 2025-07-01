"""generate_pdf – Build PDF and upload to Supabase storage.

This wrapper re-uses the legacy `build_pdf_bytes` helper so we keep the PDF
layout identical to the ADK implementation.
"""
from __future__ import annotations

import os
from typing import Any, Dict

from app.tools.pdf_generator import build_pdf_bytes

try:
    from supabase import create_client
except ImportError:  # pragma: no cover
    create_client = None  # type: ignore


BUCKET_NAME = "reports"


def _get_supabase_client():  # pragma: no cover – trivial wrapper
    if create_client is None:  # type: ignore[only-if-true]
        raise RuntimeError("supabase library not available")

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_KEY must be set")
    return create_client(url, key)


def generate_pdf(session_dict: Dict[str, Any]) -> Dict[str, str]:  # noqa: D401
    """Create the PDF, upload, and return a signed public URL.

    Parameters
    ----------
    session_dict
        Dict containing at least ``intake_data`` and ``analysis_output``.
    """

    pdf_bytes = build_pdf_bytes(
        intake_data=session_dict.get("intake_data", {}),
        analysis_output=session_dict.get("analysis_output", ""),
    )

    # Upload to Supabase Storage (or gracefully fall back to data URL)
    public_url: str
    if create_client and os.environ.get("SUPABASE_URL", "").startswith("http"):
        try:
            client = _get_supabase_client()
            filename = f"report-{os.urandom(4).hex()}.pdf"
            client.storage.from_(BUCKET_NAME).upload(filename, pdf_bytes, {
                "content-type": "application/pdf"
            })
            public_url = client.storage.from_(BUCKET_NAME).get_public_url(filename)
        except Exception:
            # On any failure fallback to inline data URI
            import base64

            public_url = f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}"
    else:
        import base64

        public_url = f"data:application/pdf;base64,{base64.b64encode(pdf_bytes).decode()}"

    return {"pdf_url": public_url} 