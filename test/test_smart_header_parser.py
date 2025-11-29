"""
Test SmartNodeSplitter và so sánh với SimpleNodeSplitter.

Focus: Regulation documents
Test cases:
1. Title merging (3 short chunks → 1)
2. Pattern detection (Điều X, CHƯƠNG X)
3. Clean output comparison
"""
from pathlib import Path
from llama_index.core import Document
from src.indexing.splitters import SmartNodeSplitter
from src.indexing.splitters import SimpleNodeSplitter
import json


def test_smart_parser(file_path: str, verbose: bool = True):
    """Test SmartNodeSplitter with detailed output."""
    print(f"\n{'='*80}")
    print(f"TESTING SMART HEADER PARSER")
    print(f"File: {Path(file_path).name}")
    print(f"{'='*80}\n")

    # Read file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Load metadata_generator
    metadata = {}
    auto_metadata_path = Path(file_path).with_suffix('.json')
    if auto_metadata_path.exists():
        with open(auto_metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        print(f"✅ Loaded metadata_generator: {auto_metadata_path.name}")
    else:
        metadata = {
            "document_id": Path(file_path).stem,
            "category": "regulation"  # Assume regulation for testing
        }
        print("⚠️  No metadata_generator file, using defaults")

    print(f"   Category: {metadata.get('category')}")
    print(f"   Title: {metadata.get('title', 'N/A')[:60]}...\n")

    # Create parser
    parser = SmartNodeSplitter(
        max_tokens=7000,
        sub_chunk_size=1024,
        sub_chunk_overlap=200,
        enable_title_merging=True,
        enable_pattern_detection=True
    )

    # Parse
    doc = Document(text=content, metadata=metadata)
    nodes = parser.get_nodes_from_documents([doc])

    # Show stats
    stats = parser.get_stats()
    print(f"\n{'='*80}")
    print(f"📊 PARSING STATISTICS")
    print(f"{'='*80}")
    print(f"Total chunks (initial):        {stats['total_chunks']}")
    print(f"Title chunks merged:           {stats['title_chunks_merged']}")
    print(f"Patterns detected:             {stats['patterns_detected']}")
    print(f"Large chunks split:            {stats['large_chunks_split']}")
    print(f"Final nodes:                   {stats['final_nodes']}")
    print()

    # Show nodes with FULL CONTENT
    if verbose:
        print(f"{'='*80}")
        print(f"📄 ALL NODES (showing first 10 with FULL content + hierarchy)")
        print(f"{'='*80}\n")

        for i, node in enumerate(nodes[:20], 1):
            token_count = node.metadata.get('token_count', 0)
            is_sub_chunked = node.metadata.get('is_sub_chunked', False)
            is_title = node.metadata.get('is_title', False)
            current_header = node.metadata.get('current_header')
            header_level = node.metadata.get('header_level', 0)
            header_path = node.metadata.get('header_path', [])  # NEW: hierarchy

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

            # NEW: Show hierarchy
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

        if len(nodes) > 10:
            print(f"\n... and {len(nodes) - 10} more nodes (not shown)")

    return nodes, stats


def compare_parsers(file_path: str):
    """
    So sánh SmartNodeSplitter vs SimpleNodeSplitter.

    Focus:
    - Title merging: SmartParser merges, SimpleParser doesn't
    - Pattern detection: SmartParser detects Điều/CHƯƠNG
    - Output quality: Which one is better?
    """
    print(f"\n{'='*80}")
    print(f"COMPARISON: SmartNodeSplitter vs SimpleNodeSplitter")
    print(f"File: {Path(file_path).name}")
    print(f"{'='*80}\n")

    # Read file
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Load metadata_generator
    metadata = {}
    auto_metadata_path = Path(file_path).with_suffix('.json')
    if auto_metadata_path.exists():
        with open(auto_metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    metadata = metadata or {
        "document_id": Path(file_path).stem,
        "category": "regulation"
    }

    doc = Document(text=content, metadata=metadata)

    # Test SmartNodeSplitter
    print("🔹 SMART HEADER PARSER")
    print("─" * 80)
    smart_parser = SmartNodeSplitter()
    smart_nodes = smart_parser.get_nodes_from_documents([doc])
    smart_stats = smart_parser.get_stats()

    print(f"Results:")
    print(f"  Total nodes: {len(smart_nodes)}")
    print(f"  Title chunks merged: {smart_stats['title_chunks_merged']}")
    print(f"  Patterns detected: {smart_stats['patterns_detected']}")
    print(f"  Avg tokens/node: {sum(n.metadata.get('token_count', 0) for n in smart_nodes) / len(smart_nodes):.0f}")

    # Show first 3 nodes
    print(f"\n  First 3 nodes:")
    for i, node in enumerate(smart_nodes[:3], 1):
        header = node.metadata.get('current_header', 'N/A')
        is_title = node.metadata.get('is_title', False)
        marker = " [TITLE]" if is_title else ""
        print(f"    {i}. {header[:60]}{marker}")

    # Test SimpleNodeSplitter
    print("\n\n🔹 SIMPLE HEADER PARSER (baseline)")
    print("─" * 80)
    simple_parser = SimpleNodeSplitter()
    simple_nodes = simple_parser.get_nodes_from_documents([doc])
    simple_stats = simple_parser.get_stats()

    print(f"Results:")
    print(f"  Total nodes: {len(simple_nodes)}")
    print(f"  Avg tokens/node: {sum(n.metadata.get('token_count', 0) for n in simple_nodes) / len(simple_nodes):.0f}")

    # Show first 3 nodes
    print(f"\n  First 3 nodes:")
    for i, node in enumerate(simple_nodes[:3], 1):
        header = node.metadata.get('current_header', 'N/A')
        print(f"    {i}. {header[:60]}")

    # Comparison
    print(f"\n\n{'='*80}")
    print(f"📊 COMPARISON SUMMARY")
    print(f"{'='*80}")

    print(f"\n✨ SmartNodeSplitter improvements:")
    if smart_stats['title_chunks_merged'] > 0:
        print(f"  ✅ Merged {smart_stats['title_chunks_merged']} title chunks → 1 coherent title")
    else:
        print(f"  ⚠️  No title chunks merged (maybe not needed for this file)")

    if smart_stats['patterns_detected'] > 0:
        print(f"  ✅ Detected {smart_stats['patterns_detected']} section patterns (Điều, CHƯƠNG)")
    else:
        print(f"  ⚠️  No patterns detected (file might have clear markdown headers)")

    node_diff = len(simple_nodes) - len(smart_nodes)
    if node_diff > 0:
        print(f"  ✅ Reduced nodes: {len(simple_nodes)} → {len(smart_nodes)} (-{node_diff} nodes)")
    else:
        print(f"  ℹ️  Same node count: {len(smart_nodes)} nodes")

    print(f"\n💡 Recommendation:")
    if smart_stats['title_chunks_merged'] > 0 or smart_stats['patterns_detected'] > 0:
        print(f"  → SmartNodeSplitter is better for this file!")
        print(f"    Reason: Title merging and/or pattern detection improved structure")
    else:
        print(f"  → Both parsers work similarly for this file")
        print(f"    Reason: File has clean markdown structure already")

    # Detailed comparison of first node
    print(f"\n\n{'='*80}")
    print(f"📋 DETAILED COMPARISON: First Node")
    print(f"{'='*80}\n")

    print("🔹 SmartNodeSplitter (first node):")
    print("─" * 80)
    print(f"Header: {smart_nodes[0].metadata.get('current_header')}")
    print(f"Is title: {smart_nodes[0].metadata.get('is_title', False)}")
    print(f"Tokens: {smart_nodes[0].metadata.get('token_count')}")
    print(f"\nContent preview (first 400 chars):")
    print(smart_nodes[0].text[:10000])
    print("...")

    print("\n\n🔹 SimpleNodeSplitter (first node):")
    print("─" * 80)
    print(f"Header: {simple_nodes[0].metadata.get('current_header')}")
    print(f"Tokens: {simple_nodes[0].metadata.get('token_count')}")
    print(f"\nContent preview (first 400 chars):")
    print(simple_nodes[0].text[:10000])
    print("...")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--compare":
            test_file = sys.argv[2] if len(sys.argv) > 2 else "data/processed/regulation/790-qd-dhcntt_28-9-22_quy_che_dao_tao.md"
            compare_parsers(test_file)
        else:
            test_file = sys.argv[1]
            verbose = "--verbose" in sys.argv or "-v" in sys.argv
            test_smart_parser(test_file, verbose=verbose)
    else:
        # Default: compare mode
        test_file = "data/processed/regulation/790-qd-dhcntt_28-9-22_quy_che_dao_tao.md"

        if not Path(test_file).exists():
            print(f"[ERROR] File not found: {test_file}\n")
            print("Usage:")
            print("  python test/test_smart_header_parser.py <file_path>")
            print("  python test/test_smart_header_parser.py <file_path> --verbose")
            print("  python test/test_smart_header_parser.py --compare <file_path>")
        else:
            print("Running in COMPARISON mode (use --verbose for full output)\n")
            compare_parsers(test_file)
