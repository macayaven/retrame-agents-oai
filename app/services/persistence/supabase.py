from functools import lru_cache

from google.adk.sessions import (
    DatabaseSessionService,
    InMemorySessionService,
)

from app.config.base import Settings


@lru_cache
def get_session_service() -> DatabaseSessionService | InMemorySessionService:
    """Return an appropriate SessionService instance.

    If `SUPABASE_REFRAME_DB_CONNECTION_STRING` is set in the environment we
    treat it as a standard SQLAlchemy/Postgres URL and hand it to the ADK's
    built-in `DatabaseSessionService`. This works for Supabase because the
    service exposes a regular Postgres endpoint.  When that variable is not
    set, we fall back to the in-memory store so local development and unit
    tests require zero infrastructure.
    """

    settings = Settings()
    if settings.supabase_connection_string:

        return DatabaseSessionService(db_url=str(settings.supabase_connection_string))

    return InMemorySessionService()
