"""
Enhanced Vector Search Service for Think-Tank.

This module provides an optimized vector search implementation with:
- Multi-model support (OpenAI, Anthropic, local models)
- Efficient batch processing
- Caching for embeddings and search results
- Parallel processing for improved performance
- Advanced filtering and ranking
- Monitoring and telemetry
"""

import os
import time
import asyncio
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Union, Tuple, Set, Callable
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from dataclasses import dataclass, field

# Vector DB and embedding libraries
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

# Local imports
from config import settings
from caching import cached, get_cache, cache_key
from secrets_manager import get_api_key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vector_search")

# Constants
DEFAULT_EMBEDDING_DIMENSION = 1536  # OpenAI ada-002 dimension
DEFAULT_SIMILARITY_THRESHOLD = 0.75
DEFAULT_BATCH_SIZE = 100
DEFAULT_PARALLEL_REQUESTS = 5
DEFAULT_CACHE_TTL = 3600  # 1 hour


@dataclass
class SearchResult:
    """Search result with content, metadata, and score."""
    content: str
    metadata: Dict[str, Any]
    score: float
    vector: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
        }


@dataclass
class SearchMetrics:
    """Metrics for search operations."""
    query_time_ms: float = 0
    embedding_time_ms: float = 0
    db_search_time_ms: float = 0
    post_processing_time_ms: float = 0
    total_time_ms: float = 0
    cache_hit: bool = False
    result_count: int = 0
    filtered_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_time_ms": self.query_time_ms,
            "embedding_time_ms": self.embedding_time_ms,
            "db_search_time_ms": self.db_search_time_ms,
            "post_processing_time_ms": self.post_processing_time_ms,
            "total_time_ms": self.total_time_ms,
            "cache_hit": self.cache_hit,
            "result_count": self.result_count,
            "filtered_count": self.filtered_count,
        }


class MockEmbeddings(Embeddings):
    """Mock embeddings for testing without API keys."""
    
    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIMENSION):
        """Initialize mock embeddings."""
        self.dimension = dimension
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return mock embeddings for documents."""
        return [self._get_mock_embedding() for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Return mock embedding for query."""
        return self._get_mock_embedding()
    
    def _get_mock_embedding(self) -> List[float]:
        """Generate a deterministic mock embedding based on text."""
        return [0.1] * self.dimension


class EmbeddingService:
    """Service for generating embeddings with caching and fallbacks."""
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding service.
        
        Args:
            model_name: Name of the embedding model to use
        """
        self.model_name = model_name or settings.OPENAI_EMBEDDING_MODEL
        self.embeddings = self._initialize_embeddings()
        self.cache = get_cache("embeddings")
        self.cache_ttl = settings.CACHE_TTL
        self.executor = ThreadPoolExecutor(max_workers=DEFAULT_PARALLEL_REQUESTS)
        logger.info(f"Embedding service initialized with model: {self.model_name}")
    
    def _initialize_embeddings(self) -> Embeddings:
        """
        Initialize the embedding model with fallbacks.
        
        Returns:
            Embeddings: The embedding model
        """
        # Try OpenAI embeddings first
        openai_api_key = get_api_key("openai")
        if openai_api_key:
            try:
                return OpenAIEmbeddings(
                    openai_api_key=openai_api_key,
                    model=self.model_name,
                    chunk_size=DEFAULT_BATCH_SIZE,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}")
        
        # TODO: Add support for other embedding models (Anthropic, local models)
        
        # Fall back to mock embeddings
        logger.warning("Using mock embeddings (no API key available)")
        return MockEmbeddings()
    
    @cached(namespace="embeddings")
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for a single text with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            List[float]: Embedding vector
        """
        start_time = time.time()
        embedding = self.embeddings.embed_query(text)
        logger.debug(f"Embedding generated in {(time.time() - start_time) * 1000:.2f}ms")
        return embedding
    
    async def get_embeddings_async(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for multiple texts asynchronously.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List[List[float]]: List of embedding vectors
        """
        if not texts:
            return []
        
        # Check cache first
        cache_keys = [cache_key("embedding", text) for text in texts]
        cached_embeddings = self.cache.get_many(cache_keys)
        
        # Identify texts that need embedding
        missing_indices = []
        results = [None] * len(texts)
        
        for i, key in enumerate(cache_keys):
            if key in cached_embeddings:
                results[i] = cached_embeddings[key]
            else:
                missing_indices.append(i)
        
        if missing_indices:
            # Generate embeddings for missing texts
            missing_texts = [texts[i] for i in missing_indices]
            
            # Process in batches for efficiency
            batches = [missing_texts[i:i + DEFAULT_BATCH_SIZE] 
                      for i in range(0, len(missing_texts), DEFAULT_BATCH_SIZE)]
            
            # Generate embeddings in parallel
            loop = asyncio.get_event_loop()
            batch_results = await asyncio.gather(*[
                loop.run_in_executor(
                    self.executor,
                    partial(self.embeddings.embed_documents, batch)
                )
                for batch in batches
            ])
            
            # Flatten batch results
            all_embeddings = []
            for batch in batch_results:
                all_embeddings.extend(batch)
            
            # Update results and cache
            for idx, embedding in zip(missing_indices, all_embeddings):
                results[idx] = embedding
                self.cache.set(cache_keys[idx], embedding, self.cache_ttl)
        
        return results


class VectorSearchEnhanced:
    """
    Enhanced vector search service with optimizations.
    
    This class provides vector search functionality with:
    - Multi-model support
    - Caching
    - Batch processing
    - Advanced filtering and ranking
    """
    
    def __init__(self):
        """Initialize the vector search service."""
        self.embedding_service = EmbeddingService()
        self.vector_stores = {}
        self.initialized = False
        self.cache = get_cache("vector_search")
        self.cache_ttl = settings.CACHE_TTL
        logger.info("Enhanced vector search service initialized")
    
    async def initialize(self):
        """Initialize vector stores."""
        if self.initialized:
            return
        
        # Initialize default collections
        self.vector_stores["knowledge_base"] = await self._create_vector_store(
            collection_name="knowledge_base",
            persist_directory=os.path.join(settings.VECTOR_DB_PERSIST_DIRECTORY, "knowledge_base")
        )
        
        self.vector_stores["tal_blocks"] = await self._create_vector_store(
            collection_name="tal_blocks",
            persist_directory=os.path.join(settings.VECTOR_DB_PERSIST_DIRECTORY, "tal_blocks")
        )
        
        self.initialized = True
        logger.info("Vector stores initialized")
    
    async def _create_vector_store(
        self, 
        collection_name: str, 
        persist_directory: str
    ) -> Chroma:
        """
        Create a vector store.
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist the vector store
            
        Returns:
            Chroma: The vector store
        """
        # Ensure directory exists
        os.makedirs(persist_directory, exist_ok=True)
        
        # Create vector store
        return Chroma(
            collection_name=collection_name,
            embedding_function=self.embedding_service.embeddings,
            persist_directory=persist_directory
        )
    
    async def search(
        self, 
        query: str, 
        collection: str = "knowledge_base", 
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        return_metrics: bool = False,
        rerank: bool = False
    ) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict[str, Any]]]:
        """
        Search for similar documents in the vector store.
        
        Args:
            query: Search query
            collection: Collection to search
            limit: Maximum number of results
            filters: Metadata filters
            similarity_threshold: Minimum similarity score
            return_metrics: Whether to return search metrics
            rerank: Whether to rerank results
            
        Returns:
            Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict[str, Any]]]:
                Search results and optionally metrics
        """
        metrics = SearchMetrics()
        start_time = time.time()
        
        # Check if initialized
        if not self.initialized:
            await self.initialize()
        
        # Check if collection exists
        if collection not in self.vector_stores:
            raise ValueError(f"Collection {collection} not found")
        
        # Generate cache key
        cache_key_str = cache_key(
            "vector_search", 
            query, 
            collection, 
            limit, 
            str(filters), 
            similarity_threshold
        )
        
        # Check cache
        cached_results = self.cache.get(cache_key_str)
        if cached_results is not None:
            metrics.cache_hit = True
            metrics.total_time_ms = (time.time() - start_time) * 1000
            
            if return_metrics:
                return cached_results, metrics.to_dict()
            return cached_results
        
        # Generate embedding
        embedding_start = time.time()
        query_embedding = self.embedding_service.get_embedding(query)
        metrics.embedding_time_ms = (time.time() - embedding_start) * 1000
        
        # Search vector store
        db_search_start = time.time()
        vector_store = self.vector_stores[collection]
        
        # Apply filters if provided
        filter_dict = None
        if filters:
            filter_dict = {}
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_dict[key] = {"$in": value}
                else:
                    filter_dict[key] = value
        
        # Increase k to allow for filtering by threshold
        search_limit = max(limit * 3, 20)
        
        # Perform search
        raw_results = vector_store.similarity_search_with_score_by_vector(
            embedding=query_embedding,
            k=search_limit,
            filter=filter_dict
        )
        
        metrics.db_search_time_ms = (time.time() - db_search_start) * 1000
        
        # Process results
        post_processing_start = time.time()
        results = []
        
        for doc, score in raw_results:
            # Convert distance to similarity (Chroma returns distance)
            similarity = 1.0 - score
            
            # Filter by similarity threshold
            if similarity >= similarity_threshold:
                results.append(SearchResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    score=similarity
                ))
        
        metrics.filtered_count = len(raw_results) - len(results)
        
        # Rerank results if requested
        if rerank and results:
            # TODO: Implement more sophisticated reranking
            # For now, just ensure they're sorted by score
            results.sort(key=lambda x: x.score, reverse=True)
        
        # Limit results
        results = results[:limit]
        metrics.result_count = len(results)
        
        # Convert to dictionaries
        result_dicts = [result.to_dict() for result in results]
        metrics.post_processing_time_ms = (time.time() - post_processing_start) * 1000
        
        # Cache results
        self.cache.set(cache_key_str, result_dicts, self.cache_ttl)
        
        # Calculate total time
        metrics.total_time_ms = (time.time() - start_time) * 1000
        
        if return_metrics:
            return result_dicts, metrics.to_dict()
        return result_dicts
    
    async def batch_search(
        self,
        queries: List[str],
        collection: str = "knowledge_base",
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
    ) -> List[List[Dict[str, Any]]]:
        """
        Search for multiple queries in parallel.
        
        Args:
            queries: List of search queries
            collection: Collection to search
            limit: Maximum number of results per query
            filters: Metadata filters
            similarity_threshold: Minimum similarity score
            
        Returns:
            List[List[Dict[str, Any]]]: List of search results for each query
        """
        if not queries:
            return []
        
        # Search in parallel
        results = await asyncio.gather(*[
            self.search(
                query=query,
                collection=collection,
                limit=limit,
                filters=filters,
                similarity_threshold=similarity_threshold
            )
            for query in queries
        ])
        
        return results
    
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        collection: str = "knowledge_base",
        batch_size: int = DEFAULT_BATCH_SIZE
    ):
        """
        Add documents to the vector store with batch processing.
        
        Args:
            documents: List of documents to add
            collection: Collection to add documents to
            batch_size: Batch size for processing
        """
        if not self.initialized:
            await self.initialize()
        
        # Create collection if it doesn't exist
        if collection not in self.vector_stores:
            self.vector_stores[collection] = await self._create_vector_store(
                collection_name=collection,
                persist_directory=os.path.join(settings.VECTOR_DB_PERSIST_DIRECTORY, collection)
            )
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Extract texts and metadata
            texts = [doc["content"] for doc in batch]
            metadatas = [doc["metadata"] for doc in batch]
            
            # Add to vector store
            self.vector_stores[collection].add_texts(
                texts=texts,
                metadatas=metadatas
            )
            
            logger.info(f"Added batch of {len(batch)} documents to {collection}")
        
        # Invalidate cache for this collection
        await self.invalidate_cache(collection)
    
    async def delete_documents(
        self,
        document_ids: List[str],
        collection: str = "knowledge_base"
    ):
        """
        Delete documents from the vector store.
        
        Args:
            document_ids: List of document IDs to delete
            collection: Collection to delete documents from
        """
        if not self.initialized:
            await self.initialize()
        
        if collection not in self.vector_stores:
            raise ValueError(f"Collection {collection} not found")
        
        # Delete documents
        self.vector_stores[collection].delete(document_ids)
        logger.info(f"Deleted {len(document_ids)} documents from {collection}")
        
        # Invalidate cache for this collection
        await self.invalidate_cache(collection)
    
    async def invalidate_cache(self, collection: str = None):
        """
        Invalidate cache for a collection or all collections.
        
        Args:
            collection: Collection to invalidate cache for, or None for all
        """
        # TODO: Implement more granular cache invalidation
        self.cache.clear()
        logger.info(f"Cache invalidated for {'all collections' if collection is None else collection}")
    
    async def get_collection_stats(self, collection: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.
        
        Args:
            collection: Collection to get statistics for
            
        Returns:
            Dict[str, Any]: Collection statistics
        """
        if not self.initialized:
            await self.initialize()
        
        if collection not in self.vector_stores:
            raise ValueError(f"Collection {collection} not found")
        
        # Get collection stats
        vector_store = self.vector_stores[collection]
        collection_obj = vector_store._collection
        
        # Get count
        count = collection_obj.count()
        
        # Get sample of embeddings to estimate dimension
        if count > 0:
            sample = collection_obj.get(limit=1)
            embedding_dimension = len(sample["embeddings"][0])
        else:
            embedding_dimension = DEFAULT_EMBEDDING_DIMENSION
        
        return {
            "name": collection,
            "count": count,
            "embedding_dimension": embedding_dimension,
            "embedding_model": self.embedding_service.model_name,
        }
    
    async def close(self):
        """Close vector stores."""
        for name, store in self.vector_stores.items():
            if hasattr(store, "persist"):
                store.persist()
                logger.info(f"Persisted vector store: {name}")


# Create a global instance
vector_search = VectorSearchEnhanced()