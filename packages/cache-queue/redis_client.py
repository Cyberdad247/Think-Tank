import os
import redis
import json
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

_shared_redis_client = None
_redis_url_config = None # To store the URL used for initialization

def get_redis_client(redis_url_override: str = None) -> redis.StrictRedis | None:
    """
    Initializes and returns a shared Redis client instance.
    Uses REDIS_URL environment variable by default.
    Allows overriding the Redis URL for specific use cases (e.g., Celery setup).
    """
    global _shared_redis_client
    global _redis_url_config

    if _shared_redis_client:
        # If a specific URL is requested and it's different from the current client's,
        # it might indicate a need for a different client. However, for a truly shared client,
        # this function should ideally always return the same client once initialized.
        # For simplicity in this refactor, we'll assume the first initialization sets the shared client.
        # If redis_url_override is different and matters, it implies multiple clients might be needed,
        # which contradicts the "single, shared" goal for general use but might be true for Celery broker/backend.
        # Let's log a warning if an override is attempted after initialization with a different URL.
        if redis_url_override and redis_url_override != _redis_url_config:
            logger.warning(f"Redis client already initialized with URL '{_redis_url_config}'. "
                           f"Ignoring override URL '{redis_url_override}' for shared client.")
        return _shared_redis_client

    # Determine Redis URL
    config_source_log = ""
    current_redis_url = redis_url_override
    if current_redis_url:
        config_source_log = f"Using Redis URL from override: {current_redis_url}"
    else:
        current_redis_url = os.getenv("REDIS_URL")
        if current_redis_url:
            config_source_log = f"Using Redis URL from REDIS_URL environment variable: {current_redis_url}"
        else:
            # Fallback to individual host/port/db if REDIS_URL is not set
            REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
            REDIS_PORT_STR = os.environ.get("REDIS_PORT", "6379")
            REDIS_DB_STR = os.environ.get("REDIS_DB", "0")

            try:
                REDIS_PORT = int(REDIS_PORT_STR)
                REDIS_DB = int(REDIS_DB_STR)
            except ValueError:
                logger.error(f"Invalid Redis port ('{REDIS_PORT_STR}') or DB ('{REDIS_DB_STR}'). Using defaults.")
                REDIS_PORT = 6379
                REDIS_DB = 0
                config_source_log = (f"REDIS_URL not found. Invalid host/port/db components provided. "
                                     f"Falling back to default redis://localhost:6379/0")
            else:
                 config_source_log = (f"REDIS_URL not found. Using components: "
                                     f"Host='{REDIS_HOST}', Port='{REDIS_PORT}', DB='{REDIS_DB}'.")

            current_redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
            if REDIS_HOST == "localhost" and REDIS_PORT == 6379 and REDIS_DB == 0 and \
               not os.getenv("REDIS_HOST") and not os.getenv("REDIS_PORT") and not os.getenv("REDIS_DB"):
                config_source_log += " (all components are defaults as none were set via env vars REDIS_HOST/PORT/DB)"

    _redis_url_config = current_redis_url # Store the URL used
    logger.info(config_source_log)
    logger.info(f"Attempting to initialize shared Redis client with resolved URL: {_redis_url_config}")
    try:
        _shared_redis_client = redis.StrictRedis.from_url(_redis_url_config, decode_responses=True)
        _shared_redis_client.ping()
        logger.info(f"Shared Redis client initialized and connected successfully to {_redis_url_config}.")
    except redis.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to Redis at {_redis_url_config}: {e}", exc_info=True)
        _shared_redis_client = None
        _redis_url_config = None # Reset config URL if connection failed
    except ValueError as e: # Handles bad URL format or int conversion errors for port/db if not using from_url
        logger.error(f"Redis configuration error (bad URL or parameters) for {_redis_url_config}: {e}", exc_info=True)
        _shared_redis_client = None
        _redis_url_config = None
    except Exception as e:
        logger.error(f"An unexpected error occurred during shared Redis client initialization with URL {_redis_url_config}: {e}", exc_info=True)
        _shared_redis_client = None
        _redis_url_config = None

    return _shared_redis_client

def get_redis_url():
    """Returns the Redis URL that the shared client was configured with."""
    global _redis_url_config
    # This function is primarily to allow other modules (like Celery config in main.py)
    # to get the *actual* connection URL that was determined and used by get_redis_client().
    # It ensures consistency if get_redis_client() had to construct it from parts or used a default.
    if _redis_url_config is None: # If get_redis_client hasn't been called yet
        # Determine it similarly to how get_redis_client would, for early access if needed.
        # This logic should mirror the determination within get_redis_client for consistency.
        temp_redis_url = os.getenv("REDIS_URL")
        if temp_redis_url:
            _redis_url_config = temp_redis_url
            logger.info(f"get_redis_url: Determined REDIS_URL from environment: {_redis_url_config}")
        else:
            REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
            REDIS_PORT_STR = os.environ.get("REDIS_PORT", "6379")
            REDIS_DB_STR = os.environ.get("REDIS_DB", "0")
            try:
                REDIS_PORT = int(REDIS_PORT_STR)
                REDIS_DB = int(REDIS_DB_STR)
            except ValueError: # Should ideally not happen if get_redis_client already ran and failed
                REDIS_PORT = 6379
                REDIS_DB = 0
            _redis_url_config = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
            logger.info(f"get_redis_url: REDIS_URL not set, constructed from components: {_redis_url_config}")

    return _redis_url_config


def get_cache(key: str):
    """
    Retrieves data from Redis cache using the shared client.
    Expects data to be stored as JSON strings.
    """
    client = get_redis_client()
    if not client:
        logger.warning("Shared Redis client not available. Cannot get cache.")
        return None
    try:
        cached_data = client.get(key)
        if cached_data:
            logger.debug(f"Cache hit for key: {key}")
            return json.loads(cached_data)
        logger.debug(f"Cache miss for key: {key}")
        return None
    except redis.exceptions.RedisError as e:
        logger.error(f"Redis error retrieving from cache for key {key}: {e}", exc_info=True)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error for key {key}: {e}. Data: {cached_data}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error retrieving from cache for key {key}: {e}", exc_info=True)
    return None

def set_cache(key: str, value, ex: int = 300):
    """
    Stores data in Redis cache using the shared client.
    Serializes data to JSON string.
    ex: Expiry time in seconds (default 5 minutes).
    """
    client = get_redis_client()
    if not client:
        logger.warning("Shared Redis client not available. Cannot set cache.")
        return False
    try:
        client.set(key, json.dumps(value), ex=ex)
        logger.debug(f"Data cached for key: {key} with expiry {ex}s.")
        return True
    except redis.exceptions.RedisError as e:
        logger.error(f"Redis error setting cache for key {key}: {e}", exc_info=True)
    except TypeError as e: # Catches JSON serialization errors
        logger.error(f"JSON serialization error for key {key}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error setting cache for key {key}: {e}", exc_info=True)
    return False

def publish_message(channel: str, message: dict):
    """
    Publishes a message to a Redis channel for pub/sub messaging using the shared client.
    """
    client = get_redis_client()
    if not client:
        logger.warning("Shared Redis client not available. Cannot publish message.")
        return False
    try:
        client.publish(channel, json.dumps(message))
        logger.debug(f"Published message to channel '{channel}': {message}")
        return True
    except redis.exceptions.RedisError as e:
        logger.error(f"Redis error publishing to channel {channel}: {e}", exc_info=True)
    except TypeError as e: # Catches JSON serialization errors
        logger.error(f"JSON serialization error for message to channel {channel}: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"Unexpected error publishing to channel {channel}: {e}", exc_info=True)
    return False

# Example usage (for testing this module independently)
if __name__ == "__main__":
    # Basic logging config for standalone testing
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Shared Redis client module running in standalone test mode.")
    
    # Set a mock environment variable for testing if not already set
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1") # Use a different DB for testing

    # Initialize client for testing
    client = get_redis_client()

    if client:
        logger.info(f"Using Redis client connected to: {client.connection_pool.connection_kwargs.get('host', 'N/A')}:{client.connection_pool.connection_kwargs.get('port', 'N/A')}")
        test_key = "test_shared_data_key"
        test_value = {"status": "success", "data": "Hello from shared cache!"}

        set_cache(test_key, test_value, ex=60)
        retrieved_value = get_cache(test_key)
        if retrieved_value:
            logger.info(f"Retrieved from shared cache: {retrieved_value}")

        publish_message("test_shared_channel", {"event": "status_update", "data": "Shared task completed."})
    else:
        logger.warning("Cannot run standalone tests as shared Redis client is not available.")