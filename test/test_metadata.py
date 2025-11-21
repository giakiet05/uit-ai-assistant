"""
Test script for metadata generators.
Tests the extraction of metadata from raw documents using the new metadata generator system.
"""

import json
from pathlib import Path
from typing import Dict, List

from src.processing.metadata.metadata_generator_factory import MetadataGeneratorFactory
from src.processing.metadata.metadata_models import (
    RegulationMetadata,
    CurriculumMetadata,
    DefaultMetadata,
)


def test_regulation_metadata():
    """Test metadata extraction for regulation documents."""
    print("\n" + "=" * 80)
    print("TESTING REGULATION METADATA GENERATOR")
    print("=" * 80)

    regulation_dir = Path("data/raw_test/regulation")
    generator = MetadataGeneratorFactory.get_generator("regulation")

    results = []

    for file_path in regulation_dir.iterdir():
        if file_path.is_file():
            print(f"\n{'─' * 80}")
            print(f"Processing: {file_path.name}")
            print(f"{'─' * 80}")

            # Read file content
            if file_path.suffix == ".pdf":
                # For PDF, we'll use a placeholder since we can't easily read PDF in test
                print("⚠️  Skipping PDF file in this test (requires LlamaParse)")
                continue
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

            # Generate metadata
            metadata = generator.generate(file_path, content)

            if metadata:
                print(f"✅ SUCCESS")
                print(f"   Title: {metadata.title}")
                print(f"   Year: {metadata.year}")
                print(f"   Document Type: {metadata.document_type}")
                print(f"   Effective Date: {metadata.effective_date}")
                print(f"   Base Regulation Code: {metadata.base_regulation_code}")
                print(f"   Summary: {metadata.summary[:100] if metadata.summary else 'N/A'}...")
                print(f"   Keywords: {metadata.keywords}")
                print(f"   Is Index Page: {metadata.is_index_page}")

                results.append({
                    "file": file_path.name,
                    "status": "success",
                    "metadata": metadata.model_dump(),
                })
            else:
                print(f"❌ FAILED")
                results.append({
                    "file": file_path.name,
                    "status": "failed",
                })

    return results


def test_curriculum_metadata():
    """Test metadata extraction for curriculum documents."""
    print("\n" + "=" * 80)
    print("TESTING CURRICULUM METADATA GENERATOR")
    print("=" * 80)

    curriculum_dir = Path("data/raw_test/curriculum")
    generator = MetadataGeneratorFactory.get_generator("curriculum")

    results = []

    for file_path in curriculum_dir.iterdir():
        if file_path.is_file():
            print(f"\n{'─' * 80}")
            print(f"Processing: {file_path.name}")
            print(f"{'─' * 80}")

            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Generate metadata
            metadata = generator.generate(file_path, content)

            if metadata:
                print(f"✅ SUCCESS")
                print(f"   Title: {metadata.title}")
                print(f"   Year: {metadata.year}")
                print(f"   Major: {metadata.major}")
                print(f"   Program Type: {metadata.program_type}")
                print(f"   Program Name: {metadata.program_name}")
                print(f"   Summary: {metadata.summary[:100] if metadata.summary else 'N/A'}...")
                print(f"   Keywords: {metadata.keywords}")
                print(f"   Is Index Page: {metadata.is_index_page}")

                results.append({
                    "file": file_path.name,
                    "status": "success",
                    "metadata": metadata.model_dump(),
                })
            else:
                print(f"❌ FAILED")
                results.append({
                    "file": file_path.name,
                    "status": "failed",
                })

    return results


def save_results(regulation_results: List[Dict], curriculum_results: List[Dict]):
    """Save test results to JSON file."""
    output_file = Path("test/metadata_test_results.json")

    results = {
        "regulation": regulation_results,
        "curriculum": curriculum_results,
        "summary": {
            "regulation": {
                "total": len(regulation_results),
                "success": sum(1 for r in regulation_results if r["status"] == "success"),
                "failed": sum(1 for r in regulation_results if r["status"] == "failed"),
            },
            "curriculum": {
                "total": len(curriculum_results),
                "success": sum(1 for r in curriculum_results if r["status"] == "success"),
                "failed": sum(1 for r in curriculum_results if r["status"] == "failed"),
            },
        },
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n📝 Test results saved to: {output_file}")
    return results


def print_summary(results: Dict):
    """Print test summary."""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for category in ["regulation", "curriculum"]:
        summary = results["summary"][category]
        print(f"\n{category.upper()}:")
        print(f"  Total: {summary['total']}")
        print(f"  ✅ Success: {summary['success']}")
        print(f"  ❌ Failed: {summary['failed']}")

        if summary["total"] > 0:
            success_rate = (summary["success"] / summary["total"]) * 100
            print(f"  Success Rate: {success_rate:.1f}%")


def main():
    """Main test function."""
    print("🚀 Starting metadata generator tests...\n")

    # Test regulation metadata
    regulation_results = test_regulation_metadata()

    # Test curriculum metadata
    curriculum_results = test_curriculum_metadata()

    # Save and display results
    results = save_results(regulation_results, curriculum_results)
    print_summary(results)

    print("\n✨ Testing complete!")


if __name__ == "__main__":
    main()
