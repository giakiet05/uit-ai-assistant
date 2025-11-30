
import os
import sys

# Add src to path to allow importing local modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import chromadb
from llama_index.core import Settings as LlamaSettings, VectorStoreIndex
from llama_index.core.schema import QueryBundle
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.shared.config import settings
from src.shared.agent import MultiCollectionRetriever


def main():
    """
    Main function to test the MultiCollectionRetriever interactively.
    """
    print("Initializing retriever for testing...")

    # 1. Setup LlamaIndex settings (especially the embedding model)
    if not settings.credentials.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in .env file.")

    LlamaSettings.embed_model = OpenAIEmbedding(
        model=settings.retrieval.EMBED_MODEL,
        api_key=settings.credentials.OPENAI_API_KEY,
    )

    # 2. Load collections from ChromaDB
    try:
        db = chromadb.PersistentClient(path=str(settings.paths.VECTOR_STORE_DIR))
    except Exception as e:
        print(f"Error connecting to ChromaDB at {settings.paths.VECTOR_STORE_DIR}: {e}")
        print("Please ensure the vector store is correctly built.")
        return

    collections = {}
    available_collections = settings.query_routing.AVAILABLE_COLLECTIONS
    if not available_collections:
        print("No available collections found in settings. Exiting.")
        return

    print(f"Loading collections: {available_collections}")
    for category in available_collections:
        try:
            chroma_collection = db.get_collection(category)
            vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
            collections[category] = VectorStoreIndex.from_vector_store(vector_store)
        except Exception as e:
            print(f"Error loading collection '{category}': {e}")
            print("Please ensure the collection exists and the data is built.")
            return

    print(f"Loaded {len(collections)} collections.")

    # 3. Initialize the MultiCollectionRetriever
    retriever = MultiCollectionRetriever(
        collections=collections, top_k=10, min_score_threshold=0.25
    )

    print("\n✅ Retriever initialized. You can now ask questions.")
    print("Type 'exit' or 'quit' to stop.")

    # 4. Interactive query loop
    while True:
        try:
            query_str = input("\nEnter your question: ")
            if query_str.lower() in ["exit", "quit"]:
                break
            if not query_str:
                continue

            query_bundle = QueryBundle(query_str)
            nodes = retriever.retrieve(query_bundle)

            print(f"\n--- Found {len(nodes)} relevant nodes ---")
            if not nodes:
                print("No relevant nodes found for your query.")
            else:
                for i, node in enumerate(nodes):
                    print(f"\n[Node {i+1}] - Score: {node.score:.4f}")
                    print(f"Source: {node.metadata.get('file_path', 'N/A')}")
                    print(f"Document ID: {node.metadata.get('document_id', 'N/A')}")
                    print(f"Title: {node.metadata.get('title', 'N/A')}")
                    print("-" * 20)
                    # Limit text for readability
                    print(node.text[:500] + "..." if len(node.text) > 500 else node.text)
                    print("-" * 20)
            print("\n" + "=" * 50)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            import traceback
            print(f"An error occurred: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
