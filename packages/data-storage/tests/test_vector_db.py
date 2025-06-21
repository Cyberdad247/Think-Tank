import pytest
from unittest.mock import patch, MagicMock, ANY
import os

# Module to be tested
from think_tank_monorepo.packages.data_storage import vector_db

# Fixture to automatically reset relevant module-level variables for test isolation
@pytest.fixture(autouse=True)
def reset_vector_db_module_state():
    # Store original values if necessary, though here we mainly reset them
    original_client = vector_db.client
    original_collection = vector_db.expert_collection
    original_db_path = vector_db.CHROMA_PERSIST_PATH # Though this is read from env

    yield # Test runs

    # Restore original state or known clean state
    vector_db.client = original_client
    vector_db.expert_collection = original_collection
    vector_db.CHROMA_PERSIST_PATH = original_db_path
    # If os.environ was manipulated, ensure it's cleaned up by tests using patch.dict or similar


# Mock the chromadb clients and collection for all tests in this file
@pytest.fixture
def mock_chroma_env():
    with patch(f'{vector_db.__name__}.chromadb.Client') as MockChromaClient, \
         patch(f'{vector_db.__name__}.chromadb.PersistentClient') as MockPersistentClient, \
         patch.object(vector_db, 'MockEmbeddingFunction', autospec=True) as MockEmbeddingFunc: # Mock the class itself

        mock_client_instance = MagicMock()
        mock_collection_instance = MagicMock()

        # Default setup: MockChromaClient returns the instance
        MockChromaClient.return_value = mock_client_instance
        MockPersistentClient.return_value = mock_client_instance # Same mock for persistent for simplicity here

        # When client.get_or_create_collection is called, return our mock_collection_instance
        mock_client_instance.get_or_create_collection.return_value = mock_collection_instance

        # Patch the module's client and expert_collection to use these mocks *after* module load
        # This handles the module-level initialization.
        # For more robust testing of initialization, module reload with patched env might be needed (see below)
        vector_db.client = mock_client_instance
        vector_db.expert_collection = mock_collection_instance

        # Mock the embedding function instance if needed, or its __call__ method
        mock_embedding_function_instance = MockEmbeddingFunc.return_value
        mock_embedding_function_instance.return_value = [[0.1]*1536 for _ in range(3)] # Mock return of __call__

        yield {
            "MockChromaClient": MockChromaClient,
            "MockPersistentClient": MockPersistentClient,
            "mock_client_instance": mock_client_instance,
            "mock_collection_instance": mock_collection_instance,
            "MockEmbeddingFunc": MockEmbeddingFunc, # The class mock
            "mock_embedding_function_instance": mock_embedding_function_instance # The instance mock
        }

class TestVectorDBInitialization:
    # Test client init with and without CHROMA_PERSIST_PATH
    @patch(f'{vector_db.__name__}.chromadb.PersistentClient')
    @patch(f'{vector_db.__name__}.chromadb.Client')
    def test_client_initialization_persistent(self, MockBasicClient, MockPersistentClient, caplog):
        mock_persistent_instance = MagicMock()
        MockPersistentClient.return_value = mock_persistent_instance

        with patch.dict(os.environ, {"CHROMA_PERSIST_PATH": "./test_chroma_data"}):
            import importlib
            importlib.reload(vector_db) # Reload to trigger client init with env var

        MockPersistentClient.assert_called_once_with(path="./test_chroma_data")
        MockBasicClient.assert_not_called()
        assert vector_db.client is mock_persistent_instance
        assert "Using persistent ChromaDB client with path: ./test_chroma_data" in caplog.text

    @patch(f'{vector_db.__name__}.chromadb.PersistentClient')
    @patch(f'{vector_db.__name__}.chromadb.Client')
    def test_client_initialization_in_memory(self, MockBasicClient, MockPersistentClient, caplog):
        mock_basic_instance = MagicMock()
        MockBasicClient.return_value = mock_basic_instance

        with patch.dict(os.environ, {}, clear=True): # Ensure CHROMA_PERSIST_PATH is not set
             import importlib
             importlib.reload(vector_db)

        MockBasicClient.assert_called_once()
        MockPersistentClient.assert_not_called()
        assert vector_db.client is mock_basic_instance
        assert "Using in-memory ChromaDB client (CHROMA_PERSIST_PATH not set)" in caplog.text

    @patch(f'{vector_db.__name__}.chromadb.PersistentClient', side_effect=Exception("Disk full"))
    @patch(f'{vector_db.__name__}.chromadb.Client')
    def test_client_initialization_persistent_failure_fallback(self, MockBasicClient, MockPersistentClient, caplog):
        mock_basic_instance = MagicMock()
        MockBasicClient.return_value = mock_basic_instance

        with patch.dict(os.environ, {"CHROMA_PERSIST_PATH": "./test_chroma_data_fail"}):
            import importlib
            importlib.reload(vector_db)

        MockPersistentClient.assert_called_once_with(path="./test_chroma_data_fail")
        assert "Failed to initialize persistent ChromaDB client" in caplog.text
        assert "Disk full" in caplog.text
        MockBasicClient.assert_called_once() # Fallback occurred
        assert vector_db.client is mock_basic_instance
        assert "Using in-memory ChromaDB client as fallback" in caplog.text


    # Test collection initialization
    def test_collection_initialization(self, mock_chroma_env, caplog):
        # This test relies on the mock_chroma_env fixture to have already
        # mocked client.get_or_create_collection.
        # We call importlib.reload to ensure the module-level code runs with these mocks.
        import importlib
        importlib.reload(vector_db)

        mock_chroma_env["mock_client_instance"].get_or_create_collection.assert_called_once_with(
            name="expert_embeddings",
            embedding_function=ANY # MockEmbeddingFunction instance
        )
        assert vector_db.expert_collection is mock_chroma_env["mock_collection_instance"]
        assert "Successfully got or created Chroma collection: expert_embeddings" in caplog.text

    @patch(f'{vector_db.__name__}.chromadb.Client') # Assume in-memory for this failure
    def test_collection_initialization_failure(self, MockBasicClient, caplog):
        mock_client_instance = MagicMock()
        MockBasicClient.return_value = mock_client_instance
        mock_client_instance.get_or_create_collection.side_effect = Exception("Chroma init failed")

        with patch.dict(os.environ, {}, clear=True): # In-memory
            import importlib
            # Patch the client instance within the module *before* reloading,
            # so the reloaded module uses this specific mock for the get_or_create_collection call.
            with patch.object(vector_db, 'client', mock_client_instance):
                 importlib.reload(vector_db)

        assert "Error getting or creating collection 'expert_embeddings': Chroma init failed" in caplog.text
        assert "ChromaDB collection 'expert_embeddings' could not be initialized." in caplog.text
        assert vector_db.expert_collection is None


class TestVectorDBFunctions:

    def test_initialize_expert_embeddings(self, mock_chroma_env):
        mock_collection = mock_chroma_env["mock_collection_instance"]
        # Simulate collection.get returning no existing items for simplicity of this part
        mock_collection.get.return_value = {'ids': []}

        vector_db.initialize_expert_embeddings()

        mock_collection.get.assert_called_once_with(ids=[d["id"] for d in vector_db.MOCK_EXPERT_DATA])

        # Check that add was called with documents, metadatas, and ids
        # The actual embeddings are generated by Chroma from documents.
        expected_ids = [d["id"] for d in vector_db.MOCK_EXPERT_DATA]
        expected_documents = [d["document"] for d in vector_db.MOCK_EXPERT_DATA]
        expected_metadatas = [d["metadata"] for d in vector_db.MOCK_EXPERT_DATA]

        mock_collection.add.assert_called_once_with(
            documents=expected_documents,
            metadatas=expected_metadatas,
            ids=expected_ids
        )

    def test_initialize_expert_embeddings_some_exist(self, mock_chroma_env):
        mock_collection = mock_chroma_env["mock_collection_instance"]
        # Simulate one item already exists
        existing_id = vector_db.MOCK_EXPERT_DATA[0]["id"]
        mock_collection.get.return_value = {'ids': [existing_id]}

        vector_db.initialize_expert_embeddings()

        # Check that 'add' was called only with non-existing items
        args, kwargs = mock_collection.add.call_args
        added_ids = kwargs['ids']
        assert existing_id not in added_ids
        assert len(added_ids) == len(vector_db.MOCK_EXPERT_DATA) - 1


    def test_initialize_expert_embeddings_collection_unavailable(self, mock_chroma_env, caplog):
        with patch.object(vector_db, 'expert_collection', None): # Simulate collection init failure
            vector_db.initialize_expert_embeddings()
        assert "Chroma expert_collection not available. Cannot initialize expert embeddings." in caplog.text
        mock_chroma_env["mock_collection_instance"].add.assert_not_called()


    def test_query_expert_embeddings_success(self, mock_chroma_env):
        mock_collection = mock_chroma_env["mock_collection_instance"]
        mock_query_text = "ai ethics"

        # Mock the return value of collection.query
        mock_results = {
            "ids": [["exp1_dev_ops", "exp2_ml_engineer"]],
            "metadatas": [[
                {"name": "Alice Developer", "domain": "DevOps"},
                {"name": "Bob Machinelearning", "domain": "Machine Learning"}
            ]],
            "documents": [[
                "Expert in CI/CD...",
                "Specializes in NLP..."
            ]],
            "distances": [[0.1, 0.2]]
        }
        mock_collection.query.return_value = mock_results

        results = vector_db.query_expert_embeddings(mock_query_text, n_results=2)

        mock_collection.query.assert_called_once_with(
            query_texts=[mock_query_text],
            n_results=2,
            include=['metadatas', 'distances', 'documents']
        )

        assert len(results) == 2
        assert results[0]["id"] == "exp1_dev_ops"
        assert results[0]["name"] == "Alice Developer"
        assert results[0]["document"] == "Expert in CI/CD..."
        assert results[0]["distance"] == 0.1
        assert results[1]["id"] == "exp2_ml_engineer"

    def test_query_expert_embeddings_collection_unavailable(self, mock_chroma_env, caplog):
        with patch.object(vector_db, 'expert_collection', None):
            results = vector_db.query_expert_embeddings("test query")
        assert results == []
        assert "Chroma expert_collection not available. Cannot query expert embeddings." in caplog.text
        mock_chroma_env["mock_collection_instance"].query.assert_not_called()

    def test_query_expert_embeddings_chroma_error(self, mock_chroma_env, caplog):
        mock_collection = mock_chroma_env["mock_collection_instance"]
        mock_collection.query.side_effect = Exception("Chroma query failed")

        results = vector_db.query_expert_embeddings("test query error")
        assert results == []
        assert "Error querying Chroma DB: Chroma query failed" in caplog.text

# Note: `importlib.reload` is used to test module-level initialization code that
# depends on environment variables. This is a common pattern for such tests.
# Ensure the `autouse=True` fixture properly resets state between tests that use reload.
# For functions that use the module-level client/collection, patching these
# (e.g., with `patch.object(vector_db, 'expert_collection', new_mock)`) is often sufficient
# if the module doesn't need a full reload for that specific test.
# The mock_chroma_env fixture already patches these module level variables after initial load.
# The reload tests are more for the *initialization* of those variables.
