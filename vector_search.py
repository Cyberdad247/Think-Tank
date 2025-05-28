from typing import Dict, Any, List, Optional
import asyncio
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from app.core.config import settings

class VectorSearchService:
    """Service for vector search operations using ChromaDB"""
    
    def __init__(self):
        # Use a mock embeddings for testing if no API key is available
        if not settings.OPENAI_API_KEY:
            self.embeddings = MockEmbeddings()
        else:
            self.embeddings = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
        self.vector_stores = {}
        self.initialized = False
        
    async def initialize(self):
        """Initialize vector stores"""
        if self.initialized:
            return
            
        # Initialize default collections
        self.vector_stores["knowledge_base"] = Chroma(
            collection_name="knowledge_base",
            embedding_function=self.embeddings,
            persist_directory="./vector_db"
        )
        
        self.vector_stores["tal_blocks"] = Chroma(
            collection_name="tal_blocks",
            embedding_function=self.embeddings,
            persist_directory="./vector_db"
        )
        
        self.initialized = True
        
    async def search(
        self, 
        query: str, 
        collection: str = "knowledge_base", 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar documents in the vector store"""
        if not self.initialized:
            await self.initialize()
            
        if collection not in self.vector_stores:
            raise ValueError(f"Collection {collection} not found")
            
        results = self.vector_stores[collection].similarity_search_with_score(
            query=query,
            k=limit
        )
        
        return [
            {
                "content": doc[0].page_content,
                "metadata": doc[0].metadata,
                "score": doc[1]
            }
            for doc in results
        ]
        
    async def add_documents(
        self,
        documents: List[Dict[str, Any]],
        collection: str = "knowledge_base"
    ):
        """Add documents to the vector store"""
        if not self.initialized:
            await self.initialize()
            
        if collection not in self.vector_stores:
            self.vector_stores[collection] = Chroma(
                collection_name=collection,
                embedding_function=self.embeddings,
                persist_directory="./vector_db"
            )
            
        texts = [doc["content"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        self.vector_stores[collection].add_texts(
            texts=texts,
            metadatas=metadatas
        )
        
    async def close(self):
        """Close vector stores"""
        for store in self.vector_stores.values():
            if hasattr(store, "persist"):
                store.persist()

# Mock embeddings class for testing without OpenAI API key
class MockEmbeddings:
    """Mock embeddings for testing"""
    def embed_documents(self, texts):
        """Return mock embeddings for documents"""
        return [[0.1] * 1536 for _ in texts]
    
    def embed_query(self, text):
        """Return mock embeddings for query"""
        return [0.1] * 1536
