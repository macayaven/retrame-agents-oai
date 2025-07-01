"""Thin wrapper that initialises a singleton async OpenAI client.

Separating the initialisation logic from function files keeps import graphs
clean and also simplifies patching in unit tests.
"""
from __future__ import annotations

import os
from functools import lru_cache

from openai import AsyncOpenAI


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    """Return a memoised :class:`AsyncOpenAI` instance.

    The API key is loaded lazily from the ``OPENAI_API_KEY`` environment
    variable so that test doubles can monkey-patch the environment at runtime.
    """

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

    return AsyncOpenAI(api_key=api_key) 