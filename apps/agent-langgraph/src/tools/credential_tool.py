"""
Native LangChain tool for retrieving user credentials from Redis.
"""

import redis
from langchain_core.tools import tool
from typing import Literal


# Redis client (shared across tool calls)
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)


@tool
def get_user_credential(user_id: str, source: Literal["daa", "courses", "drl"]) -> str:
    """Get user authentication credential from Redis storage.

    IMPORTANT: You do NOT need to provide user_id parameter - it will be
    automatically injected from the current user context. Just specify the source.

    Use this tool to retrieve authentication credentials needed for
    accessing external services like DAA portal, courses portal, or DRL portal.

    This tool reads from Redis where credentials are stored after the user
    syncs them via the browser extension.

    Args:
        user_id: (Auto-injected - DO NOT SPECIFY) The user's ID
        source: Credential source - must be one of: 'daa', 'courses', 'drl'
            - 'daa': DAA portal credentials (for grades, schedule)
            - 'courses': Courses portal credentials
            - 'drl': DRL portal credentials

    Returns:
        Authentication cookie string in format "name1=value1; name2=value2"

    Raises:
        ValueError: If source is invalid or credential not found

    Example:
        To get DAA credentials, just call with source only:
        >>> cookie = get_user_credential(source="daa")
        >>> # Then use cookie with get_grades(cookie) or get_schedule(cookie)
    """
    # Validate source
    valid_sources = {'daa', 'courses', 'drl'}
    if source not in valid_sources:
        raise ValueError(
            f"Invalid source '{source}'. Must be one of: {valid_sources}"
        )

    # Build Redis key
    key = f"{source}_cookie:{user_id}"

    try:
        # Get credential from Redis
        credential = redis_client.get(key)

        if not credential:
            raise ValueError(
                f"No {source} credential found for user {user_id}. "
                f"Please sync credentials via browser extension first."
            )
        print(f"Cookie: {credential}")
        return credential

    except redis.RedisError as e:
        raise ValueError(f"Redis error: {str(e)}")
