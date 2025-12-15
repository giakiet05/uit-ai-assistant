"""
Main entry point for LangGraph Agent gRPC Server.

Usage:
    uv run python main.py
"""

from src.grpc.agent_server import serve

if __name__ == "__main__":
    serve()
