import chromadb
from chromadb.utils import embedding_functions

# For demonstration, we'll use a simple in-memory client.
# In a production setup, this would connect to a persistent Chroma instance.
client = chromadb.Client() 

# A mock embedding function (replace with actual embedding model in production)
class MockEmbeddingFunction(embedding_functions.EmbeddingFunction):
    def __call__(self, texts):
        # In a real scenario, this would generate embeddings from text
        # For now, return mock vectors of a fixed size (e.g., 1536 for OpenAI's ada-002)
        return [[float(i) / 1000 for i in range(1536)] for _ in texts]

# Initialize the collection. If it exists, get it; otherwise, create it.
# Using a dummy embedding function for local simulation.
try:
    expert_collection = client.get_or_create_collection(
        name="expert_embeddings",
        embedding_function=MockEmbeddingFunction()
    )
except Exception as e:
    print(f"Error getting/creating collection: {e}. Attempting to delete and recreate.")
    client.delete_collection(name="expert_embeddings")
    expert_collection = client.get_or_create_collection(
        name="expert_embeddings",
        embedding_function=MockEmbeddingFunction()
    )

# Minimal, hardcoded dataset of "expert embeddings"
# In a real system, these would come from an embedding model applied to expert profiles.
MOCK_EXPERT_DATA = [
    {
        "id": "exp1_dev_ops",
        "name": "Alice Developer",
        "domain": "DevOps",
        "bio": "Expert in CI/CD, Kubernetes, and cloud infrastructure.",
        "mock_vector": [0.01 * i for i in range(1536)] # Example mock vector
    },
    {
        "id": "exp2_ml_engineer",
        "name": "Bob Machinelearning",
        "domain": "Machine Learning",
        "bio": "Specializes in natural language processing and deep learning.",
        "mock_vector": [0.02 * i for i in range(1536)] # Example mock vector
    },
    {
        "id": "exp3_frontend",
        "name": "Charlie UI/UX",
        "domain": "Frontend Development",
        "bio": "Experienced with React, Vue, and modern web frameworks.",
        "mock_vector": [0.03 * i for i in range(1536)] # Example mock vector
    }
]

def initialize_expert_embeddings():
    """
    Adds the hardcoded expert embeddings to the Chroma collection.
    This function can be called once on startup or when the data needs refreshing.
    """
    print("Initializing expert embeddings in Chroma DB...")
    # Clear existing data if any, for clean re-initialization during simulation
    try:
        expert_collection.delete(ids=[d["id"] for d in MOCK_EXPERT_DATA])
        print("Cleared existing mock expert data.")
    except Exception as e:
        print(f"No existing mock data to clear or error during deletion: {e}")

    ids = [d["id"] for d in MOCK_EXPERT_DATA]
    embeddings = [d["mock_vector"] for d in MOCK_EXPERT_DATA]
    metadatas = [
        {"name": d["name"], "domain": d["domain"], "bio": d["bio"]}
        for d in MOCK_EXPERT_DATA
    ]
    
    expert_collection.add(
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    print(f"Added {len(MOCK_EXPERT_DATA)} expert embeddings.")

def query_expert_embeddings(query_vector: list, n_results: int = 2):
    """
    Queries the Chroma vector store for similar expert embeddings.
    """
    print(f"Querying Chroma DB for {n_results} similar experts...")
    results = expert_collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=['metadatas', 'distances']
    )
    
    found_experts = []
    if results and results.get('ids') and results['ids'][0]:
        for i, expert_id in enumerate(results['ids'][0]):
            metadata = results['metadatas'][0][i]
            distance = results['distances'][0][i]
            found_experts.append({
                "id": expert_id,
                "name": metadata["name"],
                "domain": metadata["domain"],
                "bio": metadata["bio"],
                "distance": distance
            })
    print(f"Chroma DB query results: {found_experts}")
    return found_experts

# Initialize embeddings when the module is imported
initialize_expert_embeddings()

if __name__ == "__main__":
    print("\nVector DB placeholder (Chroma) created and initialized.")
    # Example usage:
    # Simulate a query vector (e.g., from a user's question embedding)
    sample_query_vector = [0.015 * i for i in range(1536)] 
    similar_experts = query_expert_embeddings(sample_query_vector, n_results=1)
    print("\n--- Example Query Result ---")
    if similar_experts:
        for expert in similar_experts:
            print(f"Found Expert: {expert['name']} ({expert['domain']}), Distance: {expert['distance']:.4f}")
    else:
        print("No similar experts found.")

    sample_query_vector_2 = [0.025 * i for i in range(1536)]
    similar_experts_2 = query_expert_embeddings(sample_query_vector_2, n_results=1)
    print("\n--- Another Example Query Result ---")
    if similar_experts_2:
        for expert in similar_experts_2:
            print(f"Found Expert: {expert['name']} ({expert['domain']}), Distance: {expert['distance']:.4f}")
    else:
        print("No similar experts found.")