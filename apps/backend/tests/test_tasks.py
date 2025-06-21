import pytest
from unittest.mock import patch, MagicMock, call
import json

# Import the Celery app instance and the task to be tested
from apps.backend.main import celery_app # To ensure Celery app context is available if needed
from apps.backend.tasks import process_query

# Configure Celery for testing (e.g., run tasks eagerly)
# This should ideally be done once, perhaps in a conftest.py or test setup
celery_app.conf.update(CELERY_TASK_ALWAYS_EAGER=True)

@pytest.fixture
def mock_dependencies():
    """Fixture to mock all external dependencies for process_query task."""
    with patch('apps.backend.tasks.get_cache') as mock_get_cache, \
         patch('apps.backend.tasks.set_cache') as mock_set_cache, \
         patch('apps.backend.tasks.query_expert_embeddings') as mock_query_experts, \
         patch('apps.backend.tasks.generate_mock_persona_prompt') as mock_gen_persona, \
         patch('apps.backend.tasks.LightAgent') as MockLightAgent, \
         patch('apps.backend.tasks.publish_message_to_channel') as mock_publish:

        # Setup default return values for mocks
        mock_get_cache.return_value = None # Default to cache miss
        mock_query_experts.return_value = [{"id": "expert1", "name": "Dr. Expert", "domain": "AI", "document": "doc", "distance": 0.1}]
        mock_gen_persona.return_value = "Mocked Persona Prompt"

        mock_light_agent_instance = MockLightAgent.return_value
        mock_light_agent_instance.run_reasoning.return_value = "Mocked LightAgent Output"

        yield {
            "get_cache": mock_get_cache,
            "set_cache": mock_set_cache,
            "query_experts": mock_query_experts,
            "gen_persona": mock_gen_persona,
            "LightAgent": MockLightAgent, # Class
            "light_agent_instance": mock_light_agent_instance, # Instance
            "publish": mock_publish
        }

class TestProcessQueryTask:

    def test_process_query_success_cache_miss(self, mock_dependencies):
        query = "test query for AI ethics"

        # Call the task directly for easier debugging and control
        # .s() creates a signature, .apply() executes it.
        # Using task_always_eager means it runs locally.
        result = process_query.apply(args=[query]).get() # .get() to get the actual return value

        # Assertions
        mock_dependencies["get_cache"].assert_called_once_with(f"query_result:{query}")
        mock_dependencies["query_experts"].assert_called_once()
        mock_dependencies["gen_persona"].assert_called_once_with(query)
        mock_dependencies["LightAgent"].assert_called_once() # Check constructor
        mock_dependencies["light_agent_instance"].run_reasoning.assert_called_once_with("Mocked Persona Prompt", query)

        expected_final_content_substring_experts = '"name": "Dr. Expert"' # Part of expert_candidates_str
        expected_final_content_substring_agent = "Mocked LightAgent Output"

        # Check set_cache call
        # The first argument to set_cache is the key, the second is the value.
        # We expect the value to contain substrings of the mocked outputs.
        args, kwargs = mock_dependencies["set_cache"].call_args
        assert args[0] == f"query_result:{query}"
        assert expected_final_content_substring_experts in args[1]
        assert expected_final_content_substring_agent in args[1]
        assert kwargs['ex'] == 600

        # Check publish calls (simplified check, could be more specific)
        assert mock_dependencies["publish"].call_count >= 5 # Initial, no cache, vector query, experts, persona, cached, final

        # Check the first publish call for "Query received"
        first_publish_call_args = mock_dependencies["publish"].call_args_list[0]
        args_payload = first_publish_call_args[0][1] # ("debate_progress", payload_dict)
        assert args_payload["status"] == f"Query received: '{query}'"
        assert args_payload["level"] == "INFO"

        # Check the last publish call for "SUCCESS"
        last_publish_call_args = mock_dependencies["publish"].call_args_list[-1]
        args_payload_last = last_publish_call_args[0][1]
        assert args_payload_last["level"] == "SUCCESS"
        assert expected_final_content_substring_experts in args_payload_last["status"]
        assert expected_final_content_substring_agent in args_payload_last["status"]

        assert expected_final_content_substring_experts in result
        assert expected_final_content_substring_agent in result

    def test_process_query_cache_hit(self, mock_dependencies):
        query = "cached query"
        cached_value = "This is a cached result for 'cached query'."
        mock_dependencies["get_cache"].return_value = cached_value

        result = process_query.apply(args=[query]).get()

        assert result == f"AI Agent Core processed query: '{query}'.\n(Cached Result) {cached_value}"
        mock_dependencies["get_cache"].assert_called_once_with(f"query_result:{query}")

        # Ensure other processing steps were skipped
        mock_dependencies["query_experts"].assert_not_called()
        mock_dependencies["LightAgent"].assert_not_called()
        mock_dependencies["set_cache"].assert_not_called()

        # Check publish calls
        # Expected calls: Initial "Query received", then "Retrieved from cache"
        assert mock_dependencies["publish"].call_count == 2

        second_publish_call_args = mock_dependencies["publish"].call_args_list[1]
        args_payload = second_publish_call_args[0][1]
        assert args_payload["status"] == "Retrieved query result from cache."

    def test_process_query_processing_error(self, mock_dependencies):
        query = "query that causes error"
        error_message = "Vector DB unavailable"
        mock_dependencies["query_experts"].side_effect = Exception(error_message)

        with pytest.raises(Exception, match=error_message):
            process_query.apply(args=[query]).get() # Exception should propagate

        # Check that an error message was published
        # The publish calls would be: Initial, No Cache, Querying Vector DB, then Error
        # The last call should contain the error.
        # This depends on how many publish calls happen before the error.
        # For query_experts failing: Query Received, Query not in cache, Querying vector DB, Error.
        assert mock_dependencies["publish"].call_count >= 4

        last_publish_call_args = mock_dependencies["publish"].call_args_list[-1]
        args_channel, args_payload = last_publish_call_args[0]

        assert args_channel == "debate_progress"
        assert args_payload["status"] == "An error occurred during processing."
        assert args_payload["level"] == "ERROR"
        assert error_message in args_payload["error"]

        # Ensure set_cache was not called in case of error
        mock_dependencies["set_cache"].assert_not_called()

    def test_light_agent_publish_progress_wrapper(self, mock_dependencies):
        query = "test light agent wrapper"
        task_id_from_celery = "celery_task_123" # Assume this would be the actual task_id

        # Mock self.request.id for direct function call if not using .apply()
        # However, with .apply(task_id=...) or if task_always_eager sets it, it's fine.
        # For this test, we'll check the arguments to LightAgent constructor.

        # We need to capture the function passed to LightAgent
        # process_query(query) # Direct call for this specific check might be easier if .apply().get() is tricky for capturing

        # Simulate the task running, which will instantiate LightAgent
        # We need to get the actual function passed to LightAgent

        # Call the task. The MockLightAgent will be instantiated.
        # The `publish_progress` argument to its constructor is what we want to test.
        with patch.object(process_query, 'request', MagicMock(id=task_id_from_celery)): # Mock self.request.id
             process_query(query)


        # Get the LightAgent constructor call
        assert mock_dependencies["LightAgent"].call_count == 1
        args, kwargs = mock_dependencies["LightAgent"].call_args

        # The first positional argument to LightAgent constructor is publish_progress
        light_agent_progress_publisher_func = args[0]

        # Now call this captured function as LightAgent would
        agent_internal_id = "agent_sub_task_456"
        agent_message = "Agent reasoning step 1"
        light_agent_progress_publisher_func(agent_internal_id, agent_message)

        # Check if publish_message_to_channel was called correctly by the wrapper
        # This will be the last call after all other publish calls from process_query itself
        # (Query received, no cache, querying, experts retrieved, persona)
        # So, this specific call check needs to be robust or isolated.

        # For simplicity, let's check the *last* call to publish_message_to_channel
        # This assumes the wrapper's call is the last one in this test flow.
        # A more robust test would isolate the wrapper.

        # Get the last call to the main publish function
        last_publish_call = mock_dependencies["publish"].call_args_list[-1]
        channel_arg, payload_arg = last_publish_call[0]

        assert channel_arg == "debate_progress"
        assert payload_arg["task_id"] == task_id_from_celery # Check it uses the main Celery task_id
        assert f"LightAgent ({agent_internal_id}): {agent_message}" in payload_arg["status"]
        assert payload_arg["level"] == "INFO"
        assert payload_arg["agent_task_id"] == agent_internal_id
```
