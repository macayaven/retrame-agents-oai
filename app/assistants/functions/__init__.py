"""Assistant function entry-points.

Each function *name* must match the registration in the published Assistant.
They are regular async callables so they can be imported by both the OpenAI
runtime and our internal unit tests.
"""

from .analyse import analyse_and_reframe
from .collect import collect_context
from .escalate import escalate_crisis, safe_complete
from .gcs_upload import gcs_upload
from .pdf import generate_pdf

__all__ = [
    "analyse_and_reframe",
    "collect_context",
    "escalate_crisis",
    "generate_pdf",
    "gcs_upload",
    "safe_complete",
]
