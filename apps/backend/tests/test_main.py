import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Ensure environment variables are loaded for tests if main.py relies on them at import time
# from dotenv import load_dotenv
# load_dotenv() # Potentially load a specific .env.test if needed

# We need to make sure that when `apps.backend.main` is imported,
# it uses a mockable version of get_redis_client to avoid actual Redis connections.
# This is tricky if get_redis_client is called at the module level in main.py.
# One common pattern is to allow dependency injection or to patch at the source.

# For `get_redis_client` called at module level in main.py:
# Patch it *before* importing the app.
# This mock_redis_client will be used by the app instance.
mock_redis_instance = MagicMock()
mock_redis_instance.pubsub.return_value = MagicMock() # Mock pubsub object

# Patch 'get_redis_client' from where it's defined and used.
# Assuming 'think_tank_monorepo.packages.cache_queue.redis_client.get_redis_client' is the source
# and 'apps.backend.main.get_redis_client' is how it's imported/used in main.py.
# The patch should target where it's *looked up*, not where it's defined if different.
# If main.py imports it as `from think_tank_monorepo.packages.cache_queue.redis_client import get_redis_client`,
# then patch 'apps.backend.main.get_redis_client'.

# Patch 'get_redis_url' as well, as it's used for Celery config.
mock_get_redis_url = MagicMock(return_value="redis://mockredis:6379/0")

with patch('apps.backend.main.get_redis_client', return_value=mock_redis_instance) as patched_get_redis_client, \
     patch('apps.backend.main.get_redis_url', new=mock_get_redis_url) as patched_get_redis_url:

    # Now import the app after patches are active
    from apps.backend.main import app, celery_app

client = TestClient(app)

# Test suite for the main FastAPI application
class TestMainAPI:

    def test_read_root_health_check_not_implemented(self):
        # Assuming no "/" route exists, FastAPI returns 404
        # If you add a root health check endpoint, this test would change.
        response = client.get("/")
        assert response.status_code == 404

    # Tests for /api/debate endpoint
    @patch.object(celery_app, 'send_task')
    def test_debate_endpoint_valid_query(self, mock_send_task):
        mock_task_id = "test-task-id"
        mock_send_task.return_value = MagicMock(id=mock_task_id)

        response = client.post("/api/debate", json={"query": "Test query about AI ethics"})

        assert response.status_code == 200
        json_response = response.json()
        assert json_response["message"] == "Query received, processing started"
        assert json_response["task_id"] == mock_task_id
        mock_send_task.assert_called_once_with("tasks.process_query", args=["Test query about AI ethics"])

    def test_debate_endpoint_missing_query(self):
        response = client.post("/api/debate", json={})
        assert response.status_code == 400
        assert "Field 'query' is missing" in response.json()["detail"]

    def test_debate_endpoint_empty_query(self):
        response = client.post("/api/debate", json={"query": "  "})
        assert response.status_code == 400
        assert "Field 'query' is missing" in response.json()["detail"]

    def test_debate_endpoint_query_not_string(self):
        response = client.post("/api/debate", json={"query": 123})
        assert response.status_code == 400
        assert "Field 'query' is missing" in response.json()["detail"] # Or a more specific type error

    @patch.object(celery_app, 'send_task')
    def test_debate_endpoint_celery_error(self, mock_send_task):
        from celery.exceptions import CeleryError
        mock_send_task.side_effect = CeleryError("Broker connection failed")

        response = client.post("/api/debate", json={"query": "A valid query"})

        assert response.status_code == 500
        assert "Could not send task to broker" in response.json()["detail"]

    # Tests for /api/debate/stream endpoint
    def test_debate_stream_endpoint_setup(self):
        # This test focuses on the setup and subscription, not the streaming content itself.
        # The actual redis_client used by the app is already mocked via patched_get_redis_client

        mock_pubsub_instance = MagicMock()
        mock_pubsub_instance.listen.return_value = [] # Simulate no messages for setup test

        # Ensure the global mock_redis_instance.pubsub() returns our new mock_pubsub_instance
        # This is a bit indirect; ideally, the app's shared_redis_client would be directly patchable
        # or injectable for testing the stream handler.
        # The current patch on get_redis_client means shared_redis_client in main.py *is* mock_redis_instance.
        mock_redis_instance.pubsub.return_value = mock_pubsub_instance

        response = client.get("/api/debate/stream") # Query param is optional for stream setup

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

        # Check if pubsub was called on the (mocked) shared_redis_client
        mock_redis_instance.pubsub.assert_called_once()
        # Check if subscribe was called on the pubsub object
        mock_pubsub_instance.subscribe.assert_called_once_with("debate_progress")
        # Unsubscribe and close are called in finally, so listen must be called too
        mock_pubsub_instance.listen.assert_called_once()
        mock_pubsub_instance.unsubscribe.assert_called_once_with("debate_progress")
        mock_pubsub_instance.close.assert_called_once()


# To run these tests:
# Ensure pytest and httpx are installed.
# From the root of the monorepo, you might run:
# PYTHONPATH=. pytest apps/backend/tests/test_main.py
# (Setting PYTHONPATH ensures imports like 'apps.backend.main' work)
# Or configure pytest via pytest.ini or pyproject.toml for path handling.
# Example pytest.ini:
# [pytest]
# pythonpath = .
# asyncio_mode = auto (if using async TestClient with pytest-asyncio)
