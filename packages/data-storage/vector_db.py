import chromadb
from chromadb.utils import embedding_functions
import logging
import os # For potential future config

# Configure logger for this module
logger = logging.getLogger(__name__)

# For demonstration, we'll use a simple in-memory client.
# In a production setup, this would connect to a persistent Chroma instance.
# CHROMA_PERSIST_PATH allows specifying a directory for persistent storage.
# If not set, an in-memory client is used.
CHROMA_PERSIST_PATH = os.getenv("CHROMA_PERSIST_PATH", None)
if CHROMA_PERSIST_PATH:
    logger.info(f"Using persistent ChromaDB client with path: {CHROMA_PERSIST_PATH}")
    try:
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_PATH)
    except Exception as e:
        logger.error(f"Failed to initialize persistent ChromaDB client at {CHROMA_PERSIST_PATH}: {e}. Falling back to in-memory client.", exc_info=True)
        logger.info("Using in-memory ChromaDB client as fallback.")
        client = chromadb.Client()
else:
    logger.info("Using in-memory ChromaDB client (CHROMA_PERSIST_PATH not set).")
    client = chromadb.Client()

expert_collection = None

# A mock embedding function (replace with actual embedding model in production)
class MockEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __call__(self, texts: chromadb.Documents) -> chromadb.Embeddings:
        # In a real scenario, this would generate embeddings from text
        # For now, return mock vectors of a fixed size (e.g., 1536 for OpenAI's ada-002)
        logger.debug(f"MockEmbeddingFunction called for {len(texts)} texts.")
        return [[float(i) / 1000 + (hash(text) % 1000) / 100000 for i in range(1536)] for text in texts]


try:
    COLLECTION_NAME = "expert_embeddings"
    logger.info(f"Attempting to get or create Chroma collection: {COLLECTION_NAME}")
    expert_collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=MockEmbeddingFunction() # Replace with actual function in production
    )
    logger.info(f"Successfully got or created Chroma collection: {COLLECTION_NAME}")
except Exception as e:
    logger.error(f"Error getting or creating collection '{COLLECTION_NAME}': {e}. Trying to reset (if applicable) or failing.", exc_info=True)
    # Depending on the error, a more robust recovery might be needed.
    # For certain errors (e.g. incompatible hash on embedding function change), deleting and recreating might be an option.
    # Example:
    # if "please delete the collection and try again" in str(e).lower():
    #     logger.warning(f"Attempting to delete and recreate collection '{COLLECTION_NAME}' due to error: {e}")
    #     try:
    #         client.delete_collection(name=COLLECTION_NAME)
    #         expert_collection = client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=MockEmbeddingFunction())
    #         logger.info(f"Successfully recreated collection '{COLLECTION_NAME}'.")
    #     except Exception as delete_recreate_e:
    #         logger.critical(f"Failed to delete and recreate collection '{COLLECTION_NAME}': {delete_recreate_e}", exc_info=True)
    #         expert_collection = None # Ensure it's None if all attempts fail
    if expert_collection is None: # If not recovered
        logger.critical(f"ChromaDB collection '{COLLECTION_NAME}' could not be initialized. Vector DB functionality will be impaired.")


# Minimal, hardcoded dataset of "expert embeddings"
MOCK_EXPERT_DATA = [
    {
        "id": "exp1_dev_ops",
        "document": "Expert in CI/CD, Kubernetes, and cloud infrastructure.", # Document for embedding
        "metadata": {"name": "Alice Developer", "domain": "DevOps"}
    },
    {
        "id": "exp2_ml_engineer",
        "document": "Specializes in natural language processing and deep learning.",
        "metadata": {"name": "Bob Machinelearning", "domain": "Machine Learning"}
    },
    {
        "id": "exp3_frontend",
        "document": "Experienced with React, Vue, and modern web frameworks.",
        "metadata": {"name": "Charlie UI/UX", "domain": "Frontend Development"}
    }
]

def initialize_expert_embeddings():
    """
    Adds the hardcoded expert documents and their embeddings to the Chroma collection.
    This function can be called once on startup or when the data needs refreshing.
    Uses the collection's embedding function to generate embeddings from documents.
    """
    if not expert_collection:
        logger.error("Chroma expert_collection not available. Cannot initialize expert embeddings.")
        return

    logger.info("Initializing expert embeddings in Chroma DB...")

    current_items = expert_collection.get(ids=[d["id"] for d in MOCK_EXPERT_DATA])
    existing_ids = set(current_items['ids'])

    new_data_to_add = [d for d in MOCK_EXPERT_DATA if d["id"] not in existing_ids]

    if not new_data_to_add:
        logger.info("All mock expert data already exists in the collection. No new data added.")
        # Optionally, one could update existing entries if their content changed.
        # For this example, we only add if ID doesn't exist.
        return

    ids_to_add = [d["id"] for d in new_data_to_add]
    documents_to_add = [d["document"] for d in new_data_to_add]
    metadatas_to_add = [d["metadata"] for d in new_data_to_add]

    try:
        expert_collection.add(
            documents=documents_to_add, # Chroma generates embeddings from these
            metadatas=metadatas_to_add,
            ids=ids_to_add
        )
        logger.info(f"Added {len(ids_to_add)} new expert embeddings to collection '{expert_collection.name}'.")
    except Exception as e:
        logger.error(f"Error adding expert embeddings to Chroma: {e}", exc_info=True)


def query_expert_embeddings(query_text: str, n_results: int = 2):
    """
    Queries the Chroma vector store for similar expert embeddings based on a query text.
    The collection's embedding function will be used to convert query_text to an embedding.
    """
    if not expert_collection:
        logger.error("Chroma expert_collection not available. Cannot query expert embeddings.")
        return []

    logger.debug(f"Querying Chroma DB for {n_results} similar experts based on text: '{query_text[:50]}...'")
    try:
        results = expert_collection.query(
            query_texts=[query_text], # Chroma generates embedding from this text
            n_results=n_results,
            include=['metadatas', 'distances', 'documents']
        )
    except Exception as e:
        logger.error(f"Error querying Chroma DB: {e}", exc_info=True)
        return []
    
    found_experts = []
    if results and results.get('ids') and results['ids'][0]:
        for i, expert_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i] if results['metadatas'] else {}
            distance = results['distances'][0][i] if results['distances'] else float('inf')
            document = results['documents'][0][i] if results['documents'] else ""
            found_experts.append({
                "id": expert_id,
                "name": metadata.get("name", "N/A"),
                "domain": metadata.get("domain", "N/A"),
                "document": document, # Changed from 'bio' to 'document' to reflect actual data
                "distance": distance
            })
    logger.debug(f"Chroma DB query results: {found_experts}")
    return found_experts

# Initialize embeddings when the module is imported, if collection is available
if expert_collection:
    initialize_expert_embeddings()
else:
    logger.warning("Expert embeddings not initialized because expert_collection is not available.")


if __name__ == "__main__":
    # Basic logging config for standalone testing
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logger.info("\nVector DB placeholder (Chroma) running in standalone test mode.")

    if not expert_collection:
        logger.critical("Chroma expert_collection not initialized. Standalone tests cannot proceed.")
    else:
        # Example usage:
        sample_query_text = "Looking for someone skilled in CI/CD and Kubernetes."
        logger.info(f"\n--- Example Query 1: '{sample_query_text}' ---")
        similar_experts = query_expert_embeddings(sample_query_text, n_results=1)
        if similar_experts:
            for expert in similar_experts:
                logger.info(f"Found Expert: {expert['name']} ({expert['domain']}), Doc: '{expert['document'][:50]}...', Distance: {expert['distance']:.4f}")
        else:
            logger.info("No similar experts found.")

        sample_query_text_2 = "Need help with natural language processing."
        logger.info(f"\n--- Example Query 2: '{sample_query_text_2}' ---")
        similar_experts_2 = query_expert_embeddings(sample_query_text_2, n_results=1)
        if similar_experts_2:
            for expert in similar_experts_2:
                logger.info(f"Found Expert: {expert['name']} ({expert['domain']}), Doc: '{expert['document'][:50]}...', Distance: {expert['distance']:.4f}")
        else:
            logger.info("No similar experts found.")