"""Simple LangGraph Agent that uses the A2A Agent Node via A2A protocol.

This is a simple agent that can delegate tasks to the A2A Agent Node
through the A2A protocol by using the call_a2a_agent tool.
"""
from __future__ import annotations

import os
from typing import Dict, Any

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from app.a2a_tool import call_a2a_agent

# Load environment variables from .env file
load_dotenv()


def build_simple_a2a_agent():
    """Build a simple LangGraph agent that can call the A2A Agent Node.
    
    Returns:
        A compiled LangGraph that uses the A2A agent tool
    """
    # Initialize the model
    model = ChatOpenAI(
        model=os.getenv('TOOL_LLM_NAME', 'gpt-4o-mini'),
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        openai_api_base=os.getenv('TOOL_LLM_URL', 'https://api.openai.com/v1'),
        temperature=0,
    )
    
    # Create tools list - just the A2A agent tool
    tools = [call_a2a_agent]
    
    # Use LangGraph's prebuilt create_react_agent for simplicity
    checkpointer = MemorySaver()
    graph = create_react_agent(
        model,
        tools,
        checkpointer=checkpointer
    )
    
    return graph


# Convenience function to invoke the agent
def invoke_simple_agent(query: str, thread_id: str = "default") -> Dict[str, Any]:
    """Invoke the simple A2A agent with a query.
    
    Args:
        query: The user's query
        thread_id: Optional thread ID for conversation context
        
    Returns:
        The agent's response
    """
    graph = build_simple_a2a_agent()
    config = {'configurable': {'thread_id': thread_id}}
    
    # System instruction for the simple agent
    system_instruction = (
        "You are a simple AI assistant that can delegate tasks to a specialized "
        "A2A Agent Node. When you receive a query, you should use the call_a2a_agent "
        "tool to send the query to the specialized agent, which has access to web search, "
        "academic paper search, and document retrieval capabilities. "
        "Present the agent's response clearly to the user."
    )
    
    # Add system message to initial messages
    initial_messages = [
        SystemMessage(content=system_instruction),
        ('user', query)
    ]
    
    response = graph.invoke(
        {'messages': initial_messages},
        config=config
    )
    
    return response


if __name__ == '__main__':
    print("=" * 50)
    print("Simple A2A Agent - Interactive Mode")
    print("=" * 50)
    print("Type your questions below. Type 'quit' or 'exit' to stop.\n")
    
    thread_id = "interactive-session"
    
    while True:
        try:
            # Get user input
            query = input("\nYour question: ").strip()
            
            # Check for exit commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\nGoodbye!")
                break
            
            # Skip empty inputs
            if not query:
                continue
            
            # Invoke the agent
            print("\nProcessing...")
            result = invoke_simple_agent(query, thread_id=thread_id)
            
            # Display response
            print("\n" + "-" * 50)
            print("Agent Response:")
            print("-" * 50)
            print(result['messages'][-1].content)
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()