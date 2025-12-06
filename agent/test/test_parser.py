"""
Test LlamaParse cho 1 folder duy nhất - kiểm tra parsing PDF/DOCX.
"""
from pathlib import Path
from src.knowledge_builder.processing.parser import ParserFactory
from src.shared.config.settings import settings


def test_parse_folder(folder_path: str):
    """Parse tất cả attachments trong 1 folder."""
    folder = Path(folder_path)

    if not folder.exists():
        print(f"[ERROR] Folder not found: {folder}")
        return

    # Tìm attachments (PDF, DOCX only - XLSX skipped, needs SQL DB)
    files = [
        f for f in folder.iterdir()
        if f.is_file()
        and f.suffix.lower() in ['.pdf', '.docx']
        and f.name != 'metadata_generator.json'
    ]

    print(f"\n{'='*70}")
    print(f"Testing folder: {folder.name}")
    print(f"{'='*70}")
    print(f"Found {len(files)} attachment(s)\n")

    if not files:
        print("[INFO] No attachments to parse (only content.md)")
        return

    for i, file_path in enumerate(files, 1):
        print(f"\n--- File {i}/{len(files)} ---")
        print(f"Name: {file_path.name}")
        print(f"Size: {file_path.stat().st_size / 1024:.1f} KB")
        print(f"Type: {file_path.suffix}")

        try:
            # Get parser
            parser = ParserFactory.get_parser(
                str(file_path),
                use_llamaparse=settings.processing.USE_LLAMAPARSE
            )

            print(f"Parser: {parser.__class__.__name__}")
            print("Parsing...", end=" ", flush=True)

            # Parse
            markdown = parser.parse(str(file_path))

            print(f"✅ Success!")
            print(f"Output length: {len(markdown)} chars ({len(markdown.split())} words)")

            # Save to root directory
            output_filename = f"parsed_{file_path.stem}.md"
            output_path = Path(output_filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            print(f"💾 Saved to: {output_filename}")

            # Preview
            lines = markdown.split('\n')
            print(f"Lines: {len(lines)}")
            print(f"\nPreview (first 400 chars):")
            print("-" * 70)
            print(markdown[:400])
            print("...")
            print("-" * 70)

        except Exception as e:
            print(f"❌ FAILED")
            print(f"Error: {e}")


def list_sample_folders():
    """List các folders có attachments để test."""
    print("\n📂 Sample folders with attachments:\n")

    raw_dir = Path("../data/raw/daa.uit.edu.vn")

    if not raw_dir.exists():
        print(f"[ERROR] Raw data directory not found: {raw_dir}")
        return

    count = 0
    for folder in sorted(raw_dir.iterdir()):
        if not folder.is_dir():
            continue

        # Check if has attachments (PDF, DOCX only)
        attachments = [
            f for f in folder.iterdir()
            if f.is_file() and f.suffix.lower() in ['.pdf', '.docx']
        ]

        if attachments:
            count += 1
            print(f"{count}. {folder.name}")
            print(f"   Attachments: {len(attachments)} files")
            for att in attachments[:3]:  # Show first 3
                print(f"   - {att.name}")
            if len(attachments) > 3:
                print(f"   ... and {len(attachments) - 3} more")
            print()

            if count >= 5:  # Only show first 5
                break

    if count == 0:
        print("No folders with attachments found")


if __name__ == "__main__":
    import sys

    # Thay đổi folder này để test, hoặc pass argument
    default_folder = "data/raw/daa.uit.edu.vn/bieu-mau-khoa-luan-tot-nghiep-danh-cho-sinh-vien"

    if len(sys.argv) > 1:
        test_folder = sys.argv[1]
    else:
        test_folder = default_folder

    if test_folder == "--list":
        # List sample folders
        list_sample_folders()
    elif not Path(test_folder).exists():
        print(f"[ERROR] Folder not found: {test_folder}\n")
        print("Usage:")
        print(f"  python test_parser.py <folder_path>")
        print(f"  python test_parser.py --list")
        print(f"\nOr edit the 'default_folder' variable in the script.")
    else:
        test_parse_folder(test_folder)
