"""
A simple script to inspect the contents of the ChromaDB vector store.
"""

import chromadb
from src.shared.config import settings

def inspect_vector_store():
    """
    Connects to the persistent ChromaDB and prints out some information.
    """
    print(f"--- Inspecting Vector Store at: {settings.paths.VECTOR_STORE_DIR} ---")

    try:
        # 1. Connect to the same persistent client
        client = chromadb.PersistentClient(path=str(settings.paths.VECTOR_STORE_DIR))

        # 2. Get the collection
        collection_name = "uit_documents_openai"
        print(f"\nAttempting to get collection: '{collection_name}'")
        collection = client.get_collection(collection_name)
        print("✅ Collection found!")

        # 3. Get the total count of items
        count = collection.count()
        print(f"\nTotal items (chunks) in the collection: {count}")

        if count == 0:
            print("\nThe collection is empty. No data has been indexed yet.")
            return

        # 4. Peek at the first 5 items to inspect them
        print("\n--- Peeking at the first 5 items ---")
        peek_result = collection.peek(limit=5)

        for i, metadata in enumerate(peek_result['metadatas']):
            print(f"\n--- Item {i+1} ---")
            print(f"  - ID: {peek_result['ids'][i]}")
            
            # Print metadata_generator fields
            print("  - Metadata:")
            for key, value in metadata.items():
                # Truncate long metadata_generator values for readability
                value_str = str(value)
                if len(value_str) > 150:
                    value_str = value_str[:150] + "..."
                print(f"    - {key}: {value_str}")

            # Print a snippet of the actual document content
            document_content = peek_result['documents'][i]
            print(f"  - Document Snippet: \"{document_content.replace('\n', ' ')}...\"")

    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}")
        print("Please ensure that you have run the builder script first and that the vector store exists.")

if __name__ == "__main__":
    inspect_vector_store()

