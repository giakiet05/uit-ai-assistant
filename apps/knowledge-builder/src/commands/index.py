"""Index command - Build vector store index from processed documents."""

from pathlib import Path


def run_index(args):
    """Handle index command."""
    from ..indexing.indexer import DocumentIndexer

    # Create indexer
    indexer = DocumentIndexer()

    # If --file is specified, index single file
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"[ERROR] File not found: {file_path}")
            return

        if not file_path.suffix == '.md':
            print(f"[ERROR] Only .md files are supported. Got: {file_path.suffix}")
            return

        print(f"[INFO] Indexing single file: {file_path}")
        indexer.index_single_file(file_path)

    # Otherwise, index by categories
    else:
        categories = None
        if args.categories:
            categories = [c.strip() for c in args.categories.split(",")]

        indexer.build_all_collections(categories=categories)
