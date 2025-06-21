from .main import celery_app, logger as main_logger # Import logger from main, removed redis_client
import time
import json
import os
import random # For simulating query embedding
from think_tank_monorepo.packages.ai_agent_core.persona_system import generate_mock_persona_prompt
from think_tank_monorepo.packages.ai_agent_core.light_agent import LightAgent
# Assuming vector_db query function expects an embedding, not text, based on its previous usage context.
# If vector_db.query_expert_embeddings was updated to take text, this import and its usage might need adjustment.
from think_tank_monorepo.packages.data_storage.vector_db import query_expert_embeddings
from think_tank_monorepo.packages.cache_queue.redis_client import get_cache, set_cache, publish_message as publish_message_to_channel

# Use the logger imported from main.py
logger = main_logger

# Removed local publish_progress_to_redis function. Using publish_message_to_channel directly.

@celery_app.task(bind=True)
def process_query(self, query: str):
    task_id = self.request.id
    logger.info(f"[Task ID: {task_id}] Processing query: {query}")
    
    # Directly use publish_message_to_channel
    payload_init = {"task_id": task_id, "status": f"Query received: '{query}'", "level": "INFO"}
    if not publish_message_to_channel("debate_progress", payload_init):
        logger.error(f"[Task ID: {task_id}] Failed to publish initial progress: '{payload_init['status']}'")

    try:
        time.sleep(0.5) # Simulating initial work

        cache_key = f"query_result:{query}"

        cached_result = get_cache(cache_key)
        if cached_result:
            payload_cache = {"task_id": task_id, "status": "Retrieved query result from cache.", "level": "INFO"}
            publish_message_to_channel("debate_progress", payload_cache)
            final_result = f"AI Agent Core processed query: '{query}'.\n(Cached Result) {cached_result}"
            logger.info(f"[Task ID: {task_id}] Cache hit for query: {query}")
            return final_result

        payload_lookup = {"task_id": task_id, "status": "Query not in cache. Proceeding with vector DB lookup.", "level": "INFO"}
        publish_message_to_channel("debate_progress", payload_lookup)
        time.sleep(0.5)

        query_embedding = [random.uniform(0, 1) for _ in range(1536)]

        payload_vectordb = {"task_id": task_id, "status": "Querying vector database for expert candidates...", "level": "INFO"}
        publish_message_to_channel("debate_progress", payload_vectordb)
        time.sleep(0.5)

        expert_candidates = query_expert_embeddings(query_embedding, n_results=3)
        payload_experts = {
            "task_id": task_id,
            "status": f"Retrieved {len(expert_candidates)} expert candidates from vector DB.",
            "level": "INFO"
        }
        publish_message_to_channel("debate_progress", payload_experts)
        expert_candidates_str = json.dumps(expert_candidates, indent=2)
        logger.debug(f"[Task ID: {task_id}] Expert candidates from vector DB:\n{expert_candidates_str}")
        time.sleep(0.5)

        persona_prompt = generate_mock_persona_prompt(query)
        payload_persona = {"task_id": task_id, "status": f"Mock persona generated: '{persona_prompt}'", "level": "INFO"}
        publish_message_to_channel("debate_progress", payload_persona)
        time.sleep(0.5)

        # Wrapper for LightAgent's publish_progress
        def light_agent_progress_publisher(agent_internal_id: str, status_message: str):
            # The LightAgent's publish_progress was Callable[[str, str], None]
            # agent_internal_id is the task_id LightAgent generates.
            # status_message is the progress message from LightAgent.
            progress_update = {
                "task_id": task_id, # Main Celery Task ID
                "status": f"LightAgent ({agent_internal_id}): {status_message}", # Prepend context
                "level": "INFO", # Assuming INFO level for agent's internal progress
                "agent_task_id": agent_internal_id # Include agent's own task_id if it's useful
            }
            if not publish_message_to_channel("debate_progress", progress_update):
                logger.error(f"[Task ID: {task_id}] Failed to publish LightAgent progress: '{status_message}'")

        light_agent = LightAgent(publish_progress=light_agent_progress_publisher)
        light_agent_output = light_agent.run_reasoning(persona_prompt, query)

        final_result_content = f"AI Agent Core processed query: '{query}'.\nExpert Candidates: {expert_candidates_str}\nLightAgent Output: {light_agent_output}"

        set_cache(cache_key, final_result_content, ex=600)
        payload_cached_done = {"task_id": task_id, "status": f"Query result cached for key: {cache_key}", "level": "INFO"}
        publish_message_to_channel("debate_progress", payload_cached_done)

        final_result = final_result_content
        payload_final = {"task_id": task_id, "status": final_result, "level": "SUCCESS"}
        publish_message_to_channel("debate_progress", payload_final)
        logger.info(f"[Task ID: {task_id}] Successfully processed query: {query}")
        return final_result

    except Exception as e:
        error_message = f"Error processing query '{query}': {str(e)}"
        logger.error(f"[Task ID: {task_id}] {error_message}", exc_info=True)

        payload_error = {
            "task_id": task_id,
            "status": "An error occurred during processing.",
            "level": "ERROR",
            "error": str(e)
        }
        if not publish_message_to_channel("debate_progress", payload_error):
            logger.error(f"[Task ID: {task_id}] Failed to publish error progress.")
        raise