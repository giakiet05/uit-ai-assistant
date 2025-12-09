"""
Entry point for running gRPC server as a module.

Usage:
    uv run python -m src.grpc.agent_server
"""

from .agent_server import main

if __name__ == '__main__':
    main()
