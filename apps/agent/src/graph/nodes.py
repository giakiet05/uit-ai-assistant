"""
Graph nodes for LangGraph agent workflow.
"""

from typing import Literal
from langchain_core.messages import AIMessage, SystemMessage

from .state import AgentState
from ..config import BENCHMARK_PROMPT


# System prompt for UIT AI Assistant (imported from config/prompts.py)
SYSTEM_PROMPT = BENCHMARK_PROMPT


def agent_node(state: AgentState, llm_with_tools):
    """
    Agent reasoning node - LLM decides whether to use tools or respond.

    Args:
        state: Current agent state
        llm_with_tools: LLM instance bound with tools

    Returns:
        Updated state with LLM response
    """
    messages = state["messages"]
    user_id = state["user_id"]

    # Add system prompt if not already present (first invocation)
    # Check if first message is SystemMessage
    has_system_prompt = (
        len(messages) > 0 and
        isinstance(messages[0], SystemMessage)
    )

    if not has_system_prompt:
        # Inject user_id into system prompt
        system_prompt_with_user_id = SYSTEM_PROMPT + f"\n\n## THÔNG TIN NGƯỜI DÙNG HIỆN TẠI\nUser ID: {user_id}\n\nKhi gọi tool `get_user_credential`, LUÔN LUÔN sử dụng user_id này."
        messages = [SystemMessage(content=system_prompt_with_user_id)] + messages

    # Invoke LLM with tools
    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """
    Routing function: decide whether to call tools or finish.

    Args:
        state: Current agent state

    Returns:
        "tools" if LLM wants to call tools, "end" otherwise
    """
    last_message = state["messages"][-1]

    # If LLM called tools -> route to tools node
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print("\n" + "="*70)
        print("[AGENT] Tool calls requested:")
        for i, tool_call in enumerate(last_message.tool_calls, 1):
            print(f"  [{i}] Tool: {tool_call['name']}")
            print(f"      Args: {tool_call['args']}")
            print(f"      Call ID: {tool_call['id']}")
        print("="*70 + "\n")
        return "tools"

    # Otherwise, finish
    print("\n" + "="*70)
    print("[AGENT] No tool calls - finishing")
    print("="*70 + "\n")
    return "end"
