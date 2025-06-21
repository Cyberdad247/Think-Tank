import pytest
from think_tank_monorepo.packages.ai_agent_core.persona_system import (
    generate_mock_persona_prompt,
    get_mock_personas,
    MOCK_PERSONAS_COUNT
)

def test_generate_mock_persona_prompt():
    query = "What is the future of AI?"
    prompt = generate_mock_persona_prompt(query)

    assert f"You are a helpful AI assistant providing a mock persona response to the query: '{query}'." in prompt
    assert "Consider the following aspects:" in prompt
    assert "Ethical implications" in prompt # Example aspect

def test_get_mock_personas():
    query = "Discuss climate change solutions."
    personas = get_mock_personas(query)

    assert len(personas) == MOCK_PERSONAS_COUNT
    for i, persona_str in enumerate(personas):
        assert f"Mock Persona {i+1} responding to query: '{query}'" in persona_str
        assert "This is a simulated response." in persona_str

def test_get_mock_personas_default_count():
    # Ensures it returns the default number of personas
    query = "Test query"
    personas = get_mock_personas(query)
    assert len(personas) == MOCK_PERSONAS_COUNT

def test_get_mock_personas_varying_queries():
    query1 = "Query number one"
    personas1 = get_mock_personas(query1)
    assert query1 in personas1[0]

    query2 = "Another different query"
    personas2 = get_mock_personas(query2)
    assert query2 in personas2[0]
    assert query1 not in personas2[0] # Ensure query is correctly substituted
