"""
Checkpointer for LangGraph state persistence.
"""

from langgraph.checkpoint.memory import MemorySaver
# from langgraph.checkpoint.postgres import PostgresSaver
# from langgraph.checkpoint.redis import RedisSaver


def create_checkpointer(backend: str = "memory"):
    """
    Create checkpointer for state persistence.

    Args:
        backend: Storage backend - currently only "memory" supported in this helper
                 For production (Postgres/Redis), use context manager directly

    Returns:
        Checkpointer instance

    Raises:
        ValueError: If backend is invalid

    Note:
        PostgresSaver requires context manager and should be used directly:

        ```python
        with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
            checkpointer.setup()
            graph = create_agent_graph(llm, tools, checkpointer)
        ```
    """
    if backend == "memory":
        return _create_memory_checkpointer()
    else:
        raise ValueError(
            f"Invalid backend '{backend}'. Only 'memory' supported in helper. "
            f"For Postgres, use PostgresSaver.from_conn_string() with context manager."
        )


def _create_memory_checkpointer():
    """
    Create in-memory checkpointer (for testing/development).

    Note: State is lost when process exits.
    Use PostgreSQL or Redis for production.
    """
    print("[CHECKPOINTER] Creating in-memory checkpointer")
    checkpointer = MemorySaver()
    print("[CHECKPOINTER] ✅ In-memory checkpointer created (state will be lost on restart)")
    return checkpointer

