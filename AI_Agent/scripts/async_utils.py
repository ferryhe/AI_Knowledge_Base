"""
Async utilities for streaming and concurrent API calls.

This module provides async support for:
- Streaming chat completions
- Concurrent embedding generation
- Async retry logic
"""

import asyncio
from typing import AsyncGenerator, List

from openai import AsyncOpenAI

from utils import retry_with_exponential_backoff_async


async def stream_chat_completion(
    client: AsyncOpenAI,
    messages: List[dict],
    model: str = "gpt-4o",
    temperature: float = 0.2,
) -> AsyncGenerator[str, None]:
    """
    Stream chat completion responses for better UX.
    
    Args:
        client: Async OpenAI client
        messages: Chat messages
        model: Model to use
        temperature: Sampling temperature
    
    Yields:
        Chunks of the response as they arrive
    
    Example:
        async with AsyncOpenAI() as client:
            async for chunk in stream_chat_completion(client, messages):
                print(chunk, end='', flush=True)
    """
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True,
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content


async def create_embeddings_async(
    client: AsyncOpenAI,
    texts: List[str],
    model: str = "text-embedding-3-large",
    batch_size: int = 64,
) -> List[List[float]]:
    """
    Create embeddings asynchronously with batching and retry logic.
    
    Args:
        client: Async OpenAI client
        texts: List of texts to embed
        model: Embedding model to use
        batch_size: Maximum texts per API call
    
    Returns:
        List of embedding vectors
    """
    all_embeddings = []
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        # Use retry logic
        response = await retry_with_exponential_backoff_async(
            client.embeddings.create,
            model=model,
            input=batch,
            max_retries=3,
        )
        
        embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(embeddings)
    
    return all_embeddings


async def concurrent_queries(
    client: AsyncOpenAI,
    queries: List[str],
    retrieval_func,
    max_concurrent: int = 5,
) -> List[dict]:
    """
    Process multiple queries concurrently with rate limiting.
    
    Args:
        client: Async OpenAI client
        queries: List of questions to process
        retrieval_func: Async function for retrieval
        max_concurrent: Maximum concurrent requests
    
    Returns:
        List of results for each query
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_query(query: str) -> dict:
        async with semaphore:
            try:
                result = await retrieval_func(client, query)
                return {"query": query, "result": result, "error": None}
            except Exception as e:
                return {"query": query, "result": None, "error": str(e)}
    
    tasks = [process_query(q) for q in queries]
    return await asyncio.gather(*tasks)


# Example usage for Streamlit with streaming
async def generate_streaming_answer(
    client: AsyncOpenAI,
    question: str,
    context: str,
    system_prompt: str,
) -> AsyncGenerator[str, None]:
    """
    Generate answer with streaming for Streamlit UI.
    
    Usage in Streamlit:
        import streamlit as st
        from openai import AsyncOpenAI
        
        async def show_answer():
            client = AsyncOpenAI()
            response_placeholder = st.empty()
            full_response = ""
            
            async for chunk in generate_streaming_answer(client, question, context, prompt):
                full_response += chunk
                response_placeholder.markdown(full_response)
        
        # Run in Streamlit
        asyncio.run(show_answer())
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Retrieved snippets:\n{context}\n\nQuestion: {question}"},
    ]
    
    async for chunk in stream_chat_completion(client, messages):
        yield chunk
