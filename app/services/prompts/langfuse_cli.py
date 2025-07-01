"""Prompt manager that downloads and caches prompts from Langfuse."""

from functools import lru_cache
import os

from langfuse import Langfuse

from app.config.base import Settings


class _LangfusePromptManager:
    """Manages prompt downloading and caching from Langfuse."""

    def __init__(self) -> None:
        """Initialize the prompt manager."""
        self.settings = Settings()
        self._prompts: dict[str, str] = {}
        self._langfuse: Langfuse | None = None
        self._cache_dir = "/tmp/reframe_prompts"
        os.makedirs(self._cache_dir, exist_ok=True)
        self._download_all_prompts()

    def _get_langfuse_client(self) -> Langfuse:
        """Get or create Langfuse client."""
        if not self._langfuse:
            self._langfuse = Langfuse(
                host=self.settings.langfuse_host,
                public_key=self.settings.langfuse_public_key,
                secret_key=self.settings.langfuse_secret_key,
            )
        return self._langfuse

    def _get_cache_path(self, prompt_name: str) -> str:
        """Get the cache file path for a prompt."""
        return os.path.join(self._cache_dir, f"{prompt_name}.txt")

    def _download_prompt(self, prompt_name: str) -> str:
        """Download a prompt from Langfuse and cache it."""
        try:
            # Try to load from memory cache first
            if prompt_name in self._prompts:
                return self._prompts[prompt_name]

            # Try to load from file cache
            cache_path = self._get_cache_path(prompt_name)
            if os.path.exists(cache_path):
                with open(cache_path, encoding="utf-8") as f:
                    prompt = f.read()
                    self._prompts[prompt_name] = prompt
                    return prompt

            # Download from Langfuse
            langfuse = self._get_langfuse_client()
            prompt_obj = langfuse.get_prompt(prompt_name)
            prompt = str(prompt_obj.compile())

            # Cache in memory and file
            self._prompts[prompt_name] = prompt
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(prompt)

            return prompt

        except Exception as e:
            raise RuntimeError(f"Failed to download prompt '{prompt_name}': {e!s}") from e

    def _download_all_prompts(self) -> dict[str, str]:
        """Download all required prompts and cache them."""
        # Prefetch both legacy ADK prompts and the new OpenAI-Assistants versions so we
        # can switch seamlessly at runtime / in tests without additional network
        # round-trips (FR-10).  These names correspond to the versions defined in
        # `design.md` and must stay in sync with the Assistants that reference
        # them.
        required_prompts = [
            # Legacy agents (kept for backwards-compat / regression tests)
            "intake-agent-adk-instructions",
            "reframe-agent-adk-instructions",
            "synthesis-agent-adk-instructions",

            # OpenAI Assistants v0.2 prompts
            "intake-agent-oai-v0.2",
            "reframe-agent-oai-v0.2",
            # Parser agent prompt
            "parser-agent-oai-v0.3",
            "intake-agent-oai-v0.3",
            "reframe-agent-oai-v0.3",
        ]

        for prompt_name in required_prompts:
            self._download_prompt(prompt_name)

        return self._prompts

    def _get_prompt(self, prompt_name: str) -> str:
        """Get a prompt, downloading if necessary."""
        if prompt_name not in self._prompts:
            return self._download_prompt(prompt_name)
        return self._prompts[prompt_name]

    def clear_cache(self) -> None:
        """Clear all cached prompts."""
        self._prompts.clear()
        # Optionally remove cache files
        for file in os.listdir(self._cache_dir):
            if file.endswith(".txt"):
                os.remove(os.path.join(self._cache_dir, file))

    @lru_cache  # noqa: B019
    def fetch_prompt(self, name: str) -> str:
        """Return the compiled prompt string by name.

        The prompt is cached in memory by the PromptManager; an additional
        `lru_cache` here lets us skip the attribute lookup entirely on hot paths.
        """
        return self._get_prompt(name)


prompt_manager = _LangfusePromptManager()
