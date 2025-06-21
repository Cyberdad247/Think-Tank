import pytest
from unittest.mock import patch, MagicMock
import os

# Module to be tested
from think_tank_monorepo.packages.data_storage import supabase_client

@pytest.fixture(autouse=True)
def reset_supabase_client_module_state():
    """Reset the supabase client instance in the module before/after each test."""
    # Store original values if any complex state needs restoring beyond just the client var
    original_client = supabase_client.supabase
    yield
    supabase_client.supabase = original_client # Restore original client
    # If os.environ was manipulated for specific tests, ensure it's cleaned up if not using patch.dict

@patch(f'{supabase_client.__name__}.create_client')
def test_supabase_client_initialization_success(mock_create_client, caplog):
    mock_supabase_instance = MagicMock()
    mock_create_client.return_value = mock_supabase_instance

    with patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test_key"}):
        # Reload the module to trigger initialization logic with patched env vars and create_client
        # This is one way to test module-level initialization code.
        # Be cautious with module reloading if it has complex side effects or state.
        import importlib
        importlib.reload(supabase_client)

    assert supabase_client.supabase is mock_supabase_instance
    mock_create_client.assert_called_once_with("https://test.supabase.co", "test_key")
    assert "Supabase client initialized successfully." in caplog.text

@patch(f'{supabase_client.__name__}.create_client')
def test_supabase_client_initialization_missing_vars(mock_create_client, caplog):
    # Ensure client is None if vars are missing
    with patch.dict(os.environ, {}, clear=True): # Clear supabase related env vars
        import importlib
        importlib.reload(supabase_client)

    assert supabase_client.supabase is None
    mock_create_client.assert_not_called()
    assert "Supabase URL or Key not provided in environment variables. Supabase client not initialized." in caplog.text

@patch(f'{supabase_client.__name__}.create_client')
def test_supabase_client_initialization_failure_exception(mock_create_client, caplog):
    mock_create_client.side_effect = Exception("Connection timeout")

    with patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test_key"}):
        import importlib
        importlib.reload(supabase_client)

    assert supabase_client.supabase is None
    mock_create_client.assert_called_once_with("https://test.supabase.co", "test_key")
    assert "Failed to initialize Supabase client: Connection timeout" in caplog.text


class TestSupabaseFunctions:

    @pytest.fixture
    def mock_sb_client(self):
        """Fixture to provide a mock Supabase client instance and patch it into the module."""
        mock_client_instance = MagicMock()
        with patch.object(supabase_client, 'supabase', mock_client_instance):
            yield mock_client_instance

    def test_get_user_data_client_unavailable(self, caplog):
        with patch.object(supabase_client, 'supabase', None): # Simulate client not initialized
            result = supabase_client.get_user_data("user_123")
        assert result is None
        assert "Supabase client not available. Cannot get user data." in caplog.text

    def test_get_user_data_success(self, mock_sb_client):
        # This function in supabase_client.py is currently a simulation
        # So we test that it returns the placeholder data.
        # If it made actual client calls, we'd mock those like:
        # mock_sb_client.from_().select().eq().execute.return_value = MagicMock(data=[{"id": "user_123", ...}])

        user_id = "user_test_id"
        result = supabase_client.get_user_data(user_id)

        assert result == {"user_id": user_id, "name": "John Doe", "role": "developer"}
        # No actual client calls are made in the current placeholder implementation to assert here

    def test_get_expert_data_with_embedding_success(self, mock_sb_client):
        expert_id = "expert_test_id"
        result = supabase_client.get_expert_data_with_embedding(expert_id)

        assert result["expert_id"] == expert_id
        assert "name" in result
        assert "embedding" in result
        assert len(result["embedding"]) == 1536 # As per current mock

    def test_store_embedding_success(self, mock_sb_client):
        data = {"name": "Test Entity"}
        embedding = [0.05] * 1536
        table_name = "test_embeddings"

        result = supabase_client.store_embedding(data, embedding, table_name)
        assert result is True # Current mock returns True

    def test_retrieve_similar_embeddings_success(self, mock_sb_client):
        query_embedding = [0.03] * 1536
        table_name = "test_embeddings"

        result = supabase_client.retrieve_similar_embeddings(query_embedding, table_name, limit=3)
        assert isinstance(result, list)
        # Current mock returns 2 items
        assert len(result) == 2
        if result:
            assert "name" in result[0]
            assert "score" in result[0]

# Note: These tests primarily cover the placeholder logic in supabase_client.py.
# If actual Supabase calls were implemented, the mocks for chained methods like
# mock_sb_client.from_("table").select("*").eq("id", user_id).execute()
# would need to be more detailed, often requiring nested MagicMocks.
# e.g., mock_from = mock_sb_client.from_.return_value
#       mock_select = mock_from.select.return_value
#       mock_eq = mock_select.eq.return_value
#       mock_eq.execute.return_value = desired_response
#
# Reloading the module (importlib.reload) is a powerful way to test module-level
# initialization code but should be used carefully.
# For function tests, directly patching `supabase_client.supabase` is often cleaner.
