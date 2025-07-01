"""escalate_crisis – safe-completion function.

Returns the Spanish crisis hotline and EU emergency number.  The text mirrors
`SafetyGuard`.
"""

from __future__ import annotations

_CRISIS_MSG = (
    "Parece que estás pasando por un momento muy difícil y podrías estar pensando en hacerte daño. "
    "Por favor, llama inmediatamente al **024** (línea de ayuda en España, 24 h, gratuita) o al "
    "**112** si tu vida está en peligro. Si te encuentras fuera de España, marca el número de "
    "emergencias local o consulta https://findahelpline.com. Un profesional se pondrá en contacto "
    "contigo en breve."
)


def escalate_crisis(msg: str | None = None) -> dict[str, str | bool]:
    """Return crisis safe-completion payload."""
    return {"crisis": True, "message": _CRISIS_MSG}


async def safe_complete(reason: str) -> dict[str, Any]:
    """Handle crisis situations with safety resources.
    
    This is a wrapper for the orchestrator's expected interface.
    
    Args:
        reason: Reason for crisis escalation
        
    Returns:
        Dictionary with crisis detection info and resources
    """
    from typing import Any
    
    # Call the original escalate_crisis function
    crisis_result = escalate_crisis(reason)
    
    # Transform to match the orchestrator's expected format
    return {
        "crisis_detected": crisis_result["crisis"],
        "reason": f"Crisis detected: {reason}",
        "resources": [
            {
                "name": "Línea de Prevención del Suicidio (España)",
                "contact": "024",
                "description": "Disponible 24/7, gratuita"
            },
            {
                "name": "Emergencias",
                "contact": "112",
                "description": "Si tu vida está en peligro"
            },
            {
                "name": "International Crisis Lines",
                "contact": "https://findahelpline.com",
                "description": "Encuentra ayuda en tu país"
            }
        ]
    }
