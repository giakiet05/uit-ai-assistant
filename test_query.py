"""
A simple script for interactively testing the QueryEngine.
"""

from src.rag.query_engine import QueryEngine

def main():
    """
    Initializes the QueryEngine and enters an interactive loop to accept user questions.
    """
    try:
        query_engine = QueryEngine()
    except Exception as e:
        print(f"[FATAL] Failed to initialize QueryEngine: {e}")
        return

    print("\n" + "="*50)
    print("✅ RAG Query Engine is ready. Type 'exit' or 'quit' to stop.")
    print("="*50)

    # Example questions you can ask:
    print("\nExample questions:")
    print(" - Quy chế đào tạo theo học chế tín chỉ là gì?")
    print(" - Các loại bằng tốt nghiệp tại trường? Và điều kiện để được cấp bằng?")
    print(" - ...")

    while True:
        try:
            question = input("\n❓ Your Question: ")
            if question.lower() in ['exit', 'quit']:
                break
            if not question:
                continue

            response = query_engine.query(question)

            print("\n" + "-"*3)
            print(f"💡 Answer: {response.response}")
            print("-"*3)

            # Print source nodes for verification
            if response.source_nodes:
                print("📚 Sources:")
                for i, source_node in enumerate(response.source_nodes):
                    print(f"  [{i+1}] Score: {source_node.score:.4f}")
                    # Access metadata that we attached during the build process
                    if 'original_url' in source_node.metadata:
                        print(f"      - URL: {source_node.metadata['original_url']}")
                    if 'title' in source_node.metadata:
                        print(f"      - Title: {source_node.metadata['title']}")
                    # print(f"      - Text: {source_node.get_content()[:200]}...") # Uncomment to see the raw chunk
            else:
                print("📚 No sources found.")

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"[ERROR] An error occurred: {e}")

if __name__ == "__main__":
    main()
