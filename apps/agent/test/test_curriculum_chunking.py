"""
Test SmartNodeSplitter với curriculum files.

Mục đích: Kiểm tra xem metadata + hierarchy có được prepend đúng vào chunks không.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from llama_index.core import Document
from src.knowledge_builder.indexing.splitters import SmartNodeSplitter
import json


def test_curriculum_chunks(file_path: str, num_chunks: int = 10):
    """Test chunking curriculum và in ra nội dung chunks."""
    print(f"\n{'='*80}")
    print(f"TESTING CURRICULUM CHUNKING")
    print(f"File: {Path(file_path).name}")
    print(f"{'='*80}\n")

    # Read file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Load metadata
    metadata = {}
    auto_metadata_path = Path(file_path).with_suffix('.json')
    if auto_metadata_path.exists():
        with open(auto_metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"✅ Loaded metadata: {auto_metadata_path.name}")
    else:
        metadata = {
            "document_id": Path(file_path).stem,
            "category": "curriculum"
        }
        print("⚠️  No metadata file, using defaults")

    print(f"\n📋 Document Metadata:")
    print(f"   Category: {metadata.get('category')}")
    print(f"   Title: {metadata.get('title', 'N/A')}")
    print(f"   Major: {metadata.get('major', 'N/A')}")
    print(f"   Year: {metadata.get('year', 'N/A')}")
    print(f"   Program Type: {metadata.get('program_type', 'N/A')}")
    print(f"   Program Name: {metadata.get('program_name', 'N/A')}")

    # Create parser
    print(f"\n🔧 Creating SmartNodeSplitter...")
    parser = SmartNodeSplitter(
        max_tokens=7000,
        sub_chunk_size=1024,
        sub_chunk_overlap=200,
        enable_title_merging=True,
        enable_pattern_detection=False,  # Curriculum không dùng pattern
        max_header_level=4  # Parse up to ####
    )

    # Parse
    print(f"\n⚙️  Parsing document...")
    doc = Document(text=content, metadata=metadata)
    nodes = parser.get_nodes_from_documents([doc])

    # Show stats
    stats = parser.get_stats()
    print(f"\n{'='*80}")
    print(f"📊 PARSING STATISTICS")
    print(f"{'='*80}")
    print(f"Total chunks (initial):        {stats['total_chunks']}")
    print(f"Title chunks merged:           {stats['title_chunks_merged']}")
    print(f"Large chunks split:            {stats['large_chunks_split']}")
    print(f"Final nodes:                   {stats['final_nodes']}")
    print()

    # Show first N chunks
    print(f"{'='*80}")
    print(f"📄 FIRST {min(num_chunks, len(nodes))} CHUNKS")
    print(f"{'='*80}\n")

    for i, node in enumerate(nodes[:num_chunks], 1):
        token_count = node.metadata.get('token_count', 0)
        is_sub_chunked = node.metadata.get('is_sub_chunked', False)
        is_title = node.metadata.get('is_title', False)
        current_header = node.metadata.get('current_header', 'N/A')
        header_level = node.metadata.get('header_level', 0)
        header_path = node.metadata.get('header_path', [])

        # Node type indicator
        if is_title:
            node_type = "📋 TITLE (MERGED)"
        elif is_sub_chunked:
            node_type = "🔪 SUB-CHUNK"
        else:
            node_type = "📄 CHUNK"

        print(f"{'─'*80}")
        print(f"{node_type} #{i}")
        print(f"{'─'*80}")
        print(f"Current Header: {current_header}")
        print(f"Header Level: {header_level}")

        # Show hierarchy
        if header_path:
            full_path = header_path + ([current_header] if current_header else [])
            hierarchy_str = " > ".join(full_path)
            print(f"Hierarchy: {hierarchy_str}")
        else:
            print(f"Hierarchy: (none - top level)")

        print(f"Tokens: {token_count}")
        print(f"Sub-chunked: {is_sub_chunked}")
        print(f"\n{'▼'*40} FULL CONTENT {'▼'*40}")
        print(node.text)
        print(f"{'▲'*40} END CONTENT {'▲'*40}\n")

    if len(nodes) > num_chunks:
        print(f"\n... and {len(nodes) - num_chunks} more nodes (not shown)")

    return nodes, stats


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
        num_chunks = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    else:
        # Default: test với file khóa 2024
        test_file = "data/fixed/curriculum/chuong-trinh-dao-tao-ctdt-khoa-2024.md"
        num_chunks = 10

    if not Path(test_file).exists():
        print(f"[ERROR] File not found: {test_file}\n")
        print("Usage:")
        print("  python test/test_curriculum_chunking.py <file_path> [num_chunks]")
        print("\nExample:")
        print("  python test/test_curriculum_chunking.py data/fixed/curriculum/chuong-trinh-dao-tao-ctdt-khoa-2024.md 10")
    else:
        test_curriculum_chunks(test_file, num_chunks)
