import pytest
from unittest.mock import patch, MagicMock, ANY
import os
import json
import redis # For redis.exceptions.RedisError

# Module to be tested
from think_tank_monorepo.packages.cache_queue import redis_client

# Before each test, reset the shared client in the module to ensure isolation
@pytest.fixture(autouse=True)
def reset_shared_client():
    redis_client._shared_redis_client = None
    redis_client._redis_url_config = None
    yield # Test runs here
    redis_client._shared_redis_client = None
    redis_client._redis_url_config = None


class TestGetRedisClient:
    @patch.object(redis.StrictRedis, 'from_url')
    def test_get_redis_client_singleton(self, mock_from_url):
        mock_instance = MagicMock()
        mock_instance.ping = MagicMock()
        mock_from_url.return_value = mock_instance

        with patch.dict(os.environ, {"REDIS_URL": "redis://testhost:1234/1"}, clear=True):
            client1 = redis_client.get_redis_client()
            client2 = redis_client.get_redis_client()

        assert client1 is client2
        assert client1 is mock_instance
        mock_from_url.assert_called_once_with("redis://testhost:1234/1", decode_responses=True)
        mock_instance.ping.assert_called_once()

    @patch.object(redis.StrictRedis, 'from_url')
    def test_get_redis_client_env_vars_priority(self, mock_from_url, caplog):
        mock_instance = MagicMock()
        mock_instance.ping = MagicMock()
        mock_from_url.return_value = mock_instance

        # Test REDIS_URL
        with patch.dict(os.environ, {"REDIS_URL": "redis://urlhost:6379/0"}, clear=True):
            redis_client.get_redis_client()
            mock_from_url.assert_called_with("redis://urlhost:6379/0", decode_responses=True)
            assert "Using Redis URL from REDIS_URL environment variable" in caplog.text

        redis_client._shared_redis_client = None # Reset for next call
        redis_client._redis_url_config = None
        mock_from_url.reset_mock()
        caplog.clear()

        # Test REDIS_HOST, REDIS_PORT, REDIS_DB
        with patch.dict(os.environ, {"REDIS_HOST": "envhost", "REDIS_PORT": "1234", "REDIS_DB": "2"}, clear=True):
            redis_client.get_redis_client()
            mock_from_url.assert_called_with("redis://envhost:1234/2", decode_responses=True)
            assert "REDIS_URL not found. Using components" in caplog.text
            assert "Host='envhost', Port='1234', DB='2'" in caplog.text

        redis_client._shared_redis_client = None
        redis_client._redis_url_config = None
        mock_from_url.reset_mock()
        caplog.clear()

        # Test defaults
        with patch.dict(os.environ, {}, clear=True): # No relevant env vars
            redis_client.get_redis_client()
            mock_from_url.assert_called_with("redis://localhost:6379/0", decode_responses=True)
            assert "REDIS_URL not found. Using components" in caplog.text
            assert "(all components are defaults as none were set via env vars REDIS_HOST/PORT/DB)" in caplog.text


    @patch.object(redis.StrictRedis, 'from_url')
    def test_get_redis_client_connection_error(self, mock_from_url, caplog):
        mock_from_url.side_effect = redis.exceptions.ConnectionError("Connection failed")
        with patch.dict(os.environ, {"REDIS_URL": "redis://badhost:1234/1"}, clear=True):
            client = redis_client.get_redis_client()
        assert client is None
        assert "Could not connect to Redis at redis://badhost:1234/1: Connection failed" in caplog.text

    def test_get_redis_url_before_client_init(self):
        with patch.dict(os.environ, {"REDIS_URL": "redis://envurl:1111/3"}, clear=True):
            url = redis_client.get_redis_url()
            assert url == "redis://envurl:1111/3"

        redis_client._redis_url_config = None # Reset for next test
        with patch.dict(os.environ, {"REDIS_HOST": "envhost", "REDIS_PORT":"2222"}, clear=True):
            url = redis_client.get_redis_url()
            assert url == "redis://envhost:2222/0" # DB defaults to 0


@patch(f'{redis_client.__name__}.get_redis_client') # Patch where get_redis_client is defined
class TestCacheFunctions:

    def test_get_cache_hit(self, mock_get_rc):
        mock_rc_instance = MagicMock()
        mock_rc_instance.get.return_value = '{"key": "value"}'
        mock_get_rc.return_value = mock_rc_instance

        result = redis_client.get_cache("testkey")
        assert result == {"key": "value"}
        mock_rc_instance.get.assert_called_once_with("testkey")

    def test_get_cache_miss(self, mock_get_rc):
        mock_rc_instance = MagicMock()
        mock_rc_instance.get.return_value = None
        mock_get_rc.return_value = mock_rc_instance

        result = redis_client.get_cache("testkey")
        assert result is None
        mock_rc_instance.get.assert_called_once_with("testkey")

    def test_get_cache_redis_error(self, mock_get_rc, caplog):
        mock_rc_instance = MagicMock()
        mock_rc_instance.get.side_effect = redis.exceptions.RedisError("Get failed")
        mock_get_rc.return_value = mock_rc_instance

        result = redis_client.get_cache("testkey")
        assert result is None
        assert "Redis error retrieving from cache for key testkey: Get failed" in caplog.text

    def test_get_cache_json_decode_error(self, mock_get_rc, caplog):
        mock_rc_instance = MagicMock()
        mock_rc_instance.get.return_value = "invalid json"
        mock_get_rc.return_value = mock_rc_instance

        result = redis_client.get_cache("testkey")
        assert result is None
        assert "JSON decoding error for key testkey" in caplog.text

    def test_get_cache_client_unavailable(self, mock_get_rc, caplog):
        mock_get_rc.return_value = None # Simulate client initialization failure
        result = redis_client.get_cache("testkey")
        assert result is None
        assert "Shared Redis client not available. Cannot get cache." in caplog.text


    def test_set_cache_success(self, mock_get_rc):
        mock_rc_instance = MagicMock()
        mock_get_rc.return_value = mock_rc_instance
        value_to_set = {"complex": [1, 2, "data"]}

        result = redis_client.set_cache("testkey", value_to_set, ex=3600)
        assert result is True
        mock_rc_instance.set.assert_called_once_with("testkey", json.dumps(value_to_set), ex=3600)

    def test_set_cache_redis_error(self, mock_get_rc, caplog):
        mock_rc_instance = MagicMock()
        mock_rc_instance.set.side_effect = redis.exceptions.RedisError("Set failed")
        mock_get_rc.return_value = mock_rc_instance

        result = redis_client.set_cache("testkey", {"data": "value"})
        assert result is False
        assert "Redis error setting cache for key testkey: Set failed" in caplog.text

    def test_set_cache_client_unavailable(self, mock_get_rc, caplog):
        mock_get_rc.return_value = None
        result = redis_client.set_cache("testkey", {"data": "value"})
        assert result is False
        assert "Shared Redis client not available. Cannot set cache." in caplog.text


    def test_publish_message_success(self, mock_get_rc):
        mock_rc_instance = MagicMock()
        mock_get_rc.return_value = mock_rc_instance
        message_to_publish = {"event": "update", "id": 123}

        result = redis_client.publish_message("test_channel", message_to_publish)
        assert result is True
        mock_rc_instance.publish.assert_called_once_with("test_channel", json.dumps(message_to_publish))

    def test_publish_message_redis_error(self, mock_get_rc, caplog):
        mock_rc_instance = MagicMock()
        mock_rc_instance.publish.side_effect = redis.exceptions.RedisError("Publish failed")
        mock_get_rc.return_value = mock_rc_instance

        result = redis_client.publish_message("test_channel", {"data": "event"})
        assert result is False
        assert "Redis error publishing to channel test_channel: Publish failed" in caplog.text

    def test_publish_message_client_unavailable(self, mock_get_rc, caplog):
        mock_get_rc.return_value = None
        result = redis_client.publish_message("test_channel", {"data": "event"})
        assert result is False
        assert "Shared Redis client not available. Cannot publish message." in caplog.text

# Note: To run these tests, ensure pytest and necessary mocking libraries are installed.
# Logging capture (caplog) requires pytest.
# Use `pip install pytest redis` (redis for exception types).
# Run with `pytest packages/cache-queue/tests/test_redis_client.py`
# Ensure PYTHONPATH is set if running from a different directory or configure pytest.
# Example pytest.ini:
# [pytest]
# pythonpath = .
# log_cli = true
# log_cli_level = INFO
