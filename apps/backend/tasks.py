from .main import celery_app, redis_client
import time
import json
import os
import random # For simulating query embedding
from think_tank_monorepo.packages.ai_agent_core.persona_system import generate_mock_persona_prompt
from think_tank_monorepo.packages.ai_agent_core.light_agent import LightAgent
from think_tank_monorepo.packages.data_storage.vector_db import query_expert_embeddings
from think_tank_monorepo.packages.cache_queue.redis_client import get_cache, set_cache, publish_message as cache_publish_message

def publish_progress_to_redis(task_id: str, message: str):
    """Helper function to publish progress to Redis."""
    # Using the redis_client from .main for existing pub/sub mechanism
    redis_client.publish("debate_progress", json.dumps({"task_id": task_id, "status": message}))
    # Also publish via the new cache_queue redis_client for consistency if needed, though main.py's client is primary
    # cache_publish_message("debate_progress", {"task_id": task_id, "status": message})

@celery_app.task
def process_query(query: str):
    print(f"Processing query: {query}")
    publish_progress_to_redis("query_processing", f"Query received: '{query}'")
    time.sleep(0.5)

    # Caching key for the query result
    cache_key = f"query_result:{query}"
    
    # 1. Check Redis cache for the query result
    cached_result = get_cache(cache_key)
    if cached_result:
        publish_progress_to_redis("cache_retrieval", f"Retrieved query result from cache.")
        final_result = f"AI Agent Core processed query: '{query}'.\n(Cached Result) {cached_result}"
        print(final_result)
        return final_result

    # If not in cache, proceed with processing
    publish_progress_to_redis("query_processing", f"Query not in cache. Proceeding with vector DB lookup.")
    time.sleep(0.5)

    # Simulate query embedding generation for vector DB
    # In a real scenario, this would come from an embedding model applied to the 'query'
    query_embedding = [random.uniform(0, 1) for _ in range(1536)] # Example 1536-dim vector

    # 2. Query the vector DB with mock expert candidate querying
    publish_progress_to_redis("vector_db_query", "Querying vector database for expert candidates...")
    time.sleep(0.5)
    
    # Replace mock expert candidate querying with actual call to vector_db
    expert_candidates = query_expert_embeddings(query_embedding, n_results=3)
    publish_progress_to_redis(
        "expert_candidates_retrieved",
        f"Retrieved {len(expert_candidates)} expert candidates from vector DB."
    )
    # Convert expert_candidates to a string representation for logging/display
    expert_candidates_str = json.dumps(expert_candidates, indent=2)
    print(f"Expert candidates from vector DB:\n{expert_candidates_str}")
    time.sleep(0.5)

    # 3. Integrate Archon or Mythosmith persona system minimally
    # Incorporate expert candidates into persona generation if applicable, for this task,
    # we'll just continue the flow.
    persona_prompt = generate_mock_persona_prompt(query)
    publish_progress_to_redis("persona_generation", f"Mock persona generated: '{persona_prompt}'")
    time.sleep(0.5)

    # 4. Implement LightAgent with a simplified TAL engine for single-round reasoning
    # Pass the publish_progress_to_redis function to LightAgent
    light_agent = LightAgent(publish_progress=publish_progress_to_redis)
    light_agent_output = light_agent.run_reasoning(persona_prompt, query)
    
    # 5. Ensure all agents communicate via Redis pub/sub and Celery tasks
    final_result_content = f"AI Agent Core processed query: '{query}'.\nExpert Candidates: {expert_candidates_str}\nLightAgent Output: {light_agent_output}"
    
    # Cache the final result before returning
    set_cache(cache_key, final_result_content, ex=600) # Cache for 10 minutes
    publish_progress_to_redis("cache_storage", f"Query result cached for key: {cache_key}")

    final_result = final_result_content
    publish_progress_to_redis("final_result", final_result)
    print(final_result)
    return final_result