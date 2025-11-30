"""
Test Indexing Pipeline - Test chunking + embedding cho 1 file cụ thể.

Verifies:
- Document loading from single file
- Hierarchical markdown parsing
- Token counting
- Embedding and indexing to ChromaDB
- Basic retrieval with hardcoded query
"""
from pathlib import Path
import json
from llama_index.core import Document, VectorStoreIndex, StorageContext, Settings as LlamaSettings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
import chromadb

from src.shared.config import settings
from src.knowledge_builder.indexing import HierarchicalMarkdownParser


# ============================================================================
# HARDCODED TEST SETTINGS - CHANGE THESE TO TEST DIFFERENT FILES
# ============================================================================
TEST_FILE_PATH = "../data/processed/daa.uit.edu.vn/regulation/01-quyet-dinh-ve-viec-ban-hanh-quy-che-dao-tao-theo-hoc-che-tin-chi__790-qd-dhcntt_28-9-22_quy_che_dao_tao.md"
TEST_QUERY = "Types of courses and their descriptions"
# ============================================================================


def load_single_document(file_path: str):
    """
    Load a single document từ file path.

    Args:
        file_path: Path to markdown file

    Returns:
        Document object or None
    """
    md_file = Path(file_path)

    if not md_file.exists():
        print(f"[ERROR] File not found: {md_file}")
        return None

    print(f"[INFO] Loading: {md_file.name}...")

    try:
        # Read markdown content
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            print(f"[ERROR] Empty content")
            return None

        # Load metadata_generator from JSON
        json_file = md_file.with_suffix('.json')
        metadata = {}

        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            print(f"[WARNING] No metadata JSON found")

        # Create Document
        doc = Document(
            text=content,
            metadata=metadata,
            id_=metadata.get("document_id", md_file.stem)
        )

        print(f"[SUCCESS] Loaded document\n")
        return doc

    except Exception as e:
        print(f"[ERROR] Failed to load: {e}")
        return None


def test_indexing():
    """Test indexing pipeline cho 1 file cụ thể."""
    print("="*70)
    print(f"🧪 TESTING INDEXING PIPELINE")
    print(f"   File: {TEST_FILE_PATH}")
    print(f"   Query: {TEST_QUERY}")
    print("="*70 + "\n")

    # Step 1: Load document
    print("📄 Step 1: Loading document...")
    document = load_single_document(TEST_FILE_PATH)

    if not document:
        print("[ERROR] Failed to load document")
        return

    # Initialize parser
    parser = HierarchicalMarkdownParser(
        max_tokens=7000,
        sub_chunk_size=1024,
        sub_chunk_overlap=128
    )

    total_chars = len(document.text)
    total_tokens = parser.count_tokens(document.text)

    print(f"📊 Document Stats:")
    print(f"   Characters: {total_chars:,}")
    print(f"   Tokens: {total_tokens:,}")
    print()

    # Step 2: Parse to nodes
    print("✂️  Step 2: Parsing to nodes...")
    nodes = parser.get_nodes_from_documents([document])
    stats = parser.get_stats()

    print(f"📊 Parsing Stats:")
    print(f"   Initial MD nodes: {stats['total_nodes']}")
    print(f"   Large nodes split: {stats['large_nodes_split']}")
    print(f"   Final nodes: {stats['final_nodes']}")
    print()

    # Token stats
    node_tokens = [parser.count_tokens(node.text) for node in nodes]
    max_tokens = max(node_tokens)
    avg_tokens = sum(node_tokens) / len(node_tokens)

    print(f"🔢 Token Stats:")
    print(f"   Max tokens/chunk: {max_tokens}")
    print(f"   Avg tokens/chunk: {avg_tokens:.1f}")
    print(f"   Chunks > 7000 tokens: {sum(1 for t in node_tokens if t > 7000)}")
    print(f"   Chunks > 8192 tokens: {sum(1 for t in node_tokens if t > 8192)} ⚠️")
    print()

    # Step 3: Setup embedding & ChromaDB
    print("🔧 Step 3: Setting up embedding & vector store...")

    if not settings.credentials.OPENAI_API_KEY:
        print("[ERROR] OPENAI_API_KEY not found")
        return

    embed_model = OpenAIEmbedding(
        model=settings.retrieval.EMBED_MODEL,
        api_key=settings.credentials.OPENAI_API_KEY
    )

    LlamaSettings.embed_model = embed_model
    # Note: Don't set node_parser in LlamaSettings since we already parsed manually

    # Create test collection in ChromaDB
    test_collection_name = "test_single_file"
    print(f"   Collection: {test_collection_name}")

    db = chromadb.PersistentClient(path=str(settings.paths.VECTOR_STORE_DIR))

    # Delete existing test collection if exists
    try:
        db.delete_collection(test_collection_name)
        print(f"   Deleted existing test collection")
    except:
        pass

    chroma_collection = db.get_or_create_collection(test_collection_name)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    print()

    # Step 4: Build index (embed + store)
    print(f"🚀 Step 4: Embedding & indexing {len(nodes)} nodes...")
    print(f"   (This may take a while...)")

    try:
        # Use from_nodes since we already parsed manually
        index = VectorStoreIndex(
            nodes=nodes,
            storage_context=storage_context,
        )

        print(f"✅ Successfully indexed {len(nodes)} nodes!")
        print()

    except Exception as e:
        print(f"❌ FAILED to index: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 5: Test retrieval
    print(f"🔍 Step 5: Testing retrieval...")
    print(f"   Query: {TEST_QUERY}")
    print()

    retriever = index.as_retriever(
        similarity_top_k=settings.retrieval.SIMILARITY_TOP_K
    )

    retrieved_nodes = retriever.retrieve(TEST_QUERY)

    print(f"📊 Retrieved {len(retrieved_nodes)} nodes:\n")

    for i, node in enumerate(retrieved_nodes, 1):
        print(f"--- Result {i} ---")
        print(f"Score: {node.score:.4f}")
        print(f"Tokens: {parser.count_tokens(node.text)}")

        if node.metadata:
            doc_id = node.metadata.get("document_id", "N/A")
            print(f"Doc ID: {doc_id}")

        preview = node.text[:200].replace("\n", " ")
        print(f"Preview: {preview}...")
        print()

    # Final summary
    print("="*70)
    print("✅ INDEXING TEST COMPLETE")
    print("="*70)
    print(f"📊 Summary:")
    print(f"   Nodes created: {len(nodes)}")
    print(f"   Max tokens/chunk: {max_tokens} {'⚠️ EXCEEDS 8192!' if max_tokens > 8192 else '✅'}")
    print(f"   Retrieved nodes: {len(retrieved_nodes)}")
    print(f"   Test collection: {test_collection_name}")
    print()
    print(f"💡 To test different file/query, edit TEST_FILE_PATH and TEST_QUERY at top of file")
    print("="*70)


if __name__ == "__main__":
    test_indexing()
