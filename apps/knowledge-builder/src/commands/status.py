"""
Status command - Show pipeline status for documents.
"""

from pathlib import Path
from ..config.settings import settings
from ..pipeline import PipelineState


def run_status(args):
    """
    Show pipeline status for document(s).

    Args:
        args: CLI arguments with:
            - category: Category to show status for
            - file: Single document to show status for
            - verbose: Show detailed stage info
    """
    # Determine what to show
    if args.file:
        # Single document directory
        file_path = Path(args.file)

        # Try to resolve path in multiple ways
        resolved_path = None

        if file_path.exists() and file_path.is_dir():
            resolved_path = file_path
        elif args.category:
            # Try: STAGES_DIR/{category}/{file_path}
            candidate = settings.paths.STAGES_DIR / args.category / file_path.name
            if candidate.exists() and candidate.is_dir():
                resolved_path = candidate

        if not resolved_path:
            print(f"[ERROR] Document directory not found: {file_path}")
            if args.category:
                print(f"[HINT] Also tried: {settings.paths.STAGES_DIR / args.category / file_path.name}")
            else:
                print(f"[HINT] You can specify --category to help locate the document")
            return

        # Infer category and document_id from path
        document_id = resolved_path.name
        category = resolved_path.parent.name

        # Override category if explicitly provided
        if args.category:
            category = args.category
        
        _show_document_status(
            category=category,
            document_id=document_id,
            verbose=args.verbose
        )
    
    elif args.category:
        # Whole category
        category_dir = settings.paths.STAGES_DIR / args.category
        
        if not category_dir.exists():
            print(f"[ERROR] Category not found: {args.category}")
            return
        
        # Get all documents
        doc_dirs = [d for d in category_dir.iterdir() if d.is_dir()]
        
        if not doc_dirs:
            print(f"[INFO] No documents found in category: {args.category}")
            return
        
        print(f"\n{'='*70}")
        print(f"CATEGORY: {args.category} ({len(doc_dirs)} documents)")
        print(f"{'='*70}\n")
        
        for doc_dir in sorted(doc_dirs):
            document_id = doc_dir.name
            _show_document_status(
                category=args.category,
                document_id=document_id,
                verbose=args.verbose
            )
    
    else:
        # Show all categories
        stages_dir = settings.paths.STAGES_DIR
        
        if not stages_dir.exists():
            print(f"[INFO] No stages directory found")
            return
        
        categories = [d for d in stages_dir.iterdir() if d.is_dir()]
        
        if not categories:
            print(f"[INFO] No categories found")
            return
        
        for category_dir in sorted(categories):
            category = category_dir.name
            doc_dirs = [d for d in category_dir.iterdir() if d.is_dir()]
            
            print(f"\n{'='*70}")
            print(f"CATEGORY: {category} ({len(doc_dirs)} documents)")
            print(f"{'='*70}\n")
            
            for doc_dir in sorted(doc_dirs)[:5]:  # Show first 5
                document_id = doc_dir.name
                _show_document_status(
                    category=category,
                    document_id=document_id,
                    verbose=False
                )
            
            if len(doc_dirs) > 5:
                print(f"  ... and {len(doc_dirs) - 5} more documents")


def _show_document_status(
    category: str,
    document_id: str,
    verbose: bool = False
):
    """
    Show status for a single document.
    
    Args:
        category: Category name
        document_id: Document ID
        verbose: Show detailed stage info
    """
    # Load state
    state = PipelineState.load(category, document_id)
    
    if state is None or not state.stages:
        print(f"  {document_id}: No pipeline state")
        return
    
    if verbose:
        # Detailed view
        print(f"\n{'='*70}")
        print(f"DOCUMENT: {category}/{document_id}")
        print(f"{'='*70}")
        
        if state.migrated_from_legacy:
            print(f"[INFO] Migrated from legacy processed/ structure")
        
        print(f"\nStatus: {state.get_status_summary()}")
        
        # Show each stage
        print(f"\nStages:")
        for stage in state.stages:
            status_symbol = {
                'completed': '[x]',
                'failed': '[FAIL]',
                'skipped': '[SKIP]',
                'rejected': '[REJ]',
                'in_progress': '[...]',
                'pending': '[ ]'
            }.get(stage.status, '[?]')
            
            print(f"  {status_symbol} {stage.name:15} {stage.status:12} ", end='')
            
            if stage.cost > 0:
                print(f"(${stage.cost:.4f})", end='')
            
            if stage.manually_edited:
                print(f" [LOCKED]", end='')
            
            print()
            
            if stage.output_file:
                output_path = state.doc_dir / stage.output_file
                if output_path.exists():
                    size = output_path.stat().st_size / 1024  # KB
                    print(f"     -> {stage.output_file} ({size:.1f} KB)")
        
        # Show total cost
        total_cost = state.get_total_cost()
        if total_cost > 0:
            print(f"\nTotal cost: ${total_cost:.4f}")
        
        print()
    
    else:
        # Compact view
        status = state.get_status_summary()
        cost = state.get_total_cost()
        
        cost_str = f"${cost:.4f}" if cost > 0 else "-"
        locked = " [LOCKED]" if any(s.manually_edited for s in state.stages) else ""
        
        print(f"  {document_id:30} {cost_str:10} {locked}")
        print(f"    {status}")
