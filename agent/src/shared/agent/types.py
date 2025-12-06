"""
Type definitions for agent responses and metadata.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ToolCall:
    """Thông tin về 1 lần gọi tool."""
    tool_name: str
    args: Dict[str, Any]
    output: str


@dataclass
class Source:
    """RAG source metadata."""
    title: str
    content: str
    score: float
    url: str = ""


@dataclass
class AgentResponse:
    """
    Response từ agent với đầy đủ metadata.

    Hiện tại các field metadata (tool_calls, sources, reasoning_steps)
    đều trả về empty, sẽ implement extraction logic sau khi nâng cấp workflow.
    """

    # Text response (đã clean, bỏ Thought/Action/Observation)
    content: str

    # Metadata (tạm thời empty)
    tool_calls: List[ToolCall] = field(default_factory=list)
    reasoning_steps: List[str] = field(default_factory=list)
    sources: List[Source] = field(default_factory=list)

    # Stats (tạm thời None)
    tokens_used: Optional[int] = None
    latency_ms: Optional[int] = None
