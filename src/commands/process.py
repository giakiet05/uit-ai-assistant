"""Process command - Run processing pipeline v2."""


def run_process(args):
    """Handle process command."""
    from src.processing.pipeline_v2 import process_domain, process_all_domains

    categories = None
    if args.categories:
        categories = [c.strip() for c in args.categories.split(",")]

    if args.domain:
        process_domain(args.domain, categories)
    else:
        process_all_domains(categories)
