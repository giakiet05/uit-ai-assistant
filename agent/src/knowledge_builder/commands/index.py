"""Index command - Build vector store index from processed documents."""


def run_index(args):
    """Handle index command."""
    from ..indexing.indexer import DocumentIndexer

    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    # Create indexer and build collections
    indexer = DocumentIndexer()
    indexer.build_all_collections(categories=categories)
