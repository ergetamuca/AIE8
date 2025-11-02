"""A2A Protocol Tool for calling the Agent Node via A2A protocol.

This tool wraps the A2AClient to make API calls to the Agent Node running
at localhost:10000 through the A2A protocol.
"""
from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import AgentCard, MessageSendParams, SendMessageRequest
from langchain_core.tools import tool


# Cache for the A2A client (set after first initialization)
_a2a_client_cache: tuple[A2AClient, httpx.AsyncClient] | None = None


def _get_a2a_client() -> tuple[A2AClient, httpx.AsyncClient]:
    """Get or create A2A client and HTTP client (cached)."""
    global _a2a_client_cache
    
    if _a2a_client_cache is not None:
        return _a2a_client_cache
    
    base_url = 'http://localhost:10000'
    httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=base_url,
    )
    
    # Fetch the agent card synchronously (wrap async call)
    async def _fetch_card():
        return await resolver.get_agent_card()
    
    # Run async function - handle event loop properly
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, we need to use a different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _fetch_card())
                agent_card = future.result()
        else:
            agent_card = loop.run_until_complete(_fetch_card())
    except RuntimeError:
        # No event loop, create one
        agent_card = asyncio.run(_fetch_card())
    
    client = A2AClient(
        httpx_client=httpx_client,
        agent_card=agent_card
    )
    
    _a2a_client_cache = (client, httpx_client)
    return _a2a_client_cache


def _call_a2a_agent_sync(query: str) -> str:
    """Synchronously call the A2A agent (wraps async call)."""
    async def _async_call():
        client, httpx_client = _get_a2a_client()
        
        send_message_payload = {
            'message': {
                'role': 'user',
                'parts': [{'kind': 'text', 'text': query}],
                'message_id': uuid4().hex,
            },
        }
        request = SendMessageRequest(
            id=str(uuid4()),
            params=MessageSendParams(**send_message_payload)
        )
        
        try:
            response = await client.send_message(request)
            
            # Debug: print full response structure
            import json
            print("\n" + "="*50)
            print("A2A Response Structure:")
            print("="*50)
            print(json.dumps(response.model_dump(mode='json'), indent=2))
            print("="*50 + "\n")
            
            # Extract the response text from the A2A response
            if hasattr(response, 'root') and hasattr(response.root, 'result'):
                result = response.root.result
                
                # Check for artifacts (final response) - this is where completed tasks store results
                if hasattr(result, 'artifacts') and result.artifacts:
                    for artifact in result.artifacts:
                        if hasattr(artifact, 'parts') and artifact.parts:
                            for part in artifact.parts:
                                # Check multiple possible paths for text
                                if hasattr(part, 'root'):
                                    if hasattr(part.root, 'text'):
                                        return part.root.text
                                elif hasattr(part, 'text'):
                                    return part.text
                
                # Check for messages in the result (intermediate or final messages)
                if hasattr(result, 'messages') and result.messages:
                    for msg in result.messages:
                        if hasattr(msg, 'parts') and msg.parts:
                            for part in msg.parts:
                                if hasattr(part, 'text'):
                                    return part.text
                                elif hasattr(part, 'root') and hasattr(part.root, 'text'):
                                    return part.root.text
                
                # Check if result itself has text
                if hasattr(result, 'text'):
                    return result.text
                    
            # Fallback: try to extract from response dict
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else {}
            
            # Try to navigate through the response structure
            if 'root' in response_dict and 'result' in response_dict['root']:
                result = response_dict['root']['result']
                if 'artifacts' in result and result['artifacts']:
                    for artifact in result['artifacts']:
                        if 'parts' in artifact and artifact['parts']:
                            for part in artifact['parts']:
                                if 'root' in part and 'text' in part['root']:
                                    return part['root']['text']
                                elif 'text' in part:
                                    return part['text']
                                    
            # Final fallback: return string representation
            return str(response.model_dump())
        except Exception as e:
            return f"Error calling A2A agent: {str(e)}"
    
    # Run async function
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _async_call())
                return future.result()
        else:
            return loop.run_until_complete(_async_call())
    except RuntimeError:
        return asyncio.run(_async_call())


@tool
def call_a2a_agent(
    query: Annotated[str, "The query to send to the A2A agent node"]
) -> str:
    """Call the A2A Agent Node through the A2A protocol.
    
    This tool makes API calls to the Agent Node running at localhost:10000
    using the A2A (Agent-to-Agent) protocol. Use this when you need to
    delegate tasks to the specialized agent that has access to web search,
    academic papers, and document retrieval.
    
    Args:
        query: The question or task to send to the A2A agent
        
    Returns:
        The response from the A2A agent node
    """
    return _call_a2a_agent_sync(query)