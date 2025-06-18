import os
import redis
import json

# Ensure redis_client is initialized or retrieved from an existing source
# For this vertical slice, we'll assume a basic Redis connection is available
# as per the "Important Context" which states "The .env.example file contains Redis and Supabase connection variables."
# and "Ensure the existing Redis client integration (from think-tank-monorepo/apps/backend/main.py and tasks.py) is robust."

# This implies a global or well-managed Redis client.
# For standalone testing/simulation, you might initialize it here.
# For integration with main.py, this file would primarily contain functions
# that *use* the client passed or imported from main.py.

# Let's define a placeholder for the Redis client based on environment variables
# as per the task requirements and .env.example context.
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
REDIS_DB = int(os.environ.get("REDIS_DB", 0))

try:
    # Use decode_responses=True to automatically decode responses to UTF-8 strings
    cache_redis_client = redis.StrictRedis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True
    )
    # Ping to check connection
    cache_redis_client.ping()
    print("Redis client initialized and connected for caching.")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis for caching: {e}")
    # In a real application, you might want to handle this more gracefully,
    # e.g., by using a mock client or raising a specific exception.
    cache_redis_client = None


def get_cache(key: str):
    """
    Retrieves data from Redis cache.
    Expects data to be stored as JSON strings.
    """
    if cache_redis_client:
        try:
            cached_data = cache_redis_client.get(key)
            if cached_data:
                print(f"Cache hit for key: {key}")
                return json.loads(cached_data)
            print(f"Cache miss for key: {key}")
        except Exception as e:
            print(f"Error retrieving from cache for key {key}: {e}")
    return None

def set_cache(key: str, value, ex: int = 300):
    """
    Stores data in Redis cache.
    Serializes data to JSON string.
    ex: Expiry time in seconds (default 5 minutes).
    """
    if cache_redis_client:
        try:
            cache_redis_client.set(key, json.dumps(value), ex=ex)
            print(f"Data cached for key: {key} with expiry {ex}s.")
            return True
        except Exception as e:
            print(f"Error setting cache for key {key}: {e}")
    return False

def publish_message(channel: str, message: dict):
    """
    Publishes a message to a Redis channel for pub/sub messaging.
    """
    if cache_redis_client:
        try:
            cache_redis_client.publish(channel, json.dumps(message))
            print(f"Published message to channel '{channel}': {message}")
            return True
        except Exception as e:
            print(f"Error publishing to channel {channel}: {e}")
    return False

# Example usage (for testing this module independently)
if __name__ == "__main__":
    print("Redis client placeholder for cache-queue created.")
    
    # Set a mock environment variable for testing
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"

    test_key = "test_data_key"
    test_value = {"status": "success", "data": "Hello from cache!"}

    set_cache(test_key, test_value, ex=60) # Cache for 60 seconds
    retrieved_value = get_cache(test_key)
    if retrieved_value:
        print(f"Retrieved from cache: {retrieved_value}")
    
    publish_message("test_channel", {"event": "status_update", "data": "Task completed."})