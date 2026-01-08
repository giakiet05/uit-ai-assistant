"""
Pipeline command - Run processing and indexing pipelines.
"""

from pathlib import Path
from typing import Optional, List
from config.settings import settings
from pipeline import ProcessingPipeline, IndexingPipeline
from utils.file_finder import find_raw_file


def run_pipeline(args):
    """
    Run full pipeline (processing + indexing) or specific range.

    Args:
        args: CLI arguments with:
            - category: Category to process
            - file: Single file to process
            - from_stage: Starting stage (optional)
            - to_stage: Ending stage (optional)
            - force: Force rerun stages
            - skip_fix_markdown: Skip fix-markdown stage
            - processing_only: Only run processing pipeline
            - indexing_only: Only run indexing pipeline
    """
    # Determine what to process
    if args.file:
        # Single document directory
        file_path = Path(args.file)

        # Try to resolve path in multiple ways:
        # 1. As-is (absolute or relative from cwd)
        # 2. From STAGES_DIR if category is provided

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
            print(f"[INFO] Use format: data/stages/{{category}}/{{document_id}}/")
            return

        # Infer category and document_id from path
        # Expected: stages/{category}/{document_id}/
        document_id = resolved_path.name
        category = resolved_path.parent.name

        # Override category if explicitly provided
        if args.category:
            category = args.category
        
        _run_pipeline_for_document(
            category=category,
            document_id=document_id,
            from_stage=args.from_stage,
            to_stage=args.to_stage,
            force=args.force,
            skip_fix_markdown=args.skip_fix_markdown,
            processing_only=args.processing_only,
            indexing_only=args.indexing_only
        )
    
    elif args.category:
        # Whole category
        category_dir = settings.paths.STAGES_DIR / args.category
        
        if not category_dir.exists():
            print(f"[ERROR] Category not found: {args.category}")
            print(f"[INFO] Available categories: {[d.name for d in settings.paths.STAGES_DIR.iterdir() if d.is_dir()]}")
            return
        
        # Get all documents in category
        doc_dirs = [d for d in category_dir.iterdir() if d.is_dir()]
        
        if not doc_dirs:
            print(f"[INFO] No documents found in category: {args.category}")
            return
        
        print(f"[INFO] Found {len(doc_dirs)} documents in {args.category}")
        
        for doc_dir in doc_dirs:
            document_id = doc_dir.name
            print(f"\n{'='*70}")
            print(f"Processing: {args.category}/{document_id}")
            print(f"{'='*70}")
            
            _run_pipeline_for_document(
                category=args.category,
                document_id=document_id,
                from_stage=args.from_stage,
                to_stage=args.to_stage,
                force=args.force,
                skip_fix_markdown=args.skip_fix_markdown,
                processing_only=args.processing_only,
                indexing_only=args.indexing_only
            )
    
    else:
        print("[ERROR] Must specify --category or --file")
        return


def _run_pipeline_for_document(
    category: str,
    document_id: str,
    from_stage: Optional[str] = None,
    to_stage: Optional[str] = None,
    force: bool = False,
    skip_fix_markdown: bool = False,
    processing_only: bool = False,
    indexing_only: bool = False
):
    """
    Run pipeline for a single document.
    
    Args:
        category: Category name
        document_id: Document ID
        from_stage: Starting stage (optional)
        to_stage: Ending stage (optional)
        force: Force rerun stages
        skip_fix_markdown: Skip fix-markdown stage
        processing_only: Only run processing pipeline
        indexing_only: Only run indexing pipeline
    """
    try:
        # Run processing pipeline (unless indexing_only)
        if not indexing_only:
            print(f"\n[INFO] Running processing pipeline...")

            # Find raw file (may be None for migrated documents)
            raw_file_path = find_raw_file(category, document_id)
            if raw_file_path:
                print(f"[INFO] Found raw file: {raw_file_path.name}")
            else:
                print(f"[INFO] No raw file found (migrated document or manual creation)")

            proc_pipeline = ProcessingPipeline(
                category=category,
                document_id=document_id,
                raw_file_path=raw_file_path or Path("dummy")
            )
            
            if from_stage and to_stage:
                # Run specific range
                result = proc_pipeline.run_from_to(
                    from_stage=from_stage,
                    to_stage=to_stage,
                    force=force,
                    skip_fix_markdown=skip_fix_markdown
                )
            else:
                # Run full processing pipeline
                result = proc_pipeline.run(
                    force=force,
                    skip_fix_markdown=skip_fix_markdown
                )
            
            print(f"[SUCCESS] Processing pipeline: {len(result['stages_run'])} stages run, "
                  f"{len(result['stages_skipped'])} skipped, cost: ${result['total_cost']:.4f}")
            
            if result.get('rejected'):
                print(f"[INFO] Document rejected by filter stage, skipping indexing")
                return
        
        # Run indexing pipeline (unless processing_only)
        if not processing_only:
            print(f"\n[INFO] Running indexing pipeline...")
            
            idx_pipeline = IndexingPipeline(
                category=category,
                document_id=document_id
            )
            
            result = idx_pipeline.run(force=force)
            
            print(f"[SUCCESS] Indexing pipeline: {len(result['stages_run'])} stages run, "
                  f"{len(result['stages_skipped'])} skipped, cost: ${result['total_cost']:.4f}")
        
        print(f"\n[SUCCESS] Pipeline completed for {category}/{document_id}")
    
    except Exception as e:
        print(f"[ERROR] Pipeline failed for {category}/{document_id}: {e}")
        raise
