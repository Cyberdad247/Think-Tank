import pytest
from unittest.mock import MagicMock, call
from think_tank_monorepo.packages.ai_agent_core.light_agent import LightAgent

def test_light_agent_run_reasoning():
    # 1. Mock the publish_progress callable
    mock_publish_progress = MagicMock()

    # 2. Instantiate LightAgent with the mock callable
    agent = LightAgent(publish_progress=mock_publish_progress)

    # 3. Call run_reasoning
    persona_prompt = "Act as a cautious advisor."
    query = "Should we invest in XYZ?"
    result = agent.run_reasoning(persona_prompt, query)

    # 4. Assert that publish_progress was called with expected messages
    #    We need to check the second argument of each call (the message string)
    #    The first argument is a task_id generated internally by LightAgent, so we can't predict it exactly,
    #    but we can check its type or that it was called.

    calls = mock_publish_progress.call_args_list
    assert len(calls) == 3 # Expecting 3 calls

    # Check messages (second argument of each call)
    assert calls[0][0][1] == "Starting single-round reasoning..."
    assert calls[1][0][1] == "Reasoning complete. Generating response..."
    assert calls[2][0][1] == "Final response generated."

    # Check that the first argument (task_id) was a string for each call
    assert isinstance(calls[0][0][0], str)
    assert isinstance(calls[1][0][0], str)
    assert isinstance(calls[2][0][0], str)

    # 5. Assert that the returned string contains the persona prompt and query
    assert persona_prompt in result
    assert query in result
    assert "LightAgent's simplified reasoning output" in result
    assert "Mock Debate Result" in result
    assert "After a brief internal deliberation" in result # Part of the mock output
