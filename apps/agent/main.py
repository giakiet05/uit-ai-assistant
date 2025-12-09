"""
Entry point for Agent Service gRPC server.

Usage:
    uv run python main.py
"""
import asyncio


def main():
    """Start the gRPC agent server."""
    from src.grpc.agent_server import serve

    asyncio.run(serve())


if __name__ == "__main__":
    main()
