"""escalate_crisis – safe-completion function.

Returns the Spanish crisis hotline and EU emergency number.  The text mirrors
`SafetyGuard`.
"""

from __future__ import annotations

from typing import Dict, Union

_CRISIS_MSG = (
    "Parece que estás pasando por un momento muy difícil y podrías estar pensando en hacerte daño. "
    "Por favor, llama inmediatamente al **024** (línea de ayuda en España, 24 h, gratuita) o al "
    "**112** si tu vida está en peligro. Si te encuentras fuera de España, marca el número de "
    "emergencias local o consulta https://findahelpline.com. Un profesional se pondrá en contacto "
    "contigo en breve."
)


def escalate_crisis(msg: str | None = None) -> Dict[str, Union[str, bool]]:  # noqa: D401
    """Return crisis safe-completion payload."""
    return {"crisis": True, "message": _CRISIS_MSG} 