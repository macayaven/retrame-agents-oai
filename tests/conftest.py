from collections import deque
from collections.abc import AsyncGenerator

from google.adk.artifacts import InMemoryArtifactService
from google.adk.models import BaseLlm, LlmRequest, LlmResponse
from google.genai.types import Content, Part
import pytest


##############################################################################
# Simple stub that replaces any LlmAgent's model with deterministic replies. #
##############################################################################
class StubLLM(BaseLlm):
    """Deterministic stand-in for any Gemini / GPT model used in tests."""

    def __init__(self, canned: deque[str]) -> None:
        super().__init__(model="stub")  # parent ctor expects a model name
        self._answers = canned

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        text = self._answers.popleft() if self._answers else "stub-reply"
        yield LlmResponse(content=Content(parts=[Part(text=text)], role="model"))


@pytest.fixture(scope="session")
def artifact_service() -> InMemoryArtifactService:
    """Artifact service for tests."""
    return InMemoryArtifactService()

@pytest.fixture(scope="function")
def supabase_env_vars(monkeypatch):
    """Ensure SUPABASE_URL environment variable is set to its original value."""
    original_url = "https://your_original_supabase_url.supabase.co"
    original_key = "your_original_supabase_key"
    monkeypatch.setenv("SUPABASE_URL", original_url)
    monkeypatch.setenv("SUPABASE_KEY", original_key)