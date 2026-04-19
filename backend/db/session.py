"""Async SQLAlchemy session factory — lazy initialization."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        from config import get_settings
        _engine = create_async_engine(get_settings().database_url, echo=False)
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions."""
    async with get_session_factory()() as session:
        yield session
