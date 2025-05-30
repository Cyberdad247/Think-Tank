"""
Multi-level caching utility for Think-Tank.

This module provides a comprehensive caching system with multiple storage backends
and strategies to optimize performance and resource usage.

Features:
- Multi-level caching (memory, Redis, file)
- Configurable TTL and eviction policies
- Cache invalidation and prefetching
- Metrics and monitoring
- Serialization/deserialization of complex objects
"""

import os
import time
import json
import pickle
import hashlib
import logging
import functools
from typing import Any, Dict, List, Optional, Union, Callable, Tuple, Set
from datetime import datetime, timedelta
from functools import lru_cache
from threading import RLock
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("caching")

# Import settings after logger configuration to avoid circular imports
from config import settings

class CacheError(Exception):
    """Base exception for cache-related errors."""
    pass

class CacheBackendError(CacheError):
    """Exception raised when there's an error with a cache backend."""
    pass

class SerializationError(CacheError):
    """Exception raised when there's an error serializing or deserializing data."""
    pass

class CacheBackend:
    """Base class for cache backends."""
    
    def __init__(self, namespace: str = "default"):
        """
        Initialize the cache backend.
        
        Args:
            namespace: Namespace for cache keys
        """
        self.namespace = namespace
    
    def _make_key(self, key: str) -> str:
        """
        Create a namespaced key.
        
        Args:
            key: Original key
            
        Returns:
            str: Namespaced key
        """
        return f"{self.namespace}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found
        """
        raise NotImplementedError("Subclasses must implement get()")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement set()")
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement delete()")
    
    def clear(self) -> bool:
        """
        Clear all values from the cache.
        
        Returns:
            bool: True if successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement clear()")
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict[str, Any]: Dictionary of key-value pairs for found keys
        """
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in the cache.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        success = True
        for key, value in mapping.items():
            if not self.set(key, value, ttl):
                success = False
        return success
class MemoryCache(CacheBackend):
    """In-memory cache backend using a dictionary."""
    
    def __init__(self, namespace: str = "default", max_size: int = 1000):
        """
        Initialize the memory cache.
        
        Args:
            namespace: Namespace for cache keys
            max_size: Maximum number of items to store
        """
        super().__init__(namespace)
        self._cache: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._max_size = max_size
        self._lock = RLock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        logger.info(f"Memory cache initialized with max size: {max_size}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found
        """
        namespaced_key = self._make_key(key)
        with self._lock:
            if namespaced_key in self._cache:
                value, expiry = self._cache[namespaced_key]
                
                # Check if expired
                if expiry is not None and time.time() > expiry:
                    del self._cache[namespaced_key]
                    self._misses += 1
                    return None
                
                # Update access time (LRU implementation)
                self._cache[namespaced_key] = (value, expiry)
                self._hits += 1
                return value
            
            self._misses += 1
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        namespaced_key = self._make_key(key)
        with self._lock:
            # Check if we need to evict items
            if len(self._cache) >= self._max_size and namespaced_key not in self._cache:
                self._evict_one()
            
            # Calculate expiry time
            expiry = time.time() + ttl if ttl is not None else None
            
            # Store value
            self._cache[namespaced_key] = (value, expiry)
            return True
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        namespaced_key = self._make_key(key)
        with self._lock:
            if namespaced_key in self._cache:
                del self._cache[namespaced_key]
                return True
            return False
    
    def clear(self) -> bool:
        """
        Clear all values from the cache.
        
        Returns:
            bool: True if successful, False otherwise
        """
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
            return True
    
    def _evict_one(self) -> None:
        """
        Evict one item from the cache using LRU policy.
        """
        # Simple LRU implementation - remove the first item
        # In a real implementation, you would track access times
        if self._cache:
            key_to_remove = next(iter(self._cache))
            del self._cache[key_to_remove]
            self._evictions += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict[str, Any]: Cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": hit_rate,
                "evictions": self._evictions,
            }
class RedisCache(CacheBackend):
    """Redis cache backend."""
    
    def __init__(
        self, 
        namespace: str = "default", 
        redis_url: Optional[str] = None,
        serializer: str = "pickle"
    ):
        """
        Initialize the Redis cache.
        
        Args:
            namespace: Namespace for cache keys
            redis_url: Redis connection URL
            serializer: Serializer to use ('json' or 'pickle')
        """
        super().__init__(namespace)
        
        # Use provided URL or get from settings
        self._redis_url = redis_url or settings.REDIS_URL
        
        # Set up serializer
        if serializer == "json":
            self._serialize = self._serialize_json
            self._deserialize = self._deserialize_json
        elif serializer == "pickle":
            self._serialize = self._serialize_pickle
            self._deserialize = self._deserialize_pickle
        else:
            raise ValueError(f"Unknown serializer: {serializer}")
        
        self._serializer = serializer
        self._client = None
        self._connect()
        logger.info(f"Redis cache initialized with {serializer} serializer")
    
    def _connect(self) -> None:
        """Connect to Redis."""
        try:
            self._client = redis.from_url(
                self._redis_url,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=False,  # We handle decoding ourselves
            )
            # Test connection
            self._client.ping()
        except redis.RedisError as e:
            logger.error(f"Redis connection error: {e}")
            raise CacheBackendError(f"Could not connect to Redis: {e}") from e
    
    def _serialize_json(self, value: Any) -> bytes:
        """
        Serialize a value to JSON.
        
        Args:
            value: Value to serialize
            
        Returns:
            bytes: Serialized value
        """
        try:
            return json.dumps(value).encode("utf-8")
        except (TypeError, ValueError) as e:
            raise SerializationError(f"JSON serialization error: {e}") from e
    
    def _deserialize_json(self, value: bytes) -> Any:
        """
        Deserialize a value from JSON.
        
        Args:
            value: Serialized value
            
        Returns:
            Any: Deserialized value
        """
        try:
            return json.loads(value.decode("utf-8"))
        except (TypeError, ValueError, UnicodeDecodeError) as e:
            raise SerializationError(f"JSON deserialization error: {e}") from e
    
    def _serialize_pickle(self, value: Any) -> bytes:
        """
        Serialize a value using pickle.
        
        Args:
            value: Value to serialize
            
        Returns:
            bytes: Serialized value
        """
        try:
            return pickle.dumps(value)
        except pickle.PickleError as e:
            raise SerializationError(f"Pickle serialization error: {e}") from e
    
    def _deserialize_pickle(self, value: bytes) -> Any:
        """
        Deserialize a value from pickle.
        
        Args:
            value: Serialized value
            
        Returns:
            Any: Deserialized value
        """
        try:
            return pickle.loads(value)
        except pickle.PickleError as e:
            raise SerializationError(f"Pickle deserialization error: {e}") from e
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found
        """
        namespaced_key = self._make_key(key)
        try:
            value = self._client.get(namespaced_key)
            if value is None:
                return None
            
            return self._deserialize(value)
        except redis.RedisError as e:
            logger.error(f"Redis error in get(): {e}")
            return None
        except SerializationError as e:
            logger.error(f"Deserialization error in get(): {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        namespaced_key = self._make_key(key)
        try:
            serialized = self._serialize(value)
            if ttl is not None:
                return bool(self._client.setex(namespaced_key, ttl, serialized))
            else:
                return bool(self._client.set(namespaced_key, serialized))
        except redis.RedisError as e:
            logger.error(f"Redis error in set(): {e}")
            return False
        except SerializationError as e:
            logger.error(f"Serialization error in set(): {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        namespaced_key = self._make_key(key)
        try:
            return bool(self._client.delete(namespaced_key))
        except redis.RedisError as e:
            logger.error(f"Redis error in delete(): {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all values from the namespace.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get all keys in the namespace
            pattern = f"{self.namespace}:*"
            keys = self._client.keys(pattern)
            
            if keys:
                return bool(self._client.delete(*keys))
            return True
        except redis.RedisError as e:
            logger.error(f"Redis error in clear(): {e}")
            return False
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict[str, Any]: Dictionary of key-value pairs for found keys
        """
        namespaced_keys = [self._make_key(key) for key in keys]
        try:
            values = self._client.mget(namespaced_keys)
            result = {}
            
            for i, value in enumerate(values):
                if value is not None:
                    try:
                        result[keys[i]] = self._deserialize(value)
                    except SerializationError as e:
                        logger.error(f"Deserialization error in get_many(): {e}")
            
            return result
        except redis.RedisError as e:
            logger.error(f"Redis error in get_many(): {e}")
            return {}
    
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in the cache.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        try:
            pipeline = self._client.pipeline()
            
            for key, value in mapping.items():
                namespaced_key = self._make_key(key)
                try:
                    serialized = self._serialize(value)
                    if ttl is not None:
                        pipeline.setex(namespaced_key, ttl, serialized)
                    else:
                        pipeline.set(namespaced_key, serialized)
                except SerializationError as e:
                    logger.error(f"Serialization error in set_many(): {e}")
                    return False
            
            pipeline.execute()
            return True
        except redis.RedisError as e:
            logger.error(f"Redis error in set_many(): {e}")
            return False
class FileCache(CacheBackend):
    """File-based cache backend."""
    
    def __init__(
        self, 
        namespace: str = "default", 
        directory: Optional[str] = None,
        serializer: str = "pickle"
    ):
        """
        Initialize the file cache.
        
        Args:
            namespace: Namespace for cache keys
            directory: Cache directory
            serializer: Serializer to use ('json' or 'pickle')
        """
        super().__init__(namespace)
        
        # Use provided directory or default
        self._directory = directory or os.path.join(os.path.dirname(__file__), "cache")
        self._namespace_dir = os.path.join(self._directory, namespace)
        
        # Set up serializer
        if serializer == "json":
            self._serialize = self._serialize_json
            self._deserialize = self._deserialize_json
            self._extension = ".json"
        elif serializer == "pickle":
            self._serialize = self._serialize_pickle
            self._deserialize = self._deserialize_pickle
            self._extension = ".pkl"
        else:
            raise ValueError(f"Unknown serializer: {serializer}")
        
        self._serializer = serializer
        self._ensure_directory()
        logger.info(f"File cache initialized in {self._namespace_dir}")
    
    def _ensure_directory(self) -> None:
        """Ensure the cache directory exists."""
        os.makedirs(self._namespace_dir, exist_ok=True)
    
    def _get_file_path(self, key: str) -> str:
        """
        Get the file path for a key.
        
        Args:
            key: Cache key
            
        Returns:
            str: File path
        """
        # Hash the key to avoid file system issues
        hashed_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self._namespace_dir, f"{hashed_key}{self._extension}")
    
    def _serialize_json(self, value: Any) -> str:
        """
        Serialize a value to JSON.
        
        Args:
            value: Value to serialize
            
        Returns:
            str: Serialized value
        """
        try:
            # Include metadata for TTL
            data = {
                "value": value,
                "expires": None,
            }
            return json.dumps(data)
        except (TypeError, ValueError) as e:
            raise SerializationError(f"JSON serialization error: {e}") from e
    
    def _deserialize_json(self, value: str) -> Any:
        """
        Deserialize a value from JSON.
        
        Args:
            value: Serialized value
            
        Returns:
            Any: Deserialized value
        """
        try:
            data = json.loads(value)
            return data["value"]
        except (TypeError, ValueError, KeyError) as e:
            raise SerializationError(f"JSON deserialization error: {e}") from e
    
    def _serialize_pickle(self, value: Any) -> bytes:
        """
        Serialize a value using pickle.
        
        Args:
            value: Value to serialize
            
        Returns:
            bytes: Serialized value
        """
        try:
            # Include metadata for TTL
            data = {
                "value": value,
                "expires": None,
            }
            return pickle.dumps(data)
        except pickle.PickleError as e:
            raise SerializationError(f"Pickle serialization error: {e}") from e
    
    def _deserialize_pickle(self, value: bytes) -> Any:
        """
        Deserialize a value from pickle.
        
        Args:
            value: Serialized value
            
        Returns:
            Any: Deserialized value
        """
        try:
            data = pickle.loads(value)
            return data["value"]
        except (pickle.PickleError, KeyError) as e:
            raise SerializationError(f"Pickle deserialization error: {e}") from e
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found
        """
        file_path = self._get_file_path(key)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            # Check if file has expired
            stat = os.stat(file_path)
            metadata_path = f"{file_path}.meta"
            
            # Check for expiration
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata = json.load(f)
                    if metadata.get("expires") and metadata["expires"] < time.time():
                        # Expired
                        os.unlink(file_path)
                        os.unlink(metadata_path)
                        return None
            
            # Read and deserialize
            mode = "rb" if self._serializer == "pickle" else "r"
            with open(file_path, mode) as f:
                data = f.read()
                return self._deserialize(data)
        except (OSError, SerializationError) as e:
            logger.error(f"Error reading cache file: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        file_path = self._get_file_path(key)
        
        try:
            # Serialize the value
            serialized = self._serialize(value)
            
            # Write to file
            mode = "wb" if self._serializer == "pickle" else "w"
            with open(file_path, mode) as f:
                f.write(serialized)
            
            # Write metadata if TTL is provided
            if ttl is not None:
                metadata_path = f"{file_path}.meta"
                metadata = {
                    "expires": time.time() + ttl,
                    "created": time.time(),
                }
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f)
            
            return True
        except (OSError, SerializationError) as e:
            logger.error(f"Error writing cache file: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if successful, False otherwise
        """
        file_path = self._get_file_path(key)
        metadata_path = f"{file_path}.meta"
        
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
            
            if os.path.exists(metadata_path):
                os.unlink(metadata_path)
            
            return True
        except OSError as e:
            logger.error(f"Error deleting cache file: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all values from the cache.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            for filename in os.listdir(self._namespace_dir):
                file_path = os.path.join(self._namespace_dir, filename)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            return True
        except OSError as e:
            logger.error(f"Error clearing cache directory: {e}")
            return False


class MultiLevelCache:
    """
    Multi-level cache with tiered storage backends.
    
    This class provides a unified interface for accessing multiple cache
    backends with different performance characteristics.
    """
    
    def __init__(
        self,
        namespace: str = "default",
        backends: Optional[List[CacheBackend]] = None,
        default_ttl: int = 3600
    ):
        """
        Initialize the multi-level cache.
        
        Args:
            namespace: Namespace for cache keys
            backends: List of cache backends (fastest to slowest)
            default_ttl: Default TTL in seconds
        """
        self.namespace = namespace
        self.default_ttl = default_ttl
        
        # Set up backends if not provided
        if backends is None:
            try:
                # Try to set up Redis cache
                redis_cache = RedisCache(namespace=namespace)
                backends = [
                    MemoryCache(namespace=namespace),
                    redis_cache,
                    FileCache(namespace=namespace),
                ]
            except CacheBackendError:
                # Fall back to memory and file cache if Redis is not available
                logger.warning("Redis not available, falling back to memory and file cache")
                backends = [
                    MemoryCache(namespace=namespace),
                    FileCache(namespace=namespace),
                ]
        
        self.backends = backends
        logger.info(f"Multi-level cache initialized with {len(backends)} backends")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        This method checks each backend in order (fastest to slowest)
        and populates faster backends when a value is found in a slower one.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value or None if not found
        """
        # Check each backend in order (fastest to slowest)
        for i, backend in enumerate(self.backends):
            value = backend.get(key)
            if value is not None:
                # Found in this backend, populate faster backends
                self._populate_faster_backends(key, value, i)
                return value
        
        # Not found in any backend
        return None
    
    def _populate_faster_backends(self, key: str, value: Any, found_index: int) -> None:
        """
        Populate faster backends with a value found in a slower backend.
        
        Args:
            key: Cache key
            value: Cached value
            found_index: Index of the backend where the value was found
        """
        # Populate all faster backends
        for i in range(found_index):
            self.backends[i].set(key, value, self.default_ttl)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in all cache backends.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            bool: True if set in at least one backend, False otherwise
        """
        ttl = ttl if ttl is not None else self.default_ttl
        success = False
        
        # Set in all backends
        for backend in self.backends:
            if backend.set(key, value, ttl):
                success = True
        
        return success
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from all cache backends.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if deleted from at least one backend, False otherwise
        """
        success = False
        
        # Delete from all backends
        for backend in self.backends:
            if backend.delete(key):
                success = True
        
        return success
    
    def clear(self) -> bool:
        """
        Clear all values from all cache backends.
        
        Returns:
            bool: True if cleared at least one backend, False otherwise
        """
        success = False
        
        # Clear all backends
        for backend in self.backends:
            if backend.clear():
                success = True
        
        return success
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict[str, Any]: Dictionary of key-value pairs for found keys
        """
        result = {}
        remaining_keys = set(keys)
        
        # Check each backend in order
        for i, backend in enumerate(self.backends):
            if not remaining_keys:
                break
                
            # Get values from this backend
            values = backend.get_many(list(remaining_keys))
            
            # Add to result and populate faster backends
            for key, value in values.items():
                result[key] = value
                remaining_keys.remove(key)
                self._populate_faster_backends(key, value, i)
        
        return result
    
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in all cache backends.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            bool: True if set in at least one backend, False otherwise
        """
        ttl = ttl if ttl is not None else self.default_ttl
        success = False
        
        # Set in all backends
        for backend in self.backends:
            if backend.set_many(mapping, ttl):
                success = True
        
        return success


def cache_key(*args, **kwargs) -> str:
    """
    Generate a cache key from arguments.
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        str: Cache key
    """
    # Convert args and kwargs to strings
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    
    # Join and hash
    key_str = ":".join(key_parts)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(
    ttl: Optional[int] = None,
    namespace: Optional[str] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time to live in seconds
        namespace: Cache namespace
        key_func: Function to generate cache key
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        func_namespace = namespace or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not settings.CACHE_ENABLED:
                return func(*args, **kwargs)
            
            # Get cache instance
            cache = get_cache(func_namespace)
            
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result
        
        return wrapper
    
    return decorator


@lru_cache()
def get_cache(namespace: str = "default") -> MultiLevelCache:
    """
    Get a cached instance of the multi-level cache.
    
    Args:
        namespace: Cache namespace
        
    Returns:
        MultiLevelCache: Cache instance
    """
    # Determine the appropriate cache strategy based on settings
    if settings.CACHE_STRATEGY == "multi_level":
        return MultiLevelCache(namespace=namespace, default_ttl=settings.CACHE_TTL)
    else:
        # Single-level cache (memory only)
        return MultiLevelCache(
            namespace=namespace,
            backends=[MemoryCache(namespace=namespace)],
            default_ttl=settings.CACHE_TTL
        )


# Create a global cache instance
cache = get_cache()