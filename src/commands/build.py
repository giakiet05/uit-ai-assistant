"""Build command - Build vector store index."""


def run_build(args):
    """Handle build command."""
    from src.config.settings import settings
    from src.indexing.builder import build_domain, build_all_domains

    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    if args.domain:
        if args.domain not in settings.domains.START_URLS:
            print(f"[ERROR] Domain '{args.domain}' not configured")
            return
        build_domain(args.domain, categories)
    else:
        build_all_domains(categories)
