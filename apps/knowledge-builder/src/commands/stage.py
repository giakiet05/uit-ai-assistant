"""
Stage command - Run a specific stage for document(s).
"""

from pathlib import Path
from ..config.settings import settings
from ..pipeline import ProcessingPipeline, IndexingPipeline
from ..utils.file_finder import find_raw_file


PROCESSING_STAGES = ['parse', 'clean', 'normalize', 'filter', 'fix-markdown', 'metadata']
INDEXING_STAGES = ['chunk', 'embed-index']
ALL_STAGES = PROCESSING_STAGES + INDEXING_STAGES


def run_stage(args):
    """
    Run a specific stage for document(s).

    Args:
        args: CLI arguments with:
            - stage: Stage name to run
            - category: Category to process
            - file: Single file to process
            - force: Force rerun stage
    """
    stage_name = args.stage
    
    # Validate stage name
    if stage_name not in ALL_STAGES:
        print(f"[ERROR] Invalid stage: {stage_name}")
        print(f"[INFO] Available stages:")
        print(f"  Processing: {', '.join(PROCESSING_STAGES)}")
        print(f"  Indexing: {', '.join(INDEXING_STAGES)}")
        return
    
    # Determine what to process
    if args.file:
        # Single document directory
        file_path = Path(args.file)

        # Try to resolve path in multiple ways:
        # 1. As-is (absolute or relative from cwd)
        # 2. Relative from project root (../../data/stages/...)
        # 3. From STAGES_DIR if category is provided

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
        # Expected: stages/{category}/{document_id}/
        document_id = resolved_path.name
        category = resolved_path.parent.name

        # Override category if explicitly provided
        if args.category:
            category = args.category
        
        _run_stage_for_document(
            stage_name=stage_name,
            category=category,
            document_id=document_id,
            force=args.force
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
        
        print(f"[INFO] Running stage '{stage_name}' for {len(doc_dirs)} documents")
        
        success_count = 0
        failed_count = 0
        
        for doc_dir in doc_dirs:
            document_id = doc_dir.name
            
            try:
                _run_stage_for_document(
                    stage_name=stage_name,
                    category=args.category,
                    document_id=document_id,
                    force=args.force
                )
                success_count += 1
            except Exception as e:
                print(f"[ERROR] Failed for {document_id}: {e}")
                failed_count += 1
        
        print(f"\n[SUMMARY] {success_count} succeeded, {failed_count} failed")
    
    else:
        print("[ERROR] Must specify --category or --file")
        return


def _run_stage_for_document(
    stage_name: str,
    category: str,
    document_id: str,
    force: bool = False
):
    """
    Run a specific stage for a document.
    
    Args:
        stage_name: Stage to run
        category: Category name
        document_id: Document ID
        force: Force rerun stage
    """
    print(f"\n[INFO] Running stage '{stage_name}' for {category}/{document_id}")
    
    try:
        # Determine which pipeline
        if stage_name in PROCESSING_STAGES:
            # Find raw file (may be None for migrated documents)
            raw_file_path = find_raw_file(category, document_id)

            # Processing pipeline
            pipeline = ProcessingPipeline(
                category=category,
                document_id=document_id,
                raw_file_path=raw_file_path or Path("dummy")
            )
            
            result = pipeline.run_stage(
                stage_name=stage_name,
                force=force
            )
        
        else:
            # Indexing pipeline
            pipeline = IndexingPipeline(
                category=category,
                document_id=document_id
            )
            
            result = pipeline.run_stage(
                stage_name=stage_name,
                force=force
            )
        
        if result['executed']:
            print(f"[SUCCESS] Stage '{stage_name}' completed (cost: ${result['cost']:.4f})")
        else:
            print(f"[INFO] Stage '{stage_name}' skipped: {result.get('skip_reason', 'unknown')}")
    
    except Exception as e:
        print(f"[ERROR] Stage '{stage_name}' failed: {e}")
        raise
