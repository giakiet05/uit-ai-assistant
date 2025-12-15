"""
LangGraph agent workflow definition.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from functools import partial

from .state import AgentState
from .nodes import agent_node, should_continue


def create_agent_graph(llm, tools, checkpointer=None):
    """
    Create LangGraph agent with ReAct-style workflow.

    Workflow:
        START -> agent -> [tools | END]
                  ^----------|

    Args:
        llm: Language model instance
        tools: List of tools (MCP tools + native tools)
        checkpointer: State persistence layer (PostgresSaver or RedisSaver)

    Returns:
        Compiled graph ready for invocation
    """
    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(tools)

    # Create partial function with LLM
    agent_with_llm = partial(agent_node, llm_with_tools=llm_with_tools)

    # Define graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_with_llm)  # LLM reasoning node
    # ToolNode with error handling - return error as ToolMessage instead of raising
    workflow.add_node("tools", ToolNode(tools, handle_tool_errors=True))

    # Set entry point using START
    workflow.add_edge(START, "agent")

    # Add conditional edges from agent
    workflow.add_conditional_edges(
        "agent",
        should_continue,  # Routing function
        {
            "tools": "tools",  # If LLM calls tools -> go to tools node
            "end": END         # Otherwise -> finish
        }
    )

    # After tools execute -> back to agent for next reasoning step
    workflow.add_edge("tools", "agent")

    # Compile graph with checkpointer for state persistence
    graph = workflow.compile(checkpointer=checkpointer)

    return graph
