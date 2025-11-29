"""
Test chunking with a real regulation file (after Gemini fix).

This tests:
1. SmartNodeSplitter on real regulation file
2. Hierarchy tracking (CHƯƠNG > Điều > Khoản > Mục)
3. Metadata generation
4. Token counting
"""

import sys
from pathlib import Path
from llama_index.core import Document
from src.indexing.splitters.smart_node_splitter import SmartNodeSplitter
from src.config.settings import settings


def test_chunking(file_pattern: str = "547"):
    """
    Test chunking on a real file.

    Args:
        file_pattern: Pattern to match regulation file (default: "547")
    """
    # ========== FIND FILE ==========

    processed_dir = settings.paths.PROCESSED_DATA_DIR / "regulation"

    if not processed_dir.exists():
        print(f"❌ Directory not found: {processed_dir}")
        return

    matches = list(processed_dir.glob(f"*{file_pattern}*.md"))

    if not matches:
        print(f"❌ No markdown file found matching: {file_pattern}")
        print(f"   Searched in: {processed_dir}")
        return

    if len(matches) > 1:
        print(f"⚠️  Multiple files found:")
        for m in matches:
            print(f"   - {m.name}")
        print(f"\nUsing first match: {matches[0].name}\n")

    md_file = matches[0]
    print(f"📄 Testing chunking on: {md_file.name}\n")

    # ========== READ FILE ==========

    with open(md_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    print(f"📊 File stats:")
    print(f"   - Characters: {len(markdown_content):,}")
    print(f"   - Lines: {len(markdown_content.splitlines()):,}")
    print()

    # ========== CREATE DOCUMENT ==========

    # Try to load metadata_generator if exists
    metadata_file = md_file.with_suffix('.json')
    metadata = {
        "document_id": md_file.stem,
        "category": "regulation"
    }

    if metadata_file.exists():
        import json
        with open(metadata_file, 'r', encoding='utf-8') as f:
            loaded_metadata = json.load(f)
            metadata.update(loaded_metadata)
            print(f"✅ Loaded metadata_generator from: {metadata_file.name}")
            print(f"   - Title: {metadata.get('title', 'N/A')}")
            print(f"   - Effective date: {metadata.get('effective_date', 'N/A')}")
            print()

    doc = Document(text=markdown_content, metadata=metadata)

    # ========== CHUNK WITH SMART SPLITTER ==========

    print("="*80)
    print("🔧 CHUNKING WITH SMARTNODESPLITTER")
    print("="*80 + "\n")

    splitter = SmartNodeSplitter(
        max_tokens=7000,
        sub_chunk_size=1024,
        sub_chunk_overlap=200,
        enable_title_merging=True,
        enable_pattern_detection=True
    )

    nodes = splitter.get_nodes_from_documents([doc])

    # ========== PRINT STATS ==========

    print("\n" + "="*80)
    print("📊 CHUNKING STATS")
    print("="*80)

    print(f"\n✅ Total nodes: {len(nodes)}")
    print(f"\nSplitter stats:")
    for key, value in splitter.stats.items():
        print(f"   - {key}: {value}")

    # Calculate token distribution
    token_counts = [n.metadata.get('token_count', 0) for n in nodes]
    if token_counts:
        print(f"\nToken distribution:")
        print(f"   - Min: {min(token_counts)}")
        print(f"   - Max: {max(token_counts)}")
        print(f"   - Avg: {sum(token_counts) // len(token_counts)}")

    # ========== SHOW SAMPLE CHUNKS ==========

    print("\n" + "="*80)
    print("📋 SAMPLE CHUNKS (First 5)")
    print("="*80 + "\n")

    for i, node in enumerate(nodes[:5]):
        header_path = node.metadata.get('header_path', [])
        current_header = node.metadata.get('current_header', '')

        full_path = header_path.copy()
        if current_header:
            full_path.append(current_header)

        hierarchy = ' > '.join(full_path) if full_path else '(root)'

        print(f"📄 CHUNK #{i+1}")
        print("─"*80)
        print(f"Header: {current_header or '(none)'}")
        print(f"Hierarchy: {hierarchy}")
        print(f"Level: {node.metadata.get('header_level', 'N/A')}")
        print(f"Tokens: {node.metadata.get('token_count', 'N/A')}")
        print(f"Sub-chunked: {node.metadata.get('is_sub_chunked', False)}")

        # Show content preview (first 300 chars)
        content_preview = node.text[:300].replace('\n', ' ')
        print(f"\nContent preview:")
        print(f"{content_preview}...")
        print("\n" + "─"*80 + "\n")

    # ========== SHOW HIERARCHY EXAMPLES ==========

    print("="*80)
    print("🌳 HIERARCHY EXAMPLES (3-level nested chunks)")
    print("="*80 + "\n")

    nested_count = 0
    for i, node in enumerate(nodes):
        header_path = node.metadata.get('header_path', [])
        current_header = node.metadata.get('current_header', '')

        full_path = header_path.copy()
        if current_header:
            full_path.append(current_header)

        hierarchy = ' > '.join(full_path)

        # Show chunks with 3+ levels
        if hierarchy.count('>') >= 2:
            print(f"Chunk #{i+1}: {hierarchy}")
            nested_count += 1
            if nested_count >= 5:  # Show first 5 examples
                break

    if nested_count == 0:
        print("(No 3-level nested chunks found)")

    print("\n" + "="*80)
    print("✅ CHUNKING TEST COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "547"
    test_chunking(pattern)
