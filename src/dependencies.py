from functools import lru_cache

from repositories.user_repository import UserRepository


@lru_cache(1)
def get_user_repository() -> UserRepository:
    """FastAPI dependency: returns singleton UserRepository instance."""
    return UserRepository()
